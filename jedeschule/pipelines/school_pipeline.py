from jedeschule.spiders.school_spider import SchoolSpider


class SchoolPipeline(object):
    def process_item(self, item, spider: SchoolSpider):
        school = spider.normalize(item)
        return {'info': school, 'item': item}
