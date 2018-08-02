from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import csv


#Open 3 files -- listing info, review info, user info
list_file = open('listings.csv', 'w')
list_writer = csv.writer(list_file, delimiter="|")

review_file = open('reviews.csv', 'w')
review_writer = csv.writer(review_file, delimiter="|")

user_file = open('users.csv', 'w')
user_writer = csv.writer(user_file)



#Load web driver
driver = webdriver.Chrome()
driver.get("https://www.tripadvisor.com/Attractions-g60763-Activities-New_York_City_New_York.html")





###FIND THE LISTINGS
#initialize listings as an empty list
listings = []

#loop through the pages of listings and collect all of the links
#while True:
for _ in range(0,2):
	try:
		page_listings = driver.find_elements_by_xpath('//div[@class="listing_title "]/a')

		if page_listings != []:
			print('v1 worked')
		else:
			print('trying v2')
			page_listings = driver.find_elements_by_xpath('//a[@class="title ui_header h2"]')
			print('v2 worked')

		print('found {x} listings'.format(x=len(page_listings)))


		page_listings = [listing.get_attribute('href') for listing in page_listings]
		listings += page_listings

		next_button = driver.find_element_by_xpath('//a[@class="nav next rndBtn ui_button primary taLnk"]')
		next_button.click()

	except:
		break

#remove links that are actually subcategories, not specific listings
listings = [listing for listing in listings if listing.find('Activities') == -1]





###GET LISTING INFORMATION
for listing in listings[0:2]:
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
	list_writer.writerow(list_dict.values())

	#close the pop-up ad, if it exists. it blocks the user overlay
	try:
		close_button = driver.find_element_by_xpath(
			'//div[@class="slide_up_messaging_container large"]/span[@class="close ui_icon times"]')
		print('found close button')
		close_button.click()
	except:
		pass






	###GET REVIEWS
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
			review_writer.writerow(review_dict.values())
			



			#find the user profile and set up the click action
			reviewer_prof = review.find_element_by_xpath('.//div[@class="memberOverlayLink"]')
			Click = ActionChains(driver).click(reviewer_prof)
			

			#click on the profile and wait until it loads; try again if it fails
			profile_wait = WebDriverWait(driver, 3)
			try:
				Click.perform()
				profile = profile_wait.until(EC.presence_of_element_located((By.XPATH,
										'//div[@class="memberOverlayRedesign g10n"]')))
			except:
				try:
					Click.perform()
					profile = profile_wait.until(EC.presence_of_element_located((By.XPATH,
										'//div[@class="memberOverlayRedesign g10n"]')))
				except:
					raise
					#continue

			#extract user info
			reviewer_username = driver.find_element_by_xpath('//div[@class="memberOverlayRedesign g10n"]/a').get_attribute('href')
			print(reviewer_username)

			#move mouse elsewhere to close the user profile
			#random_space = review.find_element_by_xpath('.//span[@class="ratingDate relativeDate"]')
			ActionChains(driver).move_by_offset(-15, 0)



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
			review_writer.writerow(review_dict.values())
			



			#find the user profile and set up the click action
			reviewer_prof = review.find_element_by_xpath('.//div[@class="memberOverlayLink clickable"]')
			Click = ActionChains(driver).click(reviewer_prof)

			#click on the profile and wait until it loads; try again if it fails
			profile_wait = WebDriverWait(driver, 3)
			try:
				Click.perform()
				profile = profile_wait.until(EC.presence_of_element_located((By.XPATH,
									'//div[@class="memberOverlayRedesign g10n"]')))
			except:
				try:
					Click.perform()
					profile = profile_wait.until(EC.presence_of_element_located((By.XPATH,
										'//div[@class="memberOverlayRedesign g10n"]')))	
				except:
					raise
					#continue

			#extract user info
			reviewer_username = driver.find_element_by_xpath('//div[@class="memberOverlayRedesign g10n"]/a').get_attribute('href')
			print(reviewer_username)

			#click elsewhere to close the user profile
			#random_space = review.find_element_by_xpath('.//span[@class="ratingDate relativeDate"]')
			ActionChains(driver).move_by_offset(-15, 0)




















list_file.close()
review_file.close()
user_file.close()

