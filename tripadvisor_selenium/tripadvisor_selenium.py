from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import csv
import datetime
import re
import random


#Open 3 files -- listing info, review info, user info
list_file = open('listings.csv', 'w')
list_writer = csv.writer(list_file, delimiter="|")

review_file = open('reviews.csv', 'w')
review_writer = csv.writer(review_file, delimiter="|")

user_file = open('users.csv', 'w')
user_writer = csv.writer(user_file, delimiter="|")




#Load web driver
driver = webdriver.Chrome()
driver.get("https://www.tripadvisor.com/Attractions-g60763-Activities-New_York_City_New_York.html")




###DEFINE FUNCTION TO GET LISTING INFORMATION
def scrape_listing(driver, listing, n_review_pages):
	driver.get(listing)

	#get the listing id
	list_id = listing.split('Review')[1].replace('-','')

	#there are two versions of the page... try the first, if it doesn't work then do the other 
	try:
		list_name = driver.find_element_by_xpath('//h1[@class="heading_title"]').text
		header = driver.find_element_by_xpath('//div[@class="rating_and_popularity"]')
		try: #listings with few ratings don't get an overall rating or rating count
			list_rating = header.find_element_by_xpath('.//div[@class="rs rating"]/div/span[1]').get_attribute('alt')
			list_review_n = header.find_element_by_xpath('.//span[@property="count"]').text
		except:
			list_rating, list_review_n = None, None
		list_type = header.find_elements_by_xpath('//span[@class="header_detail attraction_details"]/div/a')
		list_type = [a.text for a in list_type]
		list_type = ";".join(list_type)
		


	#there are two versions of the page... trying the 2nd version! 
	except:
		list_name = driver.find_element_by_xpath('//h1[@class="ui_header h1"]').text
		header = driver.find_element_by_xpath('//div[@class="headerInfoWrapper"]')
		try: #listings with few ratings don't get an overall rating or rating count
			list_rating = header.find_element_by_xpath('.//a[@href="#REVIEWS"]/div/span[1]').get_attribute('alt')
			list_review_n = header.find_element_by_xpath('.//span[@class="reviewCount"]').text
		except:
			list_rating, list_review_n = None, None
		list_type = header.find_elements_by_xpath('//span[@class="header_detail attraction_details"]/div/a')
		list_type = [a.text for a in list_type]
		list_type = ";".join(list_type)



	#a couple things are the same on both page formats -- getting those here
	#review histogram
	histogram_rows = driver.find_elements_by_xpath('//ul[@class="ratings_chart"]/li')
	list_rating_hist = []
	for row in histogram_rows:
		pct_reviews = row.find_element_by_xpath('./span[3]').text
		list_rating_hist += [pct_reviews]
	list_rating_hist = ";".join(list_rating_hist)

	#location
	list_loc = driver.find_elements_by_xpath('//div[@class="detail_section address"]/span[not(@class="ui_icon map-pin")]')
	list_loc = [a.text for a in list_loc]
	list_loc = ";".join(list_loc)



	#write out the listing details
	list_dict = {}
	list_dict['list_id'] = list_id
	list_dict['list_name'] = list_name
	list_dict['list_rating'] = list_rating
	list_dict['list_rating_hist'] = list_rating_hist
	list_dict['list_review_n'] = list_review_n
	list_dict['list_loc'] = list_loc
	list_dict['time_accessed'] = str(datetime.datetime.now())
	list_writer.writerow(list_dict.values())



	#loop over the review pages and get reviews

	#define a wait for the next page
	next_page_wait = WebDriverWait(driver, 10)

	for i in range(0, n_review_pages):
		#get reviews
		print('starting page {n}'.format(n=i+1))
		get_reviews(driver, list_id)
		print('finished page {n}'.format(n=i+1), '\n', '#'*40)


		#move on to the next page?
		#identify first review ID (we can use this later to make sure we've moved to the next page)
		first_review = driver.find_element_by_xpath('//div[@class="reviewSelector"]')


		#try to click to the next page
		try:
			#find and click on the next review page button
			print('about to look for the next review page button')
			next_reviews_button = driver.find_element_by_xpath('//a[@class="nav next taLnk ui_button primary"]')
			print('found the next page button')
			next_reviews_button.click()
			print('clicked to review page {n}'.format(n=i+2))

			#wait until the next page loads
			next_page_wait.until(EC.staleness_of(first_review))
			print('next page loaded')
			

		#if the click fails, it's probably because we reached the last review page. break the loop.
		except Exception as e:
			print(e)
			print('reached the last review page!')
			break

		





