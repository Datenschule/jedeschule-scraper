import json
import os
import re
import unicodedata
import urllib

import scrapy
import shapefile
from scrapy import Item
from scrapy.http import Response

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


FORM_ALIASES = {
    "gs": "grundschule",
    "ghs": "grund und hauptschule",
    "hs": "hauptschule",
    "rs": "realschule",
    "obs": "oberschule",
    "igs": "integrierte gesamtschule",
    "kgs": "kooperative gesamtschule",
    "gym": "gymnasium",
    "bbs": "berufsbildende schule",
    "bfs": "berufsfachschule",
    "berufsbildende schulen": "berufsbildende schule",
    "berufliche schulen": "berufsbildende schule",
}

NAME_DROP_TOKENS = {
    "bbs",
    "bfs",
    "bos",
    "ev",
    "evangelisch",
    "evangelische",
    "f",
    "fachoberschule",
    "foerderschule",
    "fuer",
    "fur",
    "fs",
    "gesamtschule",
    "ggmbh",
    "ghs",
    "ggs",
    "gmbh",
    "grund",
    "grundschule",
    "gs",
    "gym",
    "gymnasium",
    "hauptschule",
    "hs",
    "igs",
    "int",
    "integrierte",
    "internationale",
    "international",
    "kath",
    "katholisch",
    "katholische",
    "kgs",
    "kooperative",
    "obs",
    "oberschule",
    "privat",
    "private",
    "rs",
    "realschule",
    "schule",
    "schueler",
    "und",
}

AREA_DROP_TOKENS = {
    "kreisfreie",
    "kreisfreier",
    "landkreis",
    "landeshauptstadt",
    "region",
    "stadt",
}


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower().strip().replace("ß", "ss")
    text = "".join(
        char
        for char in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(char)
    )
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_name(name: str) -> str:
    tokens = []
    for token in normalize_text(name).split():
        if token in NAME_DROP_TOKENS:
            continue
        tokens.append(token)
    return " ".join(tokens)


def normalize_area(area: str) -> str:
    tokens = []
    for token in normalize_text(area).split():
        if token in AREA_DROP_TOKENS:
            continue
        tokens.append(token)
    return " ".join(tokens)


def normalize_form(form: str) -> str:
    text = normalize_text(form)
    if text.startswith("foerderschwerpunkt "):
        text = text.replace("foerderschwerpunkt ", "", 1)
    if text.startswith("schwerpunkt "):
        text = text.replace("schwerpunkt ", "", 1)
    return FORM_ALIASES.get(text, text)


def build_match_key(name: str, area: str, form: str) -> str:
    # Keep the join key intentionally small and deterministic for the POC:
    # only schools with an exact normalized name + area + form match get geodata.
    normalized_name = normalize_name(name)
    normalized_area = normalize_area(area)
    normalized_form = normalize_form(form)
    if not normalized_name or not normalized_area or not normalized_form:
        return ""
    return "|".join([normalized_name, normalized_area, normalized_form])


def first_present(data: dict, *keys):
    for key in keys:
        value = data.get(key)
        if value:
            return value
    return ""


class NiedersachsenSpider(SchoolSpider):
    name = "niedersachsen"
    allowed_domains = ["schulen.nibis.de"]
    start_urls = ["https://schulen.nibis.de/search/advanced"]

    SHAPEFILE_BASE = os.path.join(
        os.path.dirname(__file__), "..", "..", "cache", "niedersachsen_shapefiles"
    )
    LOCAL_SHAPEFILE_PATH = os.path.join(SHAPEFILE_BASE, "ABS_Shape2024")

    def _load_local_geodata_index(self):
        if getattr(self, "_local_geodata_loaded", False):
            return

        self._local_geodata_loaded = True
        self._local_geodata_enabled = False
        self._local_geodata_index = {}
        duplicate_keys = set()

        if not os.path.exists(f"{self.LOCAL_SHAPEFILE_PATH}.shp"):
            # Missing local shapefiles should not break the spider; we just keep
            # the existing API-only behavior until the manual files are present.
            self.logger.warning(
                "Missing local Niedersachsen shapefile ABS_Shape2024; falling back to API-only mode"
            )
            return

        reader = shapefile.Reader(self.LOCAL_SHAPEFILE_PATH, encoding="iso-8859-1")
        field_names = [field[0] for field in reader.fields[1:]]

        for shape_record in reader.iterShapeRecords():
            if not shape_record.shape.points:
                continue

            record = dict(zip(field_names, shape_record.record))
            match_key = build_match_key(
                first_present(record, "Schulname"),
                first_present(record, "KomName"),
                first_present(record, "Schulform"),
            )
            if not match_key:
                continue

            longitude, latitude = shape_record.shape.points[0]
            geodata = {
                "latitude": latitude,
                "longitude": longitude,
                "_geodata_category": "allgemein",
            }

            # Ambiguous keys are dropped entirely so we do not attach the
            # wrong point to an API school.
            if match_key in duplicate_keys:
                continue
            if match_key in self._local_geodata_index:
                duplicate_keys.add(match_key)
                self._local_geodata_index.pop(match_key, None)
                continue

            self._local_geodata_index[match_key] = geodata

        if duplicate_keys:
            self.logger.info(
                "Skipping %d duplicate Niedersachsen geodata keys", len(duplicate_keys)
            )

        self._local_geodata_enabled = True

    def _match_area_for_item(self, item: dict) -> str:
        ag = item.get("ag") or {}
        if (ag.get("sdb_kreis") or {}).get("kreis"):
            return ag["sdb_kreis"]["kreis"]
        if (item.get("kreis") or {}).get("kreis"):
            return item["kreis"]["kreis"]
        return ""

    def _match_key_for_item(self, item: dict) -> str:
        suffix = item.get("namensZusatz") or item.get("namenszusatz") or ""
        name = " ".join(part for part in [item.get("schulname", ""), suffix] if part).strip()
        form = (item.get("sdb_art") or {}).get("art") or ""
        return build_match_key(name, self._match_area_for_item(item), form)

    def _find_local_geodata(self, item: dict):
        if not getattr(self, "_local_geodata_enabled", False):
            return None

        match_key = self._match_key_for_item(item)
        if not match_key:
            return None

        return self._local_geodata_index.get(match_key)

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
            callback=self.parse_api_search,
        )

    def parse_api_search(self, response: Response):
        self._load_local_geodata_index()

        json_response = json.loads(response.body.decode("utf-8"))
        for school in json_response["props"]["schools"]:
            yield scrapy.Request(
                f"https://schulen.nibis.de/school/getInfo/{school.get('schulnr')}",
                callback=self.parse_details,
            )

    def parse_details(self, response: Response):
        try:
            item = json.loads(response.body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            self.logger.error("Could not parse Niedersachsen detail JSON from %s: %s", response.url, exc)
            return

        geodata = self._find_local_geodata(item)
        if geodata:
            item.update(geodata)
            item["_source"] = "api_geodata_exact"
        else:
            # Unmatched schools stay API-only; this POC never invents schools
            # or IDs from shapefile rows alone.
            item["_source"] = "api_only"

        yield item

    @staticmethod
    def normalize(item: Item) -> School:
        suffix = item.get("namensZusatz") or item.get("namenszusatz") or ""
        name = " ".join(part for part in [item.get("schulname", ""), suffix] if part).strip()

        address = item.get("hauptsitz") or item.get("sdb_adressen", [{}])[0]
        ort = address.get("sdb_ort", {})
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
