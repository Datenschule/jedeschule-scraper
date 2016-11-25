
import scrapy

def cleanjoin(listlike):
    """ returns string of joined items in list,
        removing whitespace """
    return "".join([text.strip() for text in listlike])

class NiedersachsenSpider(scrapy.Spider):
    name = 'niedersachsen'
    start_urls = ['http://schulnetz.nibis.de/db/schulen/suche_2.php']

    def parse(self, response):
        for link in response.css('tr.fliess td:nth-child(4) a ::attr(href)').extract():
            yield scrapy.Request(response.urljoin(link), callback=self.parse_detail)

        for link in response.css('tr.fliessbgg td:nth-child(4) a ::attr(href)').extract():
            yield scrapy.Request(response.urljoin(link), callback=self.parse_detail)

    def parse_detail(self, response):
        collection = {}
        for index, row in enumerate(response.css('tr')):
            # skip disclaimer header
            if index == 0:
                continue
            tds = row.css('td')

            # last character is ":". Strip that
            row_key = cleanjoin(tds[0].css('::text').extract())[:-1]
            row_value = cleanjoin(tds[1].css('::text').extract())
            collection[row_key] = row_value
        yield collection
