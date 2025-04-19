import xml.etree.ElementTree as ET
from typing import Any

from scrapy.http import Response
from scrapy import Item

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class SaarlandSpider(SchoolSpider):
    name = "saarland"
    start_urls = [
        "https://geoportal.saarland.de/arcgis/services/Internet/Staatliche_Dienste/MapServer/WFSServer?SERVICE=WFS&REQUEST=GetFeature&typeName=Staatliche%5FDienste:Schulen%5FSL&srsname=EPSG:4326"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        tree = ET.fromstring(response.body)

        namespaces = {
            "gml": "http://www.opengis.net/gml/3.2",
            "Staatliche_Dienste": "https://geoportal.saarland.de/arcgis/services/Internet/Staatliche_Dienste/MapServer/WFSServer",
        }
        for school in tree.iter("{%s}Schulen_SL" % namespaces["Staatliche_Dienste"]):
            data_elem = {}
            for entry in school:
                if entry.tag == "{%s}Shape" % namespaces["Staatliche_Dienste"]:
                    lon, lat = entry.findtext(
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
            name=item.get("SCHULNAME"),
            id="SL-{}".format(item.get("OBJECTID")),
            address=(" ".join([item.get("STR_NAME"), item.get("HNR")])),
            zip=item.get("PLZ"),
            city=item.get("ORT_NAME"),
            school_type=item.get("SCHULFORM"),
            latitude=item.get("lat"),
            longitude=item.get("lon"),
        )
