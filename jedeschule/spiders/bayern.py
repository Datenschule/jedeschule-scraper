import xml.etree.ElementTree as ET
import scrapy
from scrapy import Item

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class BayernSpider(SchoolSpider):
    name = "bayern"
    start_urls = ['https://gdiserv.bayern.de/srv112940/services/schulstandortebayern-wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities']

    def parse(self, response, **kwargs):
        tree = ET.fromstring(response.body)
        base_url = 'https://gdiserv.bayern.de/srv112940/services/schulstandortebayern-wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&srsname=EPSG:4326&typename='
        for feature_type in tree.iter("{http://www.opengis.net/wfs/2.0}FeatureType"):
            feature = feature_type.findtext("{http://www.opengis.net/wfs/2.0}Title")
            yield scrapy.Request(f"{base_url}{feature}", callback=self.parse_resource, cb_kwargs={"feature": feature})

    def parse_resource(self, response, feature):
        tree = ET.fromstring(response.body)
        namespaces = {
            "gml": "http://www.opengis.net/gml/3.2",
            "schul": "http://gdi.bayern/brbschul"
        }
        key = "{http://gdi.bayern/brbschul}" + feature
        for school in tree.iter(key):
            data_elem = {'id': school.attrib["{http://www.opengis.net/gml/3.2}id"]}

            for entry in school:
                if entry.tag == "{http://gdi.bayern/brbschul}geometry":
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
        return School(name=item.get('schulname'),
                      address=item.get('strasse'),
                      city=item.get('ort'),
                      school_type=item.get('schulart'),
                      zip=item.get('postleitzahl'),
                      id='BY-{}'.format(item.get('id')),
                      latitude=item.get('lat'),
                      longitude=item.get('lon')
                      )