###DEFINE FUNCTION TO GET REVIEWS FROM ONE PAGE OF REVIEWS
def get_reviews(driver, list_id):
	print('scraping review page')



	#close the pop-up ad, if it exists. it blocks the user overlay
	try:
		close_button = driver.find_element_by_xpath(
			'//div[@class="slide_up_messaging_container large"]/span[@class="close ui_icon times"]')
		print('ugh... I hate ads.found close button')
		close_button.click()
		print('I think I clicked it!')
	except Exception as e:
		print('thank god, tripadvisor didn\'t try to show me an ad')
		pass



	#both page formats have the same review identifier
	reviews = driver.find_elements_by_xpath('//div[@class="reviewSelector"]')

	print('I found {n} reviews!'.format(n=len(reviews)))

	#try page format 1
	try:
		for review in reviews:

			review_rating = review.find_element_by_xpath('.//div[@class="rating reviewItemInline"]/span').get_attribute('class')
			print('started scraping review')
			review_title = review.find_element_by_xpath('.//div[contains(@class, "quote")]/a/span').text
			review_date = review.find_element_by_xpath('.//span[@class="ratingDate relativeDate"]').get_attribute('title')
			review_text = review.find_element_by_xpath('.//p[@class="partial_entry"]').text

			#checks if the mobile symbol is there; if not, returns false
			try:
				review_is_mobile = review.find_element_by_xpath('.//span[@class="viaMobile"]') != None
			except:
				review_is_mobile = False


			review_dict = {}
			review_dict['list_id'] = list_id
			review_dict['review_title'] = review_title
			review_dict['review_date'] = review_date
			review_dict['review_rating'] = review_rating
			review_dict['review_text'] = review_text
			review_dict['review_is_mobile'] = review_is_mobile
			review_dict['time_accessed'] = str(datetime.datetime.now())
			

			print('scraping user')
			user_dict = extract_user_info(driver, review)
			user_writer.writerow(user_dict.values())
			print('user scraped')


			review_dict['reviewer_username'] = user_dict['username']
			review_writer.writerow(review_dict.values())


			print('review scraped', '\n', '$'*10)




	#try page format 2
	except:
		for review in reviews:

			review_rating = review.find_element_by_xpath('.//div[@class="ui_column is-9"]/span').get_attribute('class')
			print('started scraping review')
			review_title = review.find_element_by_xpath('.//div[contains(@class, "quote")]/a/span').text
			review_date = review.find_element_by_xpath('.//span[@class="ratingDate"]').get_attribute('title')
			review_text = review.find_element_by_xpath('.//p[@class="partial_entry"]').text

			#checks if the mobile symbol is there; if not, returns false
			try:
				review_is_mobile = review.find_element_by_xpath('.//span[@class="viaMobile"]') != None
			except:
				review_is_mobile = False

			review_dict = {}
			review_dict['list_id'] = list_id
			review_dict['review_title'] = review_title
			review_dict['review_date'] = review_date
			review_dict['review_rating'] = review_rating
			review_dict['review_text'] = review_text
			review_dict['review_is_mobile'] = review_is_mobile
			review_dict['time_accessed'] = str(datetime.datetime.now())
			

			print('scraping user')
			user_dict = extract_user_info(driver, review)
			user_writer.writerow(user_dict.values())
			print('user scraped')


			review_dict['reviewer_username'] = user_dict['username']
			review_writer.writerow(review_dict.values())


			print('review scraped', '\n', '$'*10)







