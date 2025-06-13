import xmltodict
from scrapy import Item

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class SaarlandSpider(SchoolSpider):
    name = "saarland"
    start_urls = [
        "https://geoportal.saarland.de/arcgis/services/Internet/Staatliche_Dienste/MapServer/WFSServer?"
        "SERVICE=WFS&REQUEST=GetFeature&typeName=Staatliche%5FDienste:Schulen%5FSL&srsname=EPSG:4326"
    ]

    def parse(self, response, **kwargs):
        data = xmltodict.parse(response.text)

        members = data.get("wfs:FeatureCollection", {}).get("wfs:member", [])
        if not isinstance(members, list):
            members = [members]

        for member in members:
            school = member.get("Staatliche_Dienste:Schulen_SL", {})
            data_elem = {}

            for key, value in school.items():
                if key == "Staatliche_Dienste:Shape":
                    pos = (
                        value.get("gml:Point", {})
                        .get("gml:pos", "")
                        .strip()
                    )
                    if pos:
                        lat, lon = pos.split()
                        data_elem["lat"] = lat
                        data_elem["lon"] = lon
                else:
                    clean_key = key.split(":")[-1]
                    data_elem[clean_key] = value

            yield data_elem

    @staticmethod
    def normalize(item: Item) -> School:
        # The data also contains a field called `SCHULKENNZ` which implies that it might be an id
        # that could be used, but some schools share ids (especially `0` or `000000`) which makes for collisions
        object_id = item.get("OBJECTID")

        return School(
            name=item.get("SCHULNAME"),
            address=" ".join(filter(None, [item.get(part) for part in ["HNR", "STR_NAME"]])),
            city=item.get("ORT_NAME"),
            zip=item.get("PLZ"),
            school_type=item.get("SCHULFORM"),
            id=f"SL-{object_id}",
        )
