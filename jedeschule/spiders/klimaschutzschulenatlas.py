import scrapy
from jedeschule.utils import cleanjoin
from scrapy.shell import inspect_response


class KlimaschutzSchulenAtlasSpider(scrapy.Spider):
    name = "klimaschutzschulenatlas"
    start_urls = ['https://www.klimaschutzschulenatlas.de/der-atlas']

    def parse(self, response):
        #inspect_response(response, self)
        yield scrapy.FormRequest.from_response(
            response, callback=self.parse_projectlist)

    def parse_projectlist(self, response):
        #inspect_response(response, self)
        schoollinks = response.css(".media-body > a::attr(href)").extract()
        for link in schoollinks:
            yield scrapy.Request('https://www.klimaschutzschulenatlas.de' + link,
                                 callback=self.parse_school)
        if len(schoollinks) == 16:
            next_page = response.css('.pagination a::attr(href)').extract()[-2]
            yield scrapy.Request('https://www.klimaschutzschulenatlas.de' + next_page,
                                 callback=self.parse_projectlist)

    def parse_school(self, response):
        #inspect_response(response, self)
        school = {}
        school_information = response.css('.school-info li::text').extract()
        school['type'] = school_information[0] if len(school_information) > 0 else ''
        school['state'] = school_information[1] if len(school_information) > 1 else ''
        school['street'] = school_information[2] if len(school_information) > 2 else ''
        if len(school_information) > 4:
            address_information = school_information[3].strip().split(' ')
            school['plz'] = address_information[0]
            school['place'] = address_information[1]

        projects = response.css('.col-xs-6 a::attr(title)').extract()

        for project in projects:
            school['project'] = project
            yield school