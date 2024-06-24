import xml.etree.ElementTree as ET

import scrapy
from jedeschule.items import School
from scrapy import Item


class BerlinSpider(scrapy.Spider):
    name = "berlin"
    start_urls = ['https://gdi.berlin.de/services/wfs/schulen?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&srsname=EPSG:25833&typename=fis:schulen']

    def parse(self, response):
        tree = ET.fromstring(response.body)

        namespaces = {
            "gml": "http://www.opengis.net/gml",
            "fis": "http://www.berlin.de/broker",
        }
        for school in tree.findall("gml:featureMember", namespaces):
            data_elem = {}
            for entry in school[0]:
                if entry.tag == "{http://www.berlin.de/broker}geom":
                    # This nested entry contains the coordinates that we would like to expand
                    lat, lon = entry.findtext(
                        "gml:Point/gml:pos", namespaces=namespaces
                    ).split(" ")
                    data_elem["lat"] = lat
                    data_elem["lon"] = lon
                    continue
                # strip the namespace before returning
                data_elem[entry.tag.split("}", 1)[1]] = entry.text
            yield data_elem

    @staticmethod
    def normalize(item: Item) -> School:
        return School(name=item.get('name'),
                      id='BE-{}'.format(item.get('bsn')),
                      address=" ".join([item.get('strasse'), item.get('hausnr')]),
                      zip=item.get('plz'),
                      city='Berlin',
                      website=item.get('internet'),
                      email=item.get('email'),
                      school_type=item.get('schulart'),
                      legal_status=item.get('traeger'),
                      fax=item.get('fax'),
                      phone=item.get('telefon'),
                      latitude=item.get('lat'),
                      longitude=item.get('lon')
                      )