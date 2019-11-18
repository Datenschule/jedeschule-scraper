# -*- coding: utf-8 -*-
import re

import scrapy
from scrapy import Item
from scrapy.shell import inspect_response

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class SachsenAnhaltSpider(SchoolSpider):
    name = "sachsen-anhalt"
    start_urls = ['https://www.bildung-lsa.de/ajax.php?m=getSSResult&q=&lk=-1&sf=-1&so=-1&timestamp=1480082277128/']

    detail_url = "https://www.bildung-lsa.de/ajax.php?m=getSSDetails&id={}&timestamp=1480082332787"

    def parse(self, response):
        js_callbacks = response.css("span ::attr(onclick)").extract()
        pattern = "getSSResultItemDetail\((\d+)\)"
        ids = [re.match(pattern, text).group(1) for text in js_callbacks]
        names = response.css("b::text").extract()
        for id, name in zip(ids, names):
            request = scrapy.Request(self.detail_url.format(id), callback=self.parse_detail)
            request.meta['name'] = name.strip()
            yield request

    def parse_detail(self, response):
        tables = response.css("table")

        content = {}
        # Only the second and third table contain interesting data
        for table in tables[1:3]:
            trs = table.css("tr")
            for tr in trs:
                tds = tr.css("td")
                key = tds[0].css("::text").extract_first()[:-2]
                value = " ".join(tds[1].css("::text").extract())

                content[key] = value
        content['Name'] = response.meta['name']
        # The name is included in the "Adresse" field so we remove that
        # in order to get only the address
        content['Adresse'] = content['Adresse'].replace(response.meta['name'], "").strip()
        yield content

    @staticmethod
    def normalize(item: Item) -> School:
        return School(name=item.get('Name'),
                      address=item.get('Addresse'),
                      website=item.get('Homepage'),
                      email=item.get('E-Mail'),
                      fax=item.get('Fax'),
                      phone=item.get('Telefon'),
                      )
