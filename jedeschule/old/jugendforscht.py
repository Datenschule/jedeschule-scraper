import scrapy
from scrapy.shell import inspect_response

class SachsenSpider(scrapy.Spider):
    name = "jugendforscht"
    base_url = "http://jugend-forscht.bmbfcluster.de"
    list = "&V=list#mpl"

    start_urls = ['http://jugend-forscht.bmbfcluster.de/index.php?M=445&PID=19']

    def parse(self, response):
        #inspect_response(response, self)
        for li in response.css(".contextcontent li"):
            link = li.css('a::attr(href)').extract_first()
            request = scrapy.Request(self.base_url + link + self.list, callback=self.parse_state)
            yield request

    def parse_state(self, response):
        #inspect_response(response, self)
        for li in response.css('.geo_list li'):
            link = li.css('a::attr(href)').extract_first()
            request = scrapy.Request(self.base_url + link, callback=self.parse_locality)
            yield request

    def parse_locality(self, response):
        #inspect_response(response, self)
        for li in response.css('.geo_list li'):
            link = li.css('a::attr(href)').extract_first()
            request = scrapy.Request(self.base_url + link, callback=self.parse_school)
            yield request

    def parse_school(self, response):
        for li in response.css('.geo_list li'):
            link = li.css('a::attr(href)').extract_first()
            request = scrapy.Request(self.base_url + link, callback=self.parse_item)
            yield request

    def parse_item(self, response):
        #inspect_response(response, self)
        collection = {}
        h4 = response.css('.even h4')
        p = response.css('.even p')

        response.h4 = h4
        response.p = p

        #inspect_response(response, self)

        if (len(h4) > 0):
            collection['Schule'] = h4[0].css('::text').extract_first()
        if (len(p) > 0):
            collection['Ort'] = p[0].css('::text').extract_first()
        if (len(h4) > 1):
            collection['Wettbewerb'] = h4[1].css('::text').extract_first()
        if (len(p) > 1):
            collection['partner'] = p[1].css('::text').extract_first()
        return collection
