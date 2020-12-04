# from dataclasses import dataclass

# from scrapy import Item

# from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


# @dataclass
# class SchoolPipelineItem:
#     info: School
#     item: Item


# class SchoolPipeline(object):
#     def process_item(self, item, spider: SchoolSpider) -> SchoolPipelineItem:
#         school = spider.normalize(item)
#         return SchoolPipelineItem(info=school, item=item)

class SchoolPipeline(object):
    def process_item(self, item, spider: SchoolSpider):
        school = spider.normalize(item)
        return {'info': school, 'item': item}
