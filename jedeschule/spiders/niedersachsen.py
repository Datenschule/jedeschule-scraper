import json
import urllib
from pathlib import Path

import scrapy
from scrapy import Item
from scrapy.http import Response

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


NLS_CACHE = Path("cache/niedersachsen_nls_coords.jsonl")


class NiedersachsenSpider(SchoolSpider):
    name = "niedersachsen"
    allowed_domains = ["schulen.nibis.de"]
    start_urls = ["https://schulen.nibis.de/search/advanced"]

    def _load_coords(self) -> None:
        if getattr(self, "_coords_loaded", False):
            return
        self._coords_loaded = True
        self._coords: dict[str, tuple[float, float]] = {}

        if not NLS_CACHE.exists():
            self.logger.warning(
                "official Niedersachsen coords cache missing at %s; running API-only. "
                "Generate it via `niedersachsen_helper.geocode_all_schools()` and "
                "`niedersachsen_helper.build_official_coords_cache()`.",
                NLS_CACHE,
            )
            return

        with NLS_CACHE.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if not str(rec.get("status", "")).startswith("matched_"):
                    continue
                schulnr = rec.get("schulnr")
                if schulnr is None or "latitude" not in rec or "longitude" not in rec:
                    continue
                self._coords[str(schulnr)] = (rec["latitude"], rec["longitude"])
        self.logger.info("Loaded %d Schulnummer -> coord entries", len(self._coords))

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
        self._load_coords()

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

        coord = getattr(self, "_coords", {}).get(str(item.get("schulnr")))
        if coord is not None:
            item["latitude"], item["longitude"] = coord

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
