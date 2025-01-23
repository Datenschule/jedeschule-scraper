import csv

from scrapy import Item

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class SchleswigHolsteinSpider(SchoolSpider):
    name = "schleswig-holstein"
    base_url = 'https://opendata.schleswig-holstein.de/collection/schulen/aktuell.csv'
    start_urls = [base_url]

    def parse(self, response):
        reader = csv.DictReader(response.text.splitlines(), delimiter='\t')
        for row in reader:
            yield row

    @staticmethod
    def normalize(item: Item) -> School:
        return School(name=item.get('name'),
                      id='SH-{}'.format(item.get('id')),
                      address=" ".join([item.get('street') or "", item.get('houseNumber') or ""]).strip(),
                      zip=item.get("zipcode"),
                      city=item.get("city"),
                      email=item.get('email'),
                      fax=item.get('fax'),
                      phone=item.get('phone'),
                      latitude=item.get('latitude') or None,
                      longitude=item.get('longitude') or None,
                      )
