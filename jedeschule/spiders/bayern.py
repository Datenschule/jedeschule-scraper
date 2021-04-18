# -*- coding: utf-8 -*-
from urllib import parse

import scrapy
from scrapy import Item
from scrapy.shell import inspect_response

from jedeschule.items import School
from jedeschule.utils import get_first_or_none, cleanjoin


class BayernSpider(scrapy.Spider):
    name = "bayern"
    # allowed_domains = ["https://www.km.bayern.de/schueler/schulsuche.html"]
    start_urls = ['https://www.km.bayern.de/schueler/schulsuche.html?s=&t=9999&r=9999&o=9999&u=0&m=3&seite=1']

    def parse(self, response):
        number_of_pages = response.css("div.schulsuche > div > p.Right a:last-child::text").extract_first()
        # number_of_pages = 2
        for i in range(1, int(number_of_pages) + 1):
            url = "https://www.km.bayern.de/schueler/schulsuche.html?s=&t=9999&r=9999&o=9999&u=0&m=3&seite={page}"
            yield scrapy.Request(url.format(page=i),
                                 callback=self.parse_list)

    def parse_list(self, response):
        links = response.css('.ListSchools a::attr(href)').extract()
        for link in links:
            yield scrapy.Request(response.urljoin(link), callback=self.parse_detail)

    def get_lat_lon(self, response):
        try:
            geoportal_href = response.css("article > a::attr(href)").extract_first()
            querystring = parse.parse_qs(geoportal_href)
            return querystring['N'][0], querystring['E'][0]
        except:
            return None, None

    def parse_detail(self, response):
        # inspect_response(response, self)
        collection = {}
        text = response.css("article ::text")
        street, city = response.css("article > p")[0].css("::text").extract()
        collection['street'] = street
        collection['city'] = city
        collection['name'] = cleanjoin(response.css('article h1::text').extract(), "")
        collection['phone'] = get_first_or_none(text.re("Telefon: ([0-9 /]+)"))
        collection['fax'] = get_first_or_none(text.re("Fax: ([0-9 /]+)"))
        collection['web'] = response.css("article a::attr(href)").extract_first()
        collection['number'] = get_first_or_none(text.re("Schulnummer: ([0-9]+)"))
        collection['school_type'] = get_first_or_none(text.re("Schulart: (.+)"))
        collection['type'] = get_first_or_none(text.re("Rechtlicher Status: (.+)"))
        collection['teachers'] = get_first_or_none(text.re("Hauptamtliche Lehrkräfte: ([0-9]+)"))
        collection['students'] = get_first_or_none(text.re("Schüler: ([0-9]+)"))
        collection['url'] = response.url
        collection['latitude'], collection['longitude'] = self.get_lat_lon(response)
        yield collection

    @staticmethod
    def normalize(item: Item) -> School:
        zip_code, *city_parts = item.get('city').split()
        return School(name=item.get('name'),
                      phone=item.get('phone'),
                      fax=item.get('fax'),
                      website=item.get('web'),
                      address=item.get('street'),
                      city=' '.join(city_parts),
                      zip=zip_code,
                      school_type=item.get('school_type'),
                      legal_status=item.get('type'),
                      id='BY-{}'.format(item.get('number')),
                      latitude=item.get('latitude'),
                      longitude=item.get('longitude')
                      )
