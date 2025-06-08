from scrapy import Item
import xml.etree.ElementTree as ET

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider

#here
class SaarlandSpider(SchoolSpider):
    name = "saarland"
    start_urls = [
        "https://geoportal.saarland.de/arcgis/services/Internet/Staatliche_Dienste/MapServer/WFSServer?SERVICE=WFS&REQUEST=GetFeature&typeName=Staatliche%5FDienste:Schulen%5FSL&srsname=EPSG:4326"
    ]

    def parse(self, response):
        tree = ET.fromstring(response.body)

        namespaces = {
            "gml": "http://www.opengis.net/gml/3.2",
            "SD": "https://geoportal.saarland.de/arcgis/services/Internet/Staatliche_Dienste/MapServer/WFSServer",
        }

        for school in tree.iter(
            "{https://geoportal.saarland.de/arcgis/services/Internet/Staatliche_Dienste/MapServer/WFSServer}Schulen_SL"
        ):
            data_elem = {}
            for entry in school:
                if (
                    entry.tag
                    == "{https://geoportal.saarland.de/arcgis/services/Internet/Staatliche_Dienste/MapServer/WFSServer}Shape"
                ):
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
        # The data also contains a field called `SCHULKENNZ` which implies that it might be an id
        # that could be used, but some schools share ids (especially `0` or `000000`) which makes for collisions
        id = item.get("OBJECTID")

        return School(
            name=item.get("SCHULNAME"),
            address=" ".join([item.get(part) for part in ["HNR", "STR_NAME"]]),
            city=item.get("ORT_NAME"),
            zip=item.get("PLZ"),
            school_type=item.get("SCHULFORM"),
            id=f"SL-{id}",
        )
