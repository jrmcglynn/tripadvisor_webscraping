from scrapy import Spider, Request
from tripadvisor.items import TaReviewItem
import re

class TripAdvisorS(Spider):
	name = 'ta_spider'
	allowed_urls = ['https://www.tripadvisor.com/']



	#get the number of listings pages and construct the list of pages
	start_urls = ['https://www.tripadvisor.com/Attractions-g60763-Activities-oa{i}-New_York_City_New_York.html#FILTERED_LIST'.\
	format(i=index) for index in range(30,31,30)]



	#get the links to the individual listing pages
	def parse(self, response):
		listings = response.xpath('//div[@class="listing_title "]')
		print('found {x} listings'.format(x=len(listings)), '0'*50)
		for listing in listings[0:2]:
			link = listing.xpath('./a/@href').extract_first()

			#remove the listings that are actually subcategories; yield the rest of the URLs
			if re.search('^/Attractions-g60763-', link) != None:
				pass
			else:
				url = 'https://www.tripadvisor.com' + link
				yield Request(url=url, callback=self.parse_list_page)



	#parse the primary listing page to construct a list of review pages
	def parse_list_page(self, response):

		#get the number of review pages
		pages = response.xpath('//div[@id="REVIEWS"]//a[@class="pageNum last taLnk "]/text()').extract_first()
		pages = int(pages)
		print('found {x} review pages'.format(x=pages), '1'*50)
		pages = 4
		
		#break down the listing url in preparation for re-constructing with review index
		root_url = response.url
		root_url_split = root_url.split('-Reviews-')

		#parse the original review page
		self.parse_review_page(response)

		#parse additional review pages by reconstructing url with index
		p=1
		while p < pages:
			print('crawling page ', p)
			url = root_url_split[0] + '-Reviews-or{p}-'.format(p=p*10) + root_url_split[1]
			yield Request(url=url, callback=self.parse_review_page)
			p += 1



	#parse the individual review pages
	def parse_review_page(self, response):

		#extract listing attributes
		list_name = response.xpath('//h1[@id="HEADING"]/text()').extract_first()
		list_type = response.xpath('//span[@class="is-hidden-mobile header_detail attractionCategories"]/div/a/text()').extract()
		list_loc = response.xpath('//div[@class="detail_section neighborhood"]/span/text()').extract_first()

		print(list_name, list_type, list_loc)

		#identify each review
		reviews = response.xpath('//div[@class="reviewSelector"]')

		print('found {x} reviews'.format(x=len(reviews)), '2'*50)


		#parse each review and yield item
		for review in reviews:
			review_date = review.xpath('.//span[@class="ratingDate"]/@title').extract_first()
			review_stars = review.xpath('.//div[@class="ui_column is-9"]/span[1]/@class').extract_first()
			review_title = review.xpath('.//span[@class="noQuotes"]/text()').extract_first()
			review_text = review.xpath('.//p[@class="partial_entry"]/text()').extract_first()
			reviewer_username = review.xpath('.//div[@class="member_info"]//div[@class="info_text"]/div/text()').extract_first()
			reviewer_location = review.xpath('.//div[@class="member_info"]//div[@class="userLoc"]/strong/text()').extract()

			item = TaReviewItem()
			item['list_name'] = list_name
			item['list_type'] = list_type
			item['list_loc'] = list_loc
			item['review_date'] = review_date
			item['review_stars'] = review_stars
			item['review_title'] = review_title
			item['review_text'] = review_text
			item['reviewer_username'] = reviewer_username
			item['reviewer_location'] = reviewer_location

			yield item

		print("="*50)

