# -*- coding: utf-8 -*-
import scrapy
from scrapy import Item
from scrapy.shell import inspect_response

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class SchleswigHolsteinSpider(SchoolSpider):
    name = "schleswig-holstein"
    base_url = 'https://www.secure-lernnetz.de/schuldatenbank/'
    start_urls = [base_url]

    def parse(self, response):
        url = self.base_url + response.css('form::attr(action)').extract_first()
        pages = response.css('#searchResultIndexTop li')
        for page in pages:
            formdata = self.parse_formdata(response)
            key = page.css('input::attr(name)').extract_first()
            formdata[key] = page.css('input::attr(value)').extract_first()
            if formdata[key] == ">":
                yield scrapy.FormRequest(url=url, formdata=formdata, callback=self.parse)
            if formdata[key].isdigit():
                yield scrapy.FormRequest(url=url, formdata=formdata, callback=self.parse_overview_table)

    def parse_formdata(self, response):
        formdata = {}
        for form in response.css('#myContent > input'):
            key = form.css('::attr(name)').extract_first()
            formdata[key] = form.css('::attr(value)').extract_first()

        formdata['filter[name1]'] = ''
        formdata['filter[dnr]'] = ''
        formdata['filter[schulart]'] = ''
        formdata['filter[kreis]'] = ''
        formdata['filter[ort]'] = ''
        formdata['filter[strasse]'] = ''

        return formdata

    def parse_overview_table(self, response):
        rows = response.css('table tbody tr')
        # use the second href element as it is only available for schools which are not "aufgeloest"
        for row in rows:
            if len(row.css('a::attr(href)').extract()) > 1:
                url = self.base_url + row.css('a::attr(href)').extract()[1]
                yield scrapy.Request(url, callback=self.parse_school)

    def parse_school(self, response):
        item = {}
        item['name'] = response.css('table thead th::text').extract_first().strip()
        for row in response.css('table tbody tr'):
            key = row.css('td.bezeichner::text').extract_first().strip()
            value = row.css('td.dbwert label::text').extract_first().strip()
            item[key] = value

        item['data_url'] = response.url
        yield item

    @staticmethod
    def normalize(item: Item) -> School:
        return School(name=item.get('name'),
                      id='SH-{}'.format(item.get('Dienststellennummer')),
                      address=item.get('Strasse'),
                      zip=item.get("Postleitzahl"),
                      city=item.get("Ort"),
                      email=item.get('E-Mail'),
                      school_type=item.get('Schularten'),
                      fax=item.get('Fax'),
                      phone=item.get('Telefon'),
                      director=item.get('Schulleitung'))

