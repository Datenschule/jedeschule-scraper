from scrapy import Item

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider
from jedeschule.wfs_basic_parsers import parse_geojson_features


class HamburgSpider(SchoolSpider):
    name = "hamburg"

    start_urls = [
        "https://api.hamburg.de/datasets/v1/schulen/collections/staatliche_schulen/items"
        "?crs=http://www.opengis.net/def/crs/EPSG/0/4326"
        "&limit=1000",
        "https://api.hamburg.de/datasets/v1/schulen/collections/nicht_staatliche_schulen/items"
        "?crs=http://www.opengis.net/def/crs/EPSG/0/4326"
        "&limit=1000"
    ]

    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "application/geo+json, application/json, */*"
        }
    }

    def parse(self, response, **kwargs):
        yield from parse_geojson_features(response, invert=True)

    @staticmethod
    def normalize(item: Item) -> School:
        city_parts = item.get("adresse_ort").split()
        zip_code, city = city_parts[0], city_parts[1:]
        return School(
            name=item.get("schulname"),
            id="HH-{}".format(item.get("schul_id")),
            address=item.get("adresse_strasse_hausnr"),
            address2="",
            zip=zip_code,
            city=" ".join(city),
            website=item.get("schul_homepage"),
            email=item.get("schul_email"),
            school_type=item.get("schulform"),
            fax=item.get("fax"),
            phone=item.get("schul_telefonnr"),
            director=item.get("name_schulleiter"),
            latitude=item.get("lat"),
            longitude=item.get("lon"),
        )
