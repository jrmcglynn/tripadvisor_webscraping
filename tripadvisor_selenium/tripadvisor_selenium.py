from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import csv
import datetime
import re


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
def scrape_listing(driver, listing):
	driver.get(listing)

	#get the listing id
	list_id = listing.split('Review')[1].replace('-','')

	#there are two versions of the page... try the first, if it doesn't work then do the other 
	try:
		list_name = driver.find_element_by_xpath('//h1[@class="heading_title"]').text
		header = driver.find_element_by_xpath('//div[@class="rating_and_popularity"]')
		list_rating = header.find_element_by_xpath('.//div[@class="rs rating"]/div/span[1]').get_attribute('alt')
		list_review_n = header.find_element_by_xpath('.//span[@property="count"]').text

		#there are different address types for different types of listings. this covers a few, otherwise gets None
		try:
			list_loc = driver.find_element_by_xpath('//span[@class="extended-address"]').text
		except:
			try:
				list_loc = driver.find_element_by_xpath('//span[@class="street-address"]').text
			except:
				try:
					list_loc = driver.find_element_by_xpath('//div[@class="detail_section neighborhood"]').text
				except:
					list_loc = None

	#there are two versions of the page... trying the 2nd version! 
	except:
		list_name = driver.find_element_by_xpath('//h1[@class="ui_header h1"]').text
		header = driver.find_element_by_xpath('//div[@class="headerInfoWrapper"]')
		list_rating = header.find_element_by_xpath('.//a[@href="#REVIEWS"]/div/span[1]').get_attribute('alt')
		list_review_n = header.find_element_by_xpath('.//span[@class="reviewCount"]').text

		#there are different address types for different types of listings. this covers a few, otherwise gets None
		try:
			list_loc = driver.find_element_by_xpath('//span[@class="extended-address"]').text
		except:
			try:
				list_loc = driver.find_element_by_xpath('//span[@class="street-address"]').text
			except:
				try:
					list_loc = driver.find_element_by_xpath('//div[@class="detail_section neighborhood"]').text
				except:
					list_loc = None

	#write out the listing details
	list_dict = {}
	list_dict['list_id'] = list_id
	list_dict['list_rating'] = list_rating
	list_dict['list_review_n'] = list_review_n
	list_dict['list_loc'] = list_loc
	list_dict['time_accessed'] = str(datetime.datetime.now())
	list_writer.writerow(list_dict.values())

	#close the pop-up ad, if it exists. it blocks the user overlay
	try:
		close_button = driver.find_element_by_xpath(
			'//div[@class="slide_up_messaging_container large"]/span[@class="close ui_icon times"]')
		print('found close button')
		close_button.click()
	except:
		pass


	get_reviews(driver, list_id)

	for _ in range(0,5):
		next_reviews_button = driver.find_element_by_xpath('//a[@class="nav next taLnk ui_button primary"]')
		next_reviews_button.click()

		get_reviews(driver, list_id)



###DEFINE FUNCTION TO GET REVIEWS FROM LISTINGS PAGE
def get_reviews(driver, list_id):
	#both page formats have the same review identifier
	reviews = driver.find_elements_by_xpath('//div[@class="reviewSelector"]')

	#try page format 1
	try:
		for review in reviews:
			review_stars = review.find_element_by_xpath('.//div[@class="rating reviewItemInline"]/span').get_attribute('class')
			review_title = review.find_element_by_xpath('.//div[@class="quote isNew"]/a/span').text
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
			review_dict['review_stars'] = review_stars
			review_dict['review_text'] = review_text
			review_dict['review_is_mobile'] = review_is_mobile
			review_dict['time_accessed'] = str(datetime.datetime.now())
			

			user_dict = extract_user_info(driver, review)
			user_writer.writerow(user_dict.values())

			review_dict['reviewer_username'] = user_dict['username']
			review_writer.writerow(review_dict.values())



	#try page format 2
	except:
		for review in reviews:
			review_stars = review.find_element_by_xpath('.//div[@class="ui_column is-9"]/span').get_attribute('class')
			review_title = review.find_element_by_xpath('.//div[@class="quote isNew"]/a/span').text
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
			review_dict['review_stars'] = review_stars
			review_dict['review_text'] = review_text
			review_dict['review_is_mobile'] = review_is_mobile
			review_dict['time_accessed'] = str(datetime.datetime.now())
			

			user_dict = extract_user_info(driver, review)
			user_writer.writerow(user_dict.values())

			review_dict['reviewer_username'] = user_dict['username']
			review_writer.writerow(review_dict.values())







