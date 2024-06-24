import csv
import json

import scrapy
import scrapy.http
from scrapy import Item

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class SchleswigHolsteinSpider(SchoolSpider):
    name = "schleswig-holstein"
    base_url = 'https://opendata.schleswig-holstein.de/collection/schulen/aktuell'
    start_urls = [base_url]

    def parse(self, response):
        url = response.css('link[rel="alternate"][type="application/ld+json"]::attr(href)').get()
        yield scrapy.Request(url, callback=self.parse_dataset_metadata)

    def parse_dataset_metadata(self, response):
        parsed = json.loads(response.text)
        csv_url = next(node['dcat:accessURL']['@id'] for node in parsed['@graph'] if
                       node['dcat:mediaType']['@id'] == 'https://www.iana.org/assignments/media-types/text/csv')
        # TODO: Remove this temporary replacement
        #  It is only here because the API seems to return wrong data currently
        csv_url = csv_url.replace("zitsh.de", "schleswig-holstein.de")
        yield scrapy.Request(csv_url, callback=self.parse_csv)

    def parse_csv(self, response: scrapy.http.Response):
        reader = csv.DictReader(response.text.splitlines(), delimiter='\t')
        for row in reader:
            yield row

    @staticmethod
    def normalize(item: Item) -> School:
        return School(name=item.get('name'),
                      id='SH-{}'.format(item.get('id')),
                      address=" ".join([item.get('street'), item.get('houseNumber')]),
                      zip=item.get("zipcode"),
                      city=item.get("city"),
                      email=item.get('email'),
                      fax=item.get('fax'),
                      phone=item.get('phone'),
                      latitude=item.get('latitude') or None,
                      longitude=item.get('longitude') or None,
                      )
