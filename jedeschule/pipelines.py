# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.exceptions import DropItem
from jedeschule.items import School

class SchoolPipeline(object):
    def process_item(self, item, spider):
        if spider.name == 'saarland':
            address = "{} {}".format(item.get('street', ""), item.get('zip',""))
            if item.get('email'):
                email = item['email'].replace('mailto:', '').replace('%40', '@')
            else:
                email = None
            school = School(name=item.get('name'),
                            phone=item.get('telephone'),
                            director=item.get('telephone'),
                            website=item.get('website'),
                            fax=item.get('fax'),
                            email=email,
                            address=address)
        elif spider.name == 'niedersachsen':
            address = "{} {}".format(item.get('Straße', ""), item.get('Ort',""))
            school = School(name=item.get('Schule'),
                            phone=item.get('Tel'),
                            email=item.get('E-Mail'),
                            website=item.get('Homepage'),
                            address=address,
                            id='NDS-{}'.format(item.get('Schulnummer')))
        else:
            return item
            raise DropItem("Missing name in %s" % item)
        return school
