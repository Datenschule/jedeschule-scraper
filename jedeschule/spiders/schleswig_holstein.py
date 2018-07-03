# -*- coding: utf-8 -*-
import scrapy
from scrapy.shell import inspect_response


class SchleswigHolsteinSpider(scrapy.Spider):
    name = "schleswig-holstein"
    base_url = 'https://www.secure-lernnetz.de/schuldatenbank/'
    start_urls = [base_url]

    def parse(self, response):
        inspect_response(response, self)
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
        # inspect_response(response, self)
        rows = response.css('table tbody tr')
        for row in rows:
            url = self.base_url + row.css('a::attr(href)').extract()[0]
            yield scrapy.Request(url, callback=self.parse_school)

    def parse_school(self, response):
        # inspect_response(response, self)
        item = {}
        item['name'] = response.css('table thead th::text').extract_first().strip()
        for row in response.css('table tbody tr'):
            key = row.css('td.bezeichner::text').extract_first().strip()
            value = row.css('td.dbwert label::text').extract_first().strip()
            item[key] = value
        yield item
