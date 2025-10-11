import xmltodict
from scrapy import Item

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class ThueringenSpider(SchoolSpider):
    name = "thueringen"
    start_urls = [
        "https://www.geoproxy.geoportal-th.de/geoproxy/services/kommunal/komm_wfs?"
        "SERVICE=WFS&REQUEST=GetFeature&typeNames=kommunal:komm_schul&"
        "srsname=EPSG:4326&VERSION=2.0.0"
    ]

    def parse(self, response, **kwargs):
        data = xmltodict.parse(response.text)
        members = data.get("wfs:FeatureCollection", {}).get("wfs:member", [])

        if not isinstance(members, list):
            members = [members]

        for member in members:
            school = member.get("kommunal:komm_schul", {})

            data_elem = {}

            # Extract geometry coordinates
            geom = school.get("kommunal:GEOM", {})
            point = geom.get("gml:Point", {})
            pos = point.get("gml:pos", "")
            if pos:
                lon, lat = pos.split()
                data_elem["lat"] = float(lat)
                data_elem["lon"] = float(lon)

            # Extract all other fields
            for key, value in school.items():
                if key not in ("kommunal:GEOM", "@gml:id") and value:
                    # Remove namespace prefix
                    clean_key = key.split(":", 1)[-1] if ":" in key else key
                    data_elem[clean_key] = value

            yield data_elem

    @staticmethod
    def normalize(item: Item) -> School:
        return School(
            name=item.get("Name"),
            id="TH-{}".format(item.get("Schulnummer")),
            address=" ".join(
                filter(None, [item.get("Strasse"), item.get("Hausnummer")])
            ),
            zip=item.get("PLZ"),
            city=item.get("Ort"),
            website=item.get("Webseite"),
            email=item.get("EMail"),
            school_type=item.get("Schulart"),
            provider=item.get("Traeger"),
            fax=item.get("Faxnummer"),
            phone=item.get("Telefonnummer"),
            latitude=item.get("lat"),
            longitude=item.get("lon"),
        )
