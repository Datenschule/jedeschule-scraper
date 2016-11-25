import scrapy
from scrapy.shell import inspect_response

class SachsenSpider(scrapy.Spider):
    name = "sachsen"

    start_urls = ['https://schuldatenbank.sachsen.de/index.php?id=2']

    def parse(self, response):
        #inspect_response(response, self)
        yield scrapy.FormRequest.from_response(
            response, formcss="#content form", callback=self.parse_schoolist)

    def parse_schoolist(self, response):
        forms = len(response.css('.ssdb_02 form'))
        for formnumber in range(forms):
            yield scrapy.FormRequest.from_response(
                response, formnumber=formnumber + 3, callback=self.parse_school)

    def parse_school(self, response):
        collection = {}
        #inspect_response(response, self)
        collection['title'] = response.css("#content h2::text").extract_first().strip()
        entries = response.css(".kontaktliste li")
        for entry in entries:
            key = entry.css("b::text").extract_first().strip()
            values = entry.css("::text").extract()[1:]
            #inspect_response(response, self)
            collection[key] = ' '.join(values).replace('zur Karte', '')
        yield collection