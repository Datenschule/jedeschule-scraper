import json
import logging

from scrapy import Item

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class BerlinSpider(SchoolSpider):
    name = "berlin"
    start_urls = [
        "https://gdi.berlin.de/services/wfs/schulen?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&srsname=EPSG:4326&"
        "typename=fis:schulen&outputFormat=application/json"
        # "&maxFeatures=1"
    ]

    def parse(self, response, **kwargs):
        geojson = json.loads(response.text)

        for feature in geojson.get("features", []):
            properties = feature.get("properties", {})
            coords = feature.get("geometry", {}).get("coordinates", [])

            try:
                properties["lon"] = coords[0]
                properties["lat"] = coords[1]
            except (TypeError, IndexError):
                logging.warning("Skipping feature with invalid geometry")

            yield properties

    @staticmethod
    def normalize(item: Item) -> School:
        return School(
            name=item.get("schulname"),
            id="BE-{}".format(item.get("bsn")),
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
