from dataclasses import dataclass

from scrapy import Item

from jedeschule.items import School


@dataclass
class SchoolPipelineItem:
    info: School
    item: Item


class SchoolPipeline:
    def __init__(self, crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_item(self, item) -> SchoolPipelineItem:
        school = self.crawler.spider.normalize(item)
        return SchoolPipelineItem(info=school, item=item)
