from scrapy import Item

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider
from jedeschule.wfs_basic_parsers import parse_geojson_features


class SaarlandSpider(SchoolSpider):
    name = "saarland"
    start_urls = [
        "https://geoportal.saarland.de/spatial-objects/257/collections/Staatliche_Dienste:Schulen_SL/items?f=json&limit=2500"
    ]

    def parse(self, response, **kwargs):
        yield from parse_geojson_features(response)

    @staticmethod
    def normalize(item: Item) -> School:
        # The data also contains a field called `Schulkennz` which implies that it might be an id
        # that could be used, but some schools share ids (especially `0` or `000000`) or
        # do not have any set at all which makes for collisions
        school_id = item.get("OBJECTID")

        return School(
            address=item.get("Straße", "").strip(),
            city=item.get("Ort"),
            fax=item.get("Fax"),
            id=f"SL-{school_id}",
            latitude=item.get("lat"),
            longitude=item.get("lon"),
            name=item.get("Bezeichnung"),
            phone=item.get("Telefon"),
            school_type=item.get("Schulform"),
            website=item.get("Homepage"),
            zip=item.get("PLZ"),
        )
