import json
import math
from pathlib import Path
import urllib

import scrapy
from scrapy import Item
from scrapy.http import Response

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


MAP_COORDS_URL = "https://karten.nibis.de/fetchAddresses.ajax.php"
SCHOOL_DETAILS_URL = "https://schulen.nibis.de/school/getInfo/{schulnr}"
OVERRIDES_PATH = Path(__file__).with_name("niedersachsen_coordinate_overrides.json")
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


def load_coordinate_overrides(path: Path = OVERRIDES_PATH) -> dict[str, tuple[float, float]]:
    """Load explicit, human-approved coordinate corrections keyed by NI ID."""
    if not path.exists():
        return {}

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Niedersachsen coordinate overrides must be a JSON object")
    overrides = payload.get("overrides", {})
    if not isinstance(overrides, dict):
        raise ValueError("Niedersachsen coordinate overrides must contain an object")

    result = {}
    for school_id, value in overrides.items():
        if not isinstance(school_id, str) or not school_id.startswith("NI-"):
            raise ValueError(f"Invalid Niedersachsen override ID: {school_id!r}")
        if not isinstance(value, dict) or not _valid_coordinates(
            value.get("latitude"), value.get("longitude")
        ):
            raise ValueError(f"Invalid coordinates for Niedersachsen override {school_id}")
        result[school_id] = (float(value["latitude"]), float(value["longitude"]))
    return result


class NiedersachsenSpider(SchoolSpider):
    name = "niedersachsen"
    allowed_domains = ["schulen.nibis.de", "karten.nibis.de"]
    start_urls = ["https://schulen.nibis.de/search/advanced"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._coords: dict[str, tuple[float, float]] = {}
        self._coordinate_overrides = load_coordinate_overrides()
        self.logger.info("Loaded %d Niedersachsen coordinate overrides", len(self._coordinate_overrides))

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
        json_response = json.loads(response.text)
        schools = json_response.get("props", {}).get("schools", [])
        school_numbers = [
            str(school["schulnr"])
            for school in schools
            if school.get("schulnr") is not None
        ]

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

        self._coords = {}
        for row in rows:
            if not isinstance(row, list) or len(row) != 3:
                continue
            schulnr, latitude, longitude = row
            try:
                latitude = float(latitude)
                longitude = float(longitude)
            except (TypeError, ValueError):
                continue
            if _valid_coordinates(latitude, longitude):
                self._coords[str(schulnr)] = (latitude, longitude)

        self.logger.info(
            "Loaded %d/%d Schulnummer -> coordinates from NiBiS map service",
            len(self._coords),
            len(schools),
        )

        yield from self._detail_requests(schools)

    def parse_map_coords_failure(self, failure, schools: list[dict]):
        self.logger.error("Could not fetch Niedersachsen map coordinates: %s", failure.getErrorMessage())
        yield from self._detail_requests(schools)

    def _detail_requests(self, schools: list[dict]):
        for school in schools:
            school_number = school.get("schulnr")
            if school_number is None:
                continue
            yield scrapy.Request(
                SCHOOL_DETAILS_URL.format(schulnr=school_number),
                callback=self.parse_details,
            )

    def parse_details(self, response: Response):
        try:
            item = json.loads(response.text)
        except (json.JSONDecodeError, TypeError) as exc:
            self.logger.error(
                "Could not parse Niedersachsen detail JSON from %s: %s",
                response.url,
                exc,
            )
            return

        school_id = f"NI-{item.get('schulnr')}"
        coord = self._coordinate_overrides.get(school_id) or self._coords.get(
            str(item.get("schulnr"))
        )
        if coord is not None:
            item["latitude"], item["longitude"] = coord

        yield item

    @staticmethod
    def normalize(item: Item) -> School:
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
            legal_status=item.get("sdb_traegerschaft", {}).get("bezeichnung"),
            latitude=item.get("latitude"),
            longitude=item.get("longitude"),
            id="NI-{}".format(item.get("schulnr")),
        )
