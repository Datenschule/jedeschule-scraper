import xml.etree.ElementTree as ET

from scrapy import Item

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class BrandenburgSpider(SchoolSpider):
    name = "brandenburg"

    start_urls = [
        "https://schullandschaft.brandenburg.de/edugis/wfs/schulen?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&typename=ms:Schul_Standorte&srsname=epsg:4326"
    ]

    def parse(self, response):
        tree = ET.fromstring(response.body)

        namespaces = {
            "gml": "http://www.opengis.net/gml",
            "ms": "http://mapserver.gis.umn.edu/mapserver",
        }
        for school in tree.findall("gml:featureMember", namespaces):
            data_elem = {}
            for entry in school[0]:
                if entry.tag == "{http://mapserver.gis.umn.edu/mapserver}msGeometry":
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
        return School(
            name=item.get("schulname"),
            id="BB-{}".format(item.get("schul_nr")),
            address=item.get("strasse_hausnr"),
            zip=item.get("plz"),
            city=item.get("ort"),
            website=item.get("homepage"),
            email=item.get("dienst_email"),
            school_type=item.get("schulform"),
            fax=item.get("faxnummer"),
            phone=item.get("telefonnummer"),
            provider=item.get('schulamtname'),
            longitude=item.get("lon"),
            latitude=item.get("lat"),
        )
