# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class TaReviewItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    list_name = scrapy.Field()
    list_type = scrapy.Field() #<-- I think I would need Selenium to get this
    list_loc = scrapy.Field()
    review_date = scrapy.Field()
    review_stars = scrapy.Field()
    review_title = scrapy.Field()
    review_text = scrapy.Field()
    reviewer_username = scrapy.Field()
    reviewer_location = scrapy.Field()
