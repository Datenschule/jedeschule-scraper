# -*- coding: utf-8 -*-
import re

import scrapy
from scrapy.shell import inspect_response



class SachsenAnhaltSpider(scrapy.Spider):
    name = "sachsen-anhalt"
    # allowed_domains = ["https://www.bildung-lsa.de/ajax.php?m=getSSResult&q=&lk=-1&sf=-1&so=-1&timestamp=1480082277128"]
    start_urls = ['https://www.bildung-lsa.de/ajax.php?m=getSSResult&q=&lk=-1&sf=-1&so=-1&timestamp=1480082277128/']

    detail_url = "https://www.bildung-lsa.de/ajax.php?m=getSSDetails&id={}&timestamp=1480082332787"

    def parse(self, response):
        # inspect_response(response, self)
        js_callbacks = response.css("span ::attr(onclick)").extract()
        pattern = "getSSResultItemDetail\((\d+)\)"
        ids = [re.match(pattern, text).group(1) for text in js_callbacks]
        for id in ids:
            yield scrapy.Request(self.detail_url.format(id), callback=self.parse_detail)


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
        yield content