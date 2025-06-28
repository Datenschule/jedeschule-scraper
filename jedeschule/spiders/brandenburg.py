from scrapy import Item

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider
from jedeschule.utils.wfs_basic_parsers import parse_geojson_features


class BrandenburgSpider(SchoolSpider):
    name = "brandenburg"

    start_urls = [
        "https://schullandschaft.brandenburg.de/edugis/wfs/schulen?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&typename=ms:Schul_Standorte"
        "&srsname=epsg:4326&outputFormat=application/json"
    ]

    def parse(self, response, **kwargs):
        yield from parse_geojson_features(response)

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
            provider=item.get("schulamtname"),
            longitude=item.get("lon"),
            latitude=item.get("lat"),
        )