###DEFINE FUNCTION TO EXTRACT INFO FROM THE USER PROFILES
def extract_user_info(driver, review):

	user_dict = {}

	#find the user profile and set up the click action;
	try:
		reviewer_prof = review.find_element_by_xpath('.//div[contains(@class,"memberOverlayLink")]')
		Click = ActionChains(driver).click(reviewer_prof)

	#if that fails, it's probably because the user has no account (probably deleted?)
	except:
		user_dict['username'] = 'no account'
		return user_dict
	

	#click on the profile and wait until it loads
	profile_wait = WebDriverWait(driver, 3)
	try:
		Click.perform()
		profile = profile_wait.until(EC.presence_of_element_located((By.XPATH,
								'//div[@class="memberOverlayRedesign g10n"]')))
	except:
		user_dict['username'] = None
		return user_dict


	#extract user info
	#username
	reviewer_link = driver.find_element_by_xpath('//div[@class="memberOverlayRedesign g10n"]/a').get_attribute('href')
	reviewer_username = re.sub('.*members/', '', reviewer_link)

	#demos
	reviewer_demos = driver.find_elements_by_xpath('//ul[@class="memberdescriptionReviewEnhancements"]/*')
	reviewer_demos = [element.text for element in reviewer_demos]
	reviewer_demos = ";".join(reviewer_demos)
	
	#reviewer rating histogram
	histogram_rows = driver.find_elements_by_xpath('//div[@class="chartRowReviewEnhancements"]')
	review_hist = []
	for row in histogram_rows:
		n_reviews = row.find_element_by_xpath('./span[3]').text
		review_hist += [n_reviews]
	review_hist = ";".join(review_hist)

	#reviewer helpful votes
	try:
		helpvotes = driver.find_element_by_xpath(
			'//div[@class="memberOverlayRedesign g10n"]//*[contains(text(), "Helpful votes")]').text
	except:
		helpvotes = None

	#reviewer cities visited
	try:
		n_cities_visited = driver.find_element_by_xpath(
			'//div[@class="memberOverlayRedesign g10n"]//*[contains(text(), "Cities visited")]').text
	except:
		n_cities_visited = None

	#reviewer tags
	tags = driver.find_elements_by_xpath('//a[@class="memberTagReviewEnhancements"]')
	tags = [tag.text for tag in tags]
	tags = ";".join(tags)


	#build dict item
	user_dict['username'] = reviewer_username
	user_dict['demos'] = reviewer_demos
	user_dict['review_hist'] = review_hist
	user_dict['helpvotes'] = helpvotes
	user_dict['n_cities_visited'] = n_cities_visited
	user_dict['tags'] = tags
	user_dict['time_accessed'] = str(datetime.datetime.now())


	#close the user profile -- make sure it's closed before moving on
	close_profile_button = driver.find_element_by_xpath('//span[@class="ui_overlay ui_popover arrow_left "]/div[@class="ui_close_x"]')
	close_profile_button.click()
	profile_wait.until_not(EC.presence_of_element_located((By.XPATH, '//span[@class="ui_overlay ui_popover arrow_left "]')))

	return user_dict







###FIND THE LISTINGS=

#loop through the pages of listings and collect all of the links
listings = []
for i in range(0,2):
	try:
		print('started listings page {n}'.format(n=i+1))
		page_listings = driver.find_elements_by_xpath('//div[@class="listing_title "]/a')

		if page_listings == []:
			page_listings = driver.find_elements_by_xpath('//a[@class="title ui_header h2"]')

		page_listings = [listing.get_attribute('href') for listing in page_listings]
		listings += page_listings

		try:
			next_button = driver.find_element_by_xpath('//a[@class="nav next rndBtn ui_button primary taLnk"]')
			next_button.click()
			print('+'*50)
		except Exception as e:
			print(e, 'Error trying to go to the next page')


	except Exception as e:
		print(e, 'Error... uh not sure yet')
		break

#remove links that are actually subcategories, not specific listings, based on the URL string
listings = list(filter(lambda l: l.find('Activities') == -1, listings))
#[listing for listing in listings if listing.find('Activities') == -1]

#get top 10
top_10 = listings[0:10]

#get a random 10 outside of the top 10
rest = listings[10:]
random.seed(100)
random.shuffle(rest)
sample = rest[0:10]

#combine top 10 with sample
target_listings = top_10 + sample
print(target_listings)

#scrape scrape scrape
for listing in target_listings:
	scrape_listing(driver, listing, 100)



list_file.close()
review_file.close()
user_file.close()

