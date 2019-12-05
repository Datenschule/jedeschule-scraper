# -*- coding: utf-8 -*-
import scrapy

from jedeschule.items import School


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
            request.meta['uuid'] = uuid
            yield request

    def parse_list(self, response):
        school = response.css("body")
        data = {'id': f'SL-{response.meta["uuid"]}',
                'name': response.meta["name"],
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

    @staticmethod
    def normalize(item):
        zip, city = item['Stadt/Gemeinde'].split(', ')
        phone = item.get('Telefon').split('\n')[0] if item.get('Telefon') else None
        return School(id=item['id'],
                      name=item.get('name'),
                      phone=phone,
                      director=item.get('Schulleiter/in'),
                      website=item.get('Homepage'),
                      fax=item.get('Telefax'),
                      email=item.get('E-Mail'),  # email,
                      address=item.get('Straße'),
                      zip=zip,
                      city=city)
