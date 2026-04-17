from scrapy import Item

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider
from jedeschule.wfs_basic_parsers import parse_geojson_features


class BerlinSpider(SchoolSpider):
    name = "berlin"
    state_key = "BE"
    start_urls = [
        "https://gdi.berlin.de/services/wfs/schulen?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&srsname=EPSG:4326"
        "&typename=fis:schulen&outputFormat=application/json"
    ]

    def parse(self, response, **kwargs):
        yield from parse_geojson_features(response)

    def normalize(self, item: Item) -> School:
        return School(
            name=item.get("schulname"),
            id=self.make_school_id("{}".format(item.get("bsn"))),
            address=" ".join([item.get("strasse"), item.get("hausnr")]),
            zip=item.get("plz"),
            city="Berlin",
            website=item.get("internet"),
            email=item.get("email"),
            school_type=item.get("schulart"),
            legal_status=item.get("traeger"),
            fax=item.get("fax"),
            phone=item.get("telefon"),
            latitude=item.get("lat"),
            longitude=item.get("lon"),
        )
