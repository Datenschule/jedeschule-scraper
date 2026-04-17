from dataclasses import dataclass

from scrapy import Item

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


@dataclass
class SchoolPipelineItem:
    info: School
    item: Item


class SchoolPipeline(object):
    def process_item(self, item, spider: SchoolSpider) -> SchoolPipelineItem:
        school = spider.normalize(item)
        sk = spider.state_key
        if not isinstance(sk, str) or not sk.strip():
            raise ValueError(
                f"Spider {spider.name!r} must set a non-empty string state_key "
                f"(ISO 3166-2:DE code without DE- prefix)"
            )
        school["state_key"] = sk.strip()
        return SchoolPipelineItem(info=school, item=item)
