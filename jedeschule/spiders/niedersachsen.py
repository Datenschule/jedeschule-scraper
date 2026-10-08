import json
import urllib

import scrapy
from pydantic import BaseModel, TypeAdapter
from scrapy import Item
from scrapy.http import Response

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class SchoolListEntry(BaseModel):
    schulnr: int


class SearchProps(BaseModel):
    schools: list[SchoolListEntry]


class SearchResponse(BaseModel):
    props: SearchProps


# Rows of [Schulnummer, latitude, longitude]; coordinates are null for some schools
MapCoordinates = TypeAdapter(list[tuple[int, float | None, float | None]])


class NiedersachsenSpider(SchoolSpider):
    name = "niedersachsen"
    allowed_domains = ["schulen.nibis.de", "karten.nibis.de"]
    start_urls = ["https://schulen.nibis.de/search/advanced"]

    def parse(self, response: Response):
        parts = [
            cookie.decode("utf-8").split("=")
            for cookie in response.headers.getlist("Set-Cookie")
        ]
        headers = {part[0]: part[1].split(";")[0] for part in parts}
        xsrf = urllib.parse.unquote(headers.get("XSRF-TOKEN"))
        yield scrapy.Request(
            "https://schulen.nibis.de/school/search",
            method="POST",
            body="""{"type":"Advanced","eingabe":null,"filters":{"classifications":[],"lschb":["RLSB Braunschweig","RLSB Hannover","RLSB Lüneburg","RLSB Osnabrück"],"towns":[],"countys":[],"regions":[],"features":[],"bbs_classifications":[],"bbs_occupations":[],"bbs_orientations":[],"plz":0,"oeffentlich":"on","privat":"on"}}""",
            headers={
                "X-XSRF-TOKEN": xsrf,
                "X-Inertia": "true",
                "Content-Type": "application/json;charset=utf-8",
            },
            callback=self.parse_list,
        )

    def parse_list(self, response: Response):
        search = SearchResponse.model_validate_json(response.text)
        school_numbers = [school.schulnr for school in search.props.schools]
        # The NiBiS map service returns already geocoded coordinates by Schulnummer
        yield scrapy.FormRequest(
            "https://karten.nibis.de/fetchAddresses.ajax.php",
            formdata={
                "input": json.dumps(
                    {"aSNo": school_numbers, "aLKs": [], "aSGLs": [], "aBes": []}
                )
            },
            headers={"X-Requested-With": "XMLHttpRequest"},
            callback=self.parse_map_coordinates,
            cb_kwargs={"school_numbers": school_numbers},
        )

    def parse_map_coordinates(self, response: Response, school_numbers: list[int]):
        coordinates = {
            school_number: (latitude, longitude)
            for school_number, latitude, longitude in MapCoordinates.validate_json(
                response.text
            )
            if latitude is not None and longitude is not None
        }
        for school_number in school_numbers:
            yield scrapy.Request(
                f"https://schulen.nibis.de/school/getInfo/{school_number}",
                callback=self.parse_details,
                cb_kwargs={"coordinates": coordinates.get(school_number)},
            )

    def parse_details(
        self, response: Response, coordinates: tuple[float, float] | None
    ):
        item = response.json()
        if coordinates:
            item["latitude"], item["longitude"] = coordinates
        yield item

    @staticmethod
    def _get(dict_like, key, default):
        # This is almost like dict_like.get(key, default)
        # but it also returns default if the dictionary's
        # value for the key is `None`.
        # A regular `.get` would just return `None` there
        # as it only fills in if the key is not defined
        # at all.
        return dict_like.get(key) or default

    @staticmethod
    def normalize(item: Item) -> School:
        name = " ".join(
            [item.get("schulname", ""), item.get("namensZusatz") or ""]
        ).strip()
        address = NiedersachsenSpider._get(item, "sdb_adressen", [{}])[0]
        ort = NiedersachsenSpider._get(address, "sdb_ort", {})
        school_type = NiedersachsenSpider._get(item, "sdb_art", {}).get("art")
        provider = NiedersachsenSpider._get(item, "sdb_traeger", {}).get("name")
        legal_status = NiedersachsenSpider._get(item, "sdb_traegerschaft", {}).get(
            "bezeichnung"
        )
        return School(
            name=name,
            phone=item.get("telefon"),
            fax=item.get("fax"),
            email=item.get("email"),
            website=item.get("homepage"),
            address=address.get("strasse"),
            zip=ort.get("plz"),
            city=ort.get("ort"),
            school_type=school_type,
            provider=provider,
            legal_status=legal_status,
            latitude=item.get("latitude"),
            longitude=item.get("longitude"),
            id="NI-{}".format(item.get("schulnr")),
        )
