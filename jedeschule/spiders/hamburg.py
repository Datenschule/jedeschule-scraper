from lxml import etree
from scrapy import Item

from jedeschule.spiders.school_spider import SchoolSpider
from jedeschule.items import School


class HamburgSpider(SchoolSpider):
    name = 'hamburg'

    start_urls = ['https://geoportal-hamburg.de/geodienste_hamburg_de/HH_WFS_Schulen?REQUEST=GetFeature&SERVICE=WFS&SRSNAME=EPSG%3A25832&TYPENAME=staatliche_schulen&VERSION=1.1.0']

    def parse(self, response):
        elem = etree.fromstring(response.body)

        for member in elem:
            data_elem = {}
            for attr in member[0]:
                data_elem[attr.tag.split('}', 1)[1]] = attr.text
            yield data_elem

    @staticmethod
    def normalize(item: Item) -> School:
        city_parts = item.get('adresse_ort').split()
        zip_code, city = city_parts[0], city_parts[1:]
        return School(name=item.get('schulname'),
                      id='HH-{}'.format(item.get('schul_id')),
                      address=item.get('adresse_strasse_hausnr'),
                      address2='',
                      zip=zip_code,
                      city=' '.join(city),
                      website=item.get('schul_homepage'),
                      email=item.get('schul_email'),
                      school_type=item.get('schulform'),
                      fax=item.get('fax'),
                      phone=item.get('schul_telefonnr'),
                      director=item.get('name_schulleiter'))
