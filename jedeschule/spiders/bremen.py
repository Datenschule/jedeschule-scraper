# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy import Item

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class BremenSpider(SchoolSpider):
    name = "bremen"
    start_urls = ['http://www.bildung.bremen.de/detail.php?template=35_schulsuche_stufe2_d']

    def parse(self, response):
        for link in response.css(".table_daten_container a ::attr(href)").extract():
            request = scrapy.Request(response.urljoin(link), callback=self.parse_detail)
            request.meta['id'] = link.split("de&Sid=", 1)[1]
            yield request

    def parse_detail(self, response):
        lis = response.css(".kogis_main_visitenkarte ul li")

        if len(lis) == 0:
            # Detail page contains no info, see https://github.com/Datenschule/jedeschule-scraper/issues/54
            return

        collection = {}
        collection['id'] = response.meta['id'].zfill(3)
        collection['name'] = response.css(".main_article h3 ::text").extract_first()
        for li in lis:
            key = li.css("span ::attr(title)").extract_first()
            value = " ".join([part.strip() for part in li.css("::text").extract()])
            # Filter out this pointless entry
            if key is not None:
                collection[key] = value
            collection['data_url'] = response.url
        if collection['name']:
            yield collection

    def fix_number(number):
        new = ''
        for letter in number:
            if letter.isdigit():
                new += letter
        return new

    @staticmethod
    def normalize(item: Item) -> School:
        if 'Ansprechperson' in item:
            ansprechpersonen = item['Ansprechperson'].replace('Schulleitung:', '').replace('Vertretung:', ',').split(
                ',')
            director = ansprechpersonen[0].replace('\n', '').strip()
        else:
            director = None
        return School(name=item.get('name').strip(),
                      id='HB-{}'.format(item.get('id')),
                      address=re.split('\d{5}', item.get('Anschrift:').strip())[0].strip(),
                      zip=re.findall('\d{5}', item.get('Anschrift:').strip())[0],
                      city=re.split('\d{5}', item.get('Anschrift:').strip())[1].strip(),
                      website=item.get('Internet'),
                      email=item.get('E-Mail-Adresse').strip(),
                      fax=BremenSpider.fix_number(item.get('Telefax')),
                      phone=BremenSpider.fix_number(item.get('Telefon')),
                      director=director
                      )
