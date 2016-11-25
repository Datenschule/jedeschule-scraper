# -*- coding: utf-8 -*-
import scrapy
from scrapy.shell import inspect_response


class SchleswigHolsteinSpider(scrapy.Spider):
    name = "schleswig-holstein"
    start_urls = ['http://schulportraets.schleswig-holstein.de/portal/schule_suchen/']

    def parse(self, response):
        yield scrapy.FormRequest.from_response(
                response,
                callback=self.after_login
                )

    def after_login(self, response):
        links = response.css("table tbody td b a::attr(href)").extract()
        for link in links:
            # turns /20/ into /20-1/ which is the details page that contains the data
            detail_link = link[:-1] + "-1/"
            yield scrapy.Request(response.urljoin(detail_link), callback=self.parse_detail)
        yield scrapy.FormRequest.from_response(
                response,
                formcss=".userInput",
                callback=self.other_pages
                )

    def other_pages(self, response):
        print("------>", response.request.body)
        links = response.css("table tbody td b a::attr(href)").extract()
        for link in links:
            # turns /1/ into /1-1/ which is the details page that contains the data
            detail_link = link[:-1] + "-1/"
            yield scrapy.Request(response.urljoin(detail_link), callback=self.parse_detail)

        if response.css("#content > div > form:nth-child(6)"):
            yield scrapy.FormRequest.from_response(
                    response,
                    formcss="#content > div > form:nth-child(6)",
                    callback=self.other_pages
                    )

    def parse_detail(self, response):
        collection = {}
        for row in response.css('tbody tr'):
            tds = row.css('td')

            # last character is ":". Strip that
            row_key = tds[0].css('::text').extract_first().strip()
            row_value = tds[1].css('::text').extract_first().strip()
            collection[row_key] = row_value

        request = scrapy.Request(response.urljoin("../8-1/"),
                                 callback=self.parse_students)
        request.meta['data'] = collection
        yield request

    def parse_students(self, response):
        collection = response.meta['data']
        table = response.css("table")
        if table:
            collection['students'] = []
            headers = table.css("th ::text").extract()
            for tr in table.css("tbody tr"):
                tds = tr.css("td ::text").extract()
                row = {}
                for index, td in enumerate(tds):
                    row[headers[index]] = tds[index].strip()
                collection['students'].append(row)

        request = scrapy.Request(response.urljoin("../5-3/"),
                                 callback=self.parse_partners)
        request.meta['data'] = collection
        yield request

    def parse_partners(self, response):
        collection = response.meta['data']
        text = " ".join([text.strip() for text in response.css(".teaserBlock p ::text").extract()])
        collection['partners_text'] = text

        yield collection
