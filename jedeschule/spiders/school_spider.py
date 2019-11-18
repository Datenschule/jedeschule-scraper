from abc import ABC

import scrapy
from scrapy import Item

from jedeschule.items import School


class SchoolSpider(scrapy.Spider, ABC):
    @staticmethod
    def normalize(item: Item) -> School:
        pass
