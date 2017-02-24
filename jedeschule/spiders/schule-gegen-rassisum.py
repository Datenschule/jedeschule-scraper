import scrapy
from jedeschule.utils import cleanjoin
from scrapy.shell import inspect_response


class SchuleGegenRassismusSpider(scrapy.Spider):
    name = "schule-gegen-rassismus"
    start_urls = ['http://www.schule-ohne-rassismus.org/courage-schulen/alle-courage-schulen/']

    def parse(self, response):
        schoolcards = response.css(".news-list-item")
        for schoolcard in schoolcards:
            school = {}
            link = schoolcard.css('#schoolcard_name a')
            school['name'] = link.css('::text').extract_first().strip()
            school['link'] = link.css('::attr(href)').extract_first().strip()
            godfather = schoolcard.css('#schoolcard_godparent p::text').extract_first().split(':')
            school['pate'] = godfather[1] if len(godfather) > 1 else godfather[0]
            school['date'] = schoolcard.css('#schoolcard_title .news-list-date::text').extract_first().strip()
            school['category'] = schoolcard.css('#schoolcard_legend::text').extract_first().strip()
            yield scrapy.Request('http://www.schule-ohne-rassismus.org/' + school['link'],
                                 meta= {'school': school},
                                 callback=self.parse_detail)
        if (len(schoolcards) == 20):
            next = response.css("div.news-list-browse a:contains('chste')::attr(href)").extract_first()
            request = scrapy.Request('http://www.schule-ohne-rassismus.org/' + next,
                                 callback=self.parse)
            yield request

    def parse_detail(self, response):
        school = response.meta['school']

        address = response.css('.news-single-item p::text').extract()
        #inspect_response(response, self)
        school['street'] = address[0]
        if (len(address) > 1):
            address2 = address[1].split(' ')
            school['postcode'] = address2[0]
            address2.pop(0)
            school['place'] = ' '.join(address2)
        yield school


