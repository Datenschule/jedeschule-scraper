import xml.etree.ElementTree as ET

from scrapy import Item

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class BrandenburgSpider(SchoolSpider):
    name = "brandenburg"

    start_urls = [
        "https://schullandschaft.brandenburg.de/edugis/wfs/schulen?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&typename=ms:Schul_Standorte"
    ]

    def parse(self, response):
        elem = ET.fromstring(response.body)

        for member in elem:
            data_elem = {}
            for attr in member[0]:
                data_elem[attr.tag.split("}", 1)[1]] = attr.text
            yield data_elem

    @staticmethod
    def normalize(item: Item) -> School:
        return School(
            name=item.get("schulname"),
            id="BB-{}".format(item.get("schul_nr")),
            address=item.get("strasse_hausnr"),
            address2="",
            zip=item.get("plz"),
            city=item.get("ort"),
            website=item.get("homepage"),
            email=item.get("dienst_email"),
            school_type=item.get("schulform"),
            fax=item.get("faxnummer"),
            phone=item.get("telefonnummer"),
        )
