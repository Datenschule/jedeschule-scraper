import xmltodict
from scrapy import Item

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class HamburgSpider(SchoolSpider):
    name = "hamburg"

    start_urls = [
        "https://geodienste.hamburg.de/HH_WFS_Schulen?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature"
        "&typename=de.hh.up:nicht_staatliche_schulen,de.hh.up:staatliche_schulen&srsname=EPSG:4326"
        # "&maxFeatures=1"
    ]

    def parse(self, response, **kwargs):
        data = xmltodict.parse(response.body)

        feature_collection = data.get("wfs:FeatureCollection", {})
        members = feature_collection.get("gml:featureMember", [])

        if not isinstance(members, list):
            members = [members]

        for member in members:
            school_data = (member.get("de.hh.up:staatliche_schulen") or
                           member.get("de.hh.up:nicht_staatliche_schulen"))
            if not school_data:
                continue

            result = {}
            for key, value in school_data.items():
                if key == "de.hh.up:the_geom":
                    coords = value["gml:Point"]["gml:pos"]
                    lon, lat = map(float, coords.split())
                    result["lat"] = lat
                    result["lon"] = lon
                else:
                    result[key.split(":")[-1]] = value

            yield result

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
