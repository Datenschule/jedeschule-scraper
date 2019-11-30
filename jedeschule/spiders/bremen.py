# -*- coding: utf-8 -*-
import scrapy
from scrapy import Item
from scrapy.exceptions import DropItem
from scrapy.shell import inspect_response

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class BremenSpider(SchoolSpider):
    name = "bremen"
    start_urls = ['http://www.bildung.bremen.de/detail.php?template=35_schulsuche_stufe2_d']

    def parse(self, response):
        for link in response.css(".table_erklaerung a"):
            detail_url = link.css("::attr(href)").get()
            school_id = link.css("em ::text").get()

            yield scrapy.Request(response.urljoin(detail_url), callback=self.parse_detail, meta={'id': school_id})

    def parse_detail(self, response):
        lis = response.css(".kogis_main_visitenkarte ul li")

        item = {}

        item['id'] = response.meta['id']
        item['data_url'] = response.url

        if len(lis) == 0:
            # Detail page contains no info, see https://github.com/Datenschule/jedeschule-scraper/issues/54
            raise DropItem(item)

        item['name'] = response.css(".main_article h3 ::text").extract_first()
        for li in lis:
            key = li.css("span ::attr(title)").extract_first()
            value = " ".join([part.strip() for part in li.css("::text").extract()])
            # Filter out this pointless entry
            if key is not None:
                item[key] = value

        yield item

    @staticmethod
    def normalize(item: Item) -> School:
        ansprechpersonen = item['Ansprechperson'].replace('Schulleitung:', '').replace('Vertretung:', ',').split(',')
        item['Schulleitung'] = ansprechpersonen[0]
        item['Vertretung'] = ansprechpersonen[1]

        return School(  id=item.get('id'),
                        name=item.get('name'),
                        address=item.get('Anschrift:'),
                        website=item.get('Internet'),
                        email=item.get('E-Mail-Adresse'),
                        fax=item.get('Telefax'),
                        phone=item.get('Telefon'),
                        director=item.get('Schulleitung'))
