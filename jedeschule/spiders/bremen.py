# -*- coding: utf-8 -*-
import scrapy
from scrapy import Item
from scrapy.shell import inspect_response

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class BremenSpider(SchoolSpider):
    name = "bremen"
    start_urls = ['http://www.bildung.bremen.de/detail.php?template=35_schulsuche_stufe2_d']

    def parse(self, response):
        for link in response.css(".table_daten_container a ::attr(href)").extract():
            yield scrapy.Request(response.urljoin(link), callback=self.parse_detail)

    def parse_detail(self, response):
        lis = response.css(".kogis_main_visitenkarte ul li")

        collection = {}
        collection['name'] = response.css(".main_article h3 ::text").extract_first()
        for li in lis:
            key = li.css("span ::attr(title)").extract_first()
            value = " ".join([part.strip() for part in li.css("::text").extract()])
            # Filter out this pointless entry
            if key is not None:
                collection[key] = value
            collection['data_url'] = response.url
        yield collection

    @staticmethod
    def normalize(item: Item) -> School:
        ansprechpersonen = item['Ansprechperson'].replace('Schulleitung:', '').replace('Vertretung:', ',').split(',')
        item['Schulleitung'] = ansprechpersonen[0]
        item['Vertretung'] = ansprechpersonen[1]
        return School(name=item.get('name'),
                        address=item.get('Anschrift:'),
                        website=item.get('Internet'),
                        email=item.get('E-Mail-Adresse'),
                        fax=item.get('Telefax'),
                        phone=item.get('Telefon'))
