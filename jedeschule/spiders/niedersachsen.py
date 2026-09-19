import json
import math
import urllib

import scrapy
from scrapy import Item
from scrapy.http import Response

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


MAP_COORDS_URL = "https://karten.nibis.de/fetchAddresses.ajax.php"
SCHOOL_DETAILS_URL = "https://schulen.nibis.de/school/getInfo/{schulnr}"
SEARCH_PAYLOAD = {
    "type": "Advanced",
    "eingabe": None,
    "filters": {
        "classifications": [],
        "lschb": [
            "RLSB Braunschweig",
            "RLSB Hannover",
            "RLSB Lüneburg",
            "RLSB Osnabrück",
        ],
        "towns": [],
        "countys": [],
        "regions": [],
        "features": [],
        "bbs_classifications": [],
        "bbs_occupations": [],
        "bbs_orientations": [],
        "plz": 0,
        "oeffentlich": "on",
        "privat": "on",
    },
}


def _valid_coordinates(latitude, longitude) -> bool:
    return (
        isinstance(latitude, (int, float))
        and isinstance(longitude, (int, float))
        and math.isfinite(latitude)
        and math.isfinite(longitude)
        and -90 <= latitude <= 90
        and -180 <= longitude <= 180
    )


def _school_number(value) -> str | None:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        return None
    number = str(value)
    if number.isascii() and number.isdecimal() and int(number) > 0:
        return number
    return None


class NiedersachsenSpider(SchoolSpider):
    name = "niedersachsen"
    allowed_domains = ["schulen.nibis.de", "karten.nibis.de"]
    start_urls = ["https://schulen.nibis.de/search/advanced"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._coords: dict[str, tuple[float, float]] = {}

    def parse(self, response: Response):
        xsrf = ""
        for cookie in response.headers.getlist("Set-Cookie"):
            name, separator, value = cookie.decode("utf-8").partition("=")
            if name == "XSRF-TOKEN" and separator:
                xsrf = urllib.parse.unquote(value.split(";", 1)[0])
                break
        yield scrapy.Request(
            "https://schulen.nibis.de/school/search",
            method="POST",
            body=json.dumps(SEARCH_PAYLOAD),
            headers={
                "X-XSRF-TOKEN": xsrf,
                "X-Inertia": "true",
                "Content-Type": "application/json;charset=utf-8",
            },
            callback=self.parse_api_search,
        )

    def parse_api_search(self, response: Response):
        try:
            json_response = json.loads(response.text)
        except json.JSONDecodeError as exc:
            self.logger.error("Could not parse Niedersachsen school list: %s", exc)
            return
        props = json_response.get("props") if isinstance(json_response, dict) else None
        schools = props.get("schools") if isinstance(props, dict) else None
        if not isinstance(schools, list):
            self.logger.error("Niedersachsen search response has no school list")
            return
        valid_schools = [
            school for school in schools
            if isinstance(school, dict) and _school_number(school.get("schulnr"))
        ]
        if len(valid_schools) != len(schools):
            self.logger.warning("Skipping %d school list entries with invalid IDs", len(schools) - len(valid_schools))
        schools = valid_schools
        school_numbers = [_school_number(school["schulnr"]) for school in schools]
        if not school_numbers:
            return

        # The map service returns coordinates keyed by Schulnummer. Passing the
        # IDs from the school API keeps both requests on the same school set.
        yield scrapy.FormRequest(
            MAP_COORDS_URL,
            formdata={
                "input": json.dumps(
                    {"aSNo": school_numbers, "aLKs": [], "aSGLs": [], "aBes": []}
                )
            },
            headers={"X-Requested-With": "XMLHttpRequest"},
            callback=self.parse_map_coords,
            errback=self.parse_map_coords_failure,
            cb_kwargs={"schools": schools},
        )

    def parse_map_coords(self, response: Response, schools: list[dict]):
        try:
            rows = json.loads(response.text)
        except (json.JSONDecodeError, TypeError) as exc:
            self.logger.error("Could not parse Niedersachsen map coordinates: %s", exc)
            rows = []
        if not isinstance(rows, list):
            self.logger.error("Niedersachsen map response is not a coordinate list")
            rows = []

        self._coords = {}
        school_numbers = {
            _school_number(school.get("schulnr"))
            for school in schools if isinstance(school, dict)
        } - {None}
        for row in rows:
            if not isinstance(row, list) or len(row) != 3:
                continue
            schulnr, latitude, longitude = row
            school_number = _school_number(schulnr)
            if school_number not in school_numbers:
                continue
            if isinstance(latitude, bool) or isinstance(longitude, bool):
                continue
            try:
                latitude = float(latitude)
                longitude = float(longitude)
            except (TypeError, ValueError):
                continue
            if _valid_coordinates(latitude, longitude):
                self._coords[school_number] = (latitude, longitude)

        self.logger.info(
            "Loaded %d/%d Schulnummer -> coordinates from NiBiS map service",
            len(self._coords),
            len(schools),
        )

        yield from self._detail_requests(schools)

    def parse_map_coords_failure(self, failure):
        self.logger.error("Could not fetch Niedersachsen map coordinates: %s", failure.getErrorMessage())
        self._coords = {}
        yield from self._detail_requests(failure.request.cb_kwargs["schools"])

    def _detail_requests(self, schools: list[dict]):
        for school in schools:
            school_number = _school_number(school.get("schulnr")) if isinstance(school, dict) else None
            if school_number is None:
                continue
            yield scrapy.Request(
                SCHOOL_DETAILS_URL.format(schulnr=school_number),
                callback=self.parse_details,
                cb_kwargs={"school_number": school_number},
            )

    def parse_details(self, response: Response, school_number: str | None = None):
        try:
            item = json.loads(response.text)
        except (json.JSONDecodeError, TypeError) as exc:
            self.logger.error(
                "Could not parse Niedersachsen detail JSON from %s: %s",
                response.url,
                exc,
            )
            return

        returned_number = _school_number(item.get("schulnr")) if isinstance(item, dict) else None
        if returned_number is None:
            self.logger.error("Skipping Niedersachsen detail response with invalid school ID: %s", response.url)
            return
        if school_number is not None and returned_number != school_number:
            self.logger.error("Skipping Niedersachsen detail response for %s: expected school %s, got %s", response.url, school_number, returned_number)
            return

        coord = self._coords.get(returned_number)
        if coord is not None:
            item["latitude"], item["longitude"] = coord

        yield item

    @staticmethod
    def normalize(item: Item) -> School:
        school_number = _school_number(item.get("schulnr"))
        if school_number is None:
            raise ValueError("Cannot normalize Niedersachsen school without a valid Schulnummer")
        suffix = item.get("namensZusatz") or item.get("namenszusatz") or ""
        name = " ".join(part for part in [item.get("schulname", ""), suffix] if part).strip()

        addresses = item.get("sdb_adressen") or []
        address = item.get("hauptsitz") or (addresses[0] if addresses else {})
        address = address or {}
        ort = address.get("sdb_ort") or {}
        school_type = (item.get("sdb_art") or {}).get("art")
        provider = (item.get("sdb_traeger") or {}).get("name")

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
            legal_status=(item.get("sdb_traegerschaft") or {}).get("bezeichnung"),
            latitude=item.get("latitude"),
            longitude=item.get("longitude"),
            id=f"NI-{school_number}",
        )
