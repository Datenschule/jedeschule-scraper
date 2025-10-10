import xmltodict
from scrapy import Item

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


def as_string(value: str):
    try:
        return str(int(value))
    except ValueError:
        return value


class MecklenburgVorpommernSpider(SchoolSpider):
    name = "mecklenburg-vorpommern"
    start_urls = [
        "https://www.geodaten-mv.de/dienste/schulstandorte_wfs?"
        "SERVICE=WFS&REQUEST=GetFeature&VERSION=2.0.0&srsname=EPSG%3A4326&typeNames="
        "ms:schultyp_grund,"
        "ms:schultyp_regional,"
        "ms:schultyp_gymnasium,"
        "ms:schultyp_gesamt,"
        "ms:schultyp_waldorf,"
        "ms:schultyp_foerder,"
        "ms:schultyp_abendgym,"
        "ms:schultyp_berufs"
    ]

    def parse(self, response, **kwargs):
        data = xmltodict.parse(response.text)

        feature_collection = data.get("wfs:FeatureCollection", {})
        members = feature_collection.get("wfs:member", [])

        if not isinstance(members, list):
            members = [members]

        for member in members:
            if "wfs:FeatureCollection" in member:
                inner_members = member["wfs:FeatureCollection"].get("wfs:member", [])
                if not isinstance(inner_members, list):
                    inner_members = [inner_members]
                
                for inner_member in inner_members:
                    school_data = next(iter(inner_member.values()), {})
                    yield self._extract_school_data(school_data)
            else:
                school_data = next(iter(member.values()), {})
                yield self._extract_school_data(school_data)

    def _extract_school_data(self, school):
        data_elem = {}

        for key, value in school.items():
            if key == "ms:msGeometry":
                point = value.get("gml:Point", {})
                pos = point.get("gml:pos", "")
                if pos:
                    lat, lon = pos.split()
                    data_elem["lat"] = float(lat)
                    data_elem["lon"] = float(lon)
            elif not key.startswith("@"):
                clean_key = key.split(":", 1)[-1] if ":" in key else key
                data_elem[clean_key] = value

        return data_elem

    @staticmethod
    def normalize(item: Item) -> School:
        def safe_strip(value):
            """Safely strip a value, handling None values"""
            return value.strip() if value is not None else ""
        
        return School(
            name=safe_strip(item.get("schulname")),
            id="MV-{}".format(as_string(item.get("dstnr", ""))),
            address=safe_strip(item.get("strassehnr")),
            address2="",
            zip=as_string(item.get("plz", "")).zfill(5),
            city=safe_strip(item.get("ort")),
            website=safe_strip(item.get("internet")),
            email=safe_strip(item.get("emailadresse")),
            phone=safe_strip(item.get("telefon")),
            director=safe_strip(item.get("schulleiter")),
            school_type=safe_strip(item.get("orgform")),
            legal_status=safe_strip(item.get("rechtsstatus")),
            provider=safe_strip(item.get("schultraeger")),
            latitude=item.get("lat"),
            longitude=item.get("lon"),
        )
