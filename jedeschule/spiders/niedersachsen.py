import scrapy
from scrapy import Item

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider
from jedeschule.utils import cleanjoin


class NiedersachsenSpider(SchoolSpider):
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
            row_value = cleanjoin(tds[1].css('::text').extract(), "\n")

            if row_key == 'Schulname':
                row_value = row_value.replace('\n', ' ')

            collection[row_key] = row_value
        collection['data_url'] = response.url
        yield collection

    @staticmethod
    def normalize(item: Item) -> School:
        city_parts = item.get('Ort').split()
        zip, city = city_parts[0], ' '.join(city_parts[1:])
        return School(name=item.get('Schule'),
                        phone=item.get('Tel'),
                        fax=None,
                        email=item.get('E-Mail'),
                        website=item.get('Homepage'),
                        address=item.get('Straße'),
                        zip=zip,
                        city=city,
                        school_type=item.get("Schul-gliederung(en)"),
                        id='NI-{}'.format(item.get('Schulnummer')))