###DEFINE FUNCTION TO EXTRACT INFO FROM THE USER PROFILES
def extract_user_info(driver, review):

	#find the user profile and set up the click action
	reviewer_prof = review.find_element_by_xpath('.//div[contains(@class,"memberOverlayLink")]')
	Click = ActionChains(driver).click(reviewer_prof)

	#click on the profile and wait until it loads; try again if it fails
	profile_wait = WebDriverWait(driver, 3)
	try:
		Click.perform()
		profile = profile_wait.until(EC.presence_of_element_located((By.XPATH,
								'//div[@class="memberOverlayRedesign g10n"]')))
	except:
		return None


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
	user_dict = {}
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
	profile_wait.until_not(EC.presence_of_element_located((By.XPATH,
								'//div[@class="memberOverlayRedesign g10n"]')))

	return user_dict







###FIND THE LISTINGS
#initialize listings as an empty list
listings = []

#loop through the pages of listings and collect all of the links
#while True:
for _ in range(0,2):
	try:
		print('started listings page {n}'.format(n=_+1))
		listings = driver.find_elements_by_xpath('//div[@class="listing_title "]/a')

		if listings == []:
			listings = driver.find_elements_by_xpath('//a[@class="title ui_header h2"]')

		listings = [listing.get_attribute('href') for listing in listings]

		#remove links that are actually subcategories, not specific listings
		listings = [listing for listing in listings if listing.find('Activities') == -1]

		for listing in listings:
			scrape_listing(driver, listing)

		next_button = driver.find_element_by_xpath('//a[@class="nav next rndBtn ui_button primary taLnk"]')
		next_button.click()
		print('+'*50)

	except:
		break













	# ###GET REVIEWS
	# #both page formats have the same review identifier
	# reviews = driver.find_elements_by_xpath('//div[@class="reviewSelector"]')

	# #try page format 1
	# try:
	# 	for review in reviews:
	# 		review_stars = review.find_element_by_xpath('.//div[@class="rating reviewItemInline"]/span').get_attribute('class')
	# 		review_title = review.find_element_by_xpath('.//div[@class="quote isNew"]/a/span').text
	# 		review_date = review.find_element_by_xpath('.//span[@class="ratingDate relativeDate"]').get_attribute('title')
	# 		review_text = review.find_element_by_xpath('.//p[@class="partial_entry"]').text
	# 		#checks if the mobile symbol is there; if not, returns false
	# 		try:
	# 			review_is_mobile = review.find_element_by_xpath('.//span[@class="viaMobile"]') != None
	# 		except:
	# 			review_is_mobile = False

	# 		review_dict = {}
	# 		review_dict['list_id'] = list_id
	# 		review_dict['review_title'] = review_title
	# 		review_dict['review_date'] = review_date
	# 		review_dict['review_stars'] = review_stars
	# 		review_dict['review_text'] = review_text
	# 		review_dict['review_is_mobile'] = review_is_mobile
	# 		review_dict['time_accessed'] = str(datetime.datetime.now())
			

	# 		user_dict = extract_user_info(driver, review)
	# 		user_writer.writerow(user_dict.values())

	# 		review_dict['reviewer_username'] = user_dict['username']
	# 		review_writer.writerow(review_dict.values())



	# #try page format 2
	# except:
	# 	for review in reviews:
	# 		review_stars = review.find_element_by_xpath('.//div[@class="ui_column is-9"]/span').get_attribute('class')
	# 		review_title = review.find_element_by_xpath('.//div[@class="quote isNew"]/a/span').text
	# 		review_date = review.find_element_by_xpath('.//span[@class="ratingDate"]').get_attribute('title')
	# 		review_text = review.find_element_by_xpath('.//p[@class="partial_entry"]').text
	# 		#checks if the mobile symbol is there; if not, returns false
	# 		try:
	# 			review_is_mobile = review.find_element_by_xpath('.//span[@class="viaMobile"]') != None
	# 		except:
	# 			review_is_mobile = False

	# 		review_dict = {}
	# 		review_dict['list_id'] = list_id
	# 		review_dict['review_title'] = review_title
	# 		review_dict['review_date'] = review_date
	# 		review_dict['review_stars'] = review_stars
	# 		review_dict['review_text'] = review_text
	# 		review_dict['review_is_mobile'] = review_is_mobile
	# 		review_dict['time_accessed'] = str(datetime.datetime.now())
			

	# 		user_dict = extract_user_info(driver, review)
	# 		user_writer.writerow(user_dict.values())

	# 		review_dict['reviewer_username'] = user_dict['username']
	# 		review_writer.writerow(review_dict.values())























list_file.close()
review_file.close()
user_file.close()

