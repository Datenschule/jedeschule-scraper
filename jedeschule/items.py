# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class School(scrapy.Item):
    name = scrapy.Field()
    id = scrapy.Field()
    address = scrapy.Field()
    address2 = scrapy.Field()
    zip = scrapy.Field()
    city = scrapy.Field()
    website = scrapy.Field()
    email = scrapy.Field()
    school_type = scrapy.Field()
    legal_status = scrapy.Field()
    provider = scrapy.Field()
    fax = scrapy.Field()
    phone = scrapy.Field()
    latitude = scrapy.Field()
    longitude = scrapy.Field()

    director = scrapy.Field()
