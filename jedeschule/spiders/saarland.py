# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy.shell import inspect_response


class SaarlandSpider(scrapy.Spider):
    name = "saarland"
    # allowed_domains = ["www.saarland.de/4526.htm"]
    start_urls = ['https://www.saarland.de/schuldatenbank.htm?typ=alle&ort=']

    def parse(self, response):
        for school in response.css(".accordion h3"):
            uuid = school.css("::attr(data-id)").extract_first()
            name = school.css("::text").extract_first()
            details_url = f"https://www.saarland.de/schuldetails.htm?id={uuid}"
            request = scrapy.Request(details_url, callback=self.parse_list)
            request.meta['name'] = name.strip() if name else ""
            yield request

    def parse_list(self, response):
        school = response.css("body")
        data = {'name': response.meta["name"],
                'data-url': response.url}

        # All of the entries except for Homepage follow
        # the pattern `key:value`. For `Homepage` this is
        # `key:
        #  value`
        # This is why we have some extra code to keep track of this
        homepage_next = False
        for line in school.css("::text").extract():
            parts = line.split(': ')
            key = parts[0].strip()
            if len(parts) == 2:
                value = parts[1].strip()
                data[key] = value
            if homepage_next:
                data["Homepage"] = key
                homepage_next = False
            if key == "Homepage":
                homepage_next = True

        yield data