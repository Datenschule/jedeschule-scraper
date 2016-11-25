# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy.shell import inspect_response


class SaarlandSpider(scrapy.Spider):
    name = "saarland"
    # allowed_domains = ["www.saarland.de/4526.htm"]
    start_urls = ['http://www.saarland.de/4526.htm']

    def parse(self, response):
        for link in response.css(".relatedinfo a ::attr(href)").extract():
            yield scrapy.Request(response.urljoin(link), callback=self.parse_list)

    def parse_list(self, response):
        for link in response.css(".contentteaserlist_frame a ::attr(href)").extract():
            yield scrapy.Request(response.urljoin(link), callback=self.parse_list)

        schools = response.css(".boxpadding10")
        for school in schools:
            # inspect_response(response, self)
            data = {}
            text_content = school.css("::text").extract()

            data['name'] = school.css("h2 ::text").extract_first()

            for index, line in enumerate(text_content):
                if re.match("^\d+ \w+", line):
                    data['zip'] = line.strip()
                    data['street'] = text_content[index-1].strip()

            data['email'] = school.css(".link_email a ::attr(href)").extract_first()
            data['website'] = school.css(".link_external a ::attr(href)").extract_first()

            director_match = school.re("Schulleiter(?:[ /]? in )?: (. *)")
            data['director'] = director_match[0] if director_match else None

            phone_match = school.re("Tel(?:[\.:]+)? ([\(\) 0-9]+)")
            data['telephone'] = phone_match[0] if phone_match else None

            fax_match = school.re("Fax(?:[\.:]+)? ([\(\) 0-9]+)")
            data['fax'] = fax_match[0] if fax_match else None

            yield data