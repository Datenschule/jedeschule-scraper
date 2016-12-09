# -*- coding: utf-8 -*-
import scrapy
from scrapy.shell import inspect_response


class BerlinSpider(scrapy.Spider):
    name = "berlin"
    # allowed_domains = ["www.berlin.de/sen/bildung/schule/berliner-schulen/schulverzeichnis/SchulListe.aspx"]
    start_urls = ['http://www.berlin.de/sen/bildung/schule/berliner-schulen/schulverzeichnis/SchulListe.aspx/']

    def parse(self, response):
        yield scrapy.FormRequest.from_response(response,
                                               callback=self.parse_detail,
                                               formcss="#frmSchulListe",
                                               formdata={"__EVENTARGUMENT": "Page$4",
                                                         "__EVENTTARGET": "GridViewSchulen"}
                                               )

    def parse_detail(self, response):
        inspect_response(response, self)