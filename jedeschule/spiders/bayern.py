import xmltodict
from scrapy import Item

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class BayernSpider(SchoolSpider):
    name = "bayern"
    start_urls = [
        "https://gdiserv.bayern.de/srv112940/services/schulstandortebayern-wfs?"
        "SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&srsname=EPSG:4326&typename="
            "schul:SchulstandorteGrundschulen,"
            "schul:SchulstandorteMittelschulen,"
            "schul:SchulstandorteRealschulen,"
            "schul:SchulstandorteGymnasien,"
            "schul:SchulstandorteBeruflicheSchulen,"
            "schul:SchulstandorteFoerderzentren,"
            "schul:SchulstandorteWeitererSchulen"
    ]

    def parse(self, response, **kwargs):
        data = xmltodict.parse(response.text)
        members = data.get("wfs:FeatureCollection", {}).get("wfs:member", [])

        if not isinstance(members, list):
            members = [members]

        for member in members:
            # Each member is a dict with one key = school tag, value = school data dict
            school = next(iter(member.values()), {})

            data_elem = {
                "id": school.get("@gml:id")
            }

            for key, value in school.items():
                if key == "schul:geometry":
                    point = value.get("gml:Point", {})
                    pos = point.get("gml:pos", "")
                    if pos:
                        lon, lat = pos.split()
                        data_elem["lat"] = float(lat)
                        data_elem["lon"] = float(lon)
                elif not key.startswith("@"):
                    clean_key = key.split(":", 1)[-1]
                    data_elem[clean_key] = value

            yield data_elem

    @staticmethod
    def normalize(item: Item) -> School:
        return School(
            name=item.get("schulname"),
            address=item.get("strasse"),
            city=item.get("ort"),
            school_type=item.get("schulart"),
            zip=item.get("postleitzahl"),
            id="BY-{}".format(item.get("id")),
            latitude=item.get("lat"),
            longitude=item.get("lon"),
        )
