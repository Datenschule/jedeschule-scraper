# -*- coding: utf-8 -*-
import scrapy
from scrapy.shell import inspect_response


class BayernSpider(scrapy.Spider):
    name = "bayern"
    # allowed_domains = ["https://www.bllv.de/index.php?id=2707"]
    start_urls = ['https://www.bllv.de/index.php?id=2707']

    def parse(self, response):
        school_types = response.css("#center_col > form > p:nth-child(2) > input ::attr(value)").extract()
        print(school_types)
        for school_type in school_types:
            yield scrapy.FormRequest.from_response(
                response,
                callback=self.parse_list,
                formdata={"varSchulart[]": school_type},
            )

    def parse_list(self, response):
        school_numbers = response.css("table tr:nth-child(1) td:nth-child(2) ::text").extract()
        for school_number in school_numbers:
            yield scrapy.FormRequest.from_response(
                response,
                callback=self.parse_details,
                formdata={"varSchulnummer": school_number},
            )

    def parse_details(self, response):
        collection = {}
        for tr in response.css("table tr"):
            tds = tr.css("td ::text").extract()
            # sometimes there is no value for the key
            if len(tds) == 2:
                collection[tds[0][:-1]] = tds[1]
        yield collection
