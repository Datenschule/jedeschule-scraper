import json
import urllib
import os
import re
import zipfile
import io
import hashlib
import unicodedata
from collections import defaultdict

import scrapy
import shapefile
from scrapy import Item
from scrapy.http import Response
from pyproj import CRS, Transformer

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


# School form abbreviation mappings
FORM_ABBREV = {
    "gs": "grundschule",
    "ghs": "grund und hauptschule",
    "hs": "hauptschule",
    "rs": "realschule",
    "obs": "oberschule",
    "igs": "integrierte gesamtschule",
    "kgs": "kooperative gesamtschule",
    "gym": "gymnasium",
    "fos": "fachoberschule",
    "bos": "berufsoberschule",
    "bbs": "berufsbildende schule",
    "bfs": "berufsfachschule",
}

# Tokens to remove (fluff)
FLUFF_TOKENS = {
    "ev",
    "evang",
    "evangelisch",
    "evangelische",
    "kath",
    "katholisch",
    "katholische",
    "städt",
    "städtisch",
    "städtische",
    "staatl",
    "staatliche",
    "privat",
    "private",
    "ggmbh",
    "gemeinnützige",
}

# Compile regex for word-boundary form removal
FORM_WORDS_RE = re.compile(
    r"\b(" + "|".join(map(re.escape, FORM_ABBREV.values())) + r")\b"
)


def _strip_diacritics(s: str) -> str:
    """Remove diacritics using Unicode NFKD normalization"""
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch)
    )


def normalize_german_chars(text: str) -> str:
    """Unicode-aware normalization with German-specific rules"""
    # First apply NFKD normalization
    text = _strip_diacritics(text)
    # Then apply German digraph rules
    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
        "Ä": "Ae",
        "Ö": "Oe",
        "Ü": "Ue",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def normalize_name(name: str, remove_form: bool = False) -> str:
    if not name:
        return ""

    name = name.lower().strip()
    name = normalize_german_chars(name)
    name = re.sub(r"[.,;:()\[\]]", "", name)
    name = name.replace("-", " ")
    name = re.sub(r"\s+", " ", name)

    tokens = name.split()
    tokens = [t for t in tokens if t not in FLUFF_TOKENS]

    expanded_tokens = []
    for token in tokens:
        if token in FORM_ABBREV:
            expanded_tokens.append(FORM_ABBREV[token])
        else:
            expanded_tokens.append(token)

    name = " ".join(expanded_tokens).strip()

    if remove_form:
        # Use word boundaries to avoid removing substrings
        name = FORM_WORDS_RE.sub(" ", name)
        name = re.sub(r"\s+", " ", name).strip()

    return name


def normalize_city(city: str) -> str:
    if not city:
        return ""

    city = city.lower().strip()
    city = normalize_german_chars(city)

    municipal_prefixes = {"stadt", "gemeinde", "samtgemeinde", "flecken"}
    tokens = city.split()
    if tokens and tokens[0] in municipal_prefixes:
        tokens = tokens[1:]

    return " ".join(tokens).strip()


def normalize_school_form(form: str) -> str:
    if not form:
        return ""

    f = form.lower().strip()

    # Check exact abbreviation match
    if f in FORM_ABBREV:
        return FORM_ABBREV[f]

    # Check for abbreviations within longer strings (word boundaries)
    for abbrev, full in FORM_ABBREV.items():
        if re.search(rf"\b{re.escape(abbrev)}\b", f):
            return full

    # Normalize common long form variations
    f = f.replace("berufsbildende schulen", "berufsbildende schule")
    f = f.replace("berufliche schulen", "berufsbildende schule")

    return f


def build_match_key(name: str, city: str, form: str = "", loose: bool = False) -> str:
    norm_name = normalize_name(name, remove_form=loose)
    norm_city = normalize_city(city)
    norm_form = normalize_school_form(form) if not loose else ""

    parts = [p for p in [norm_name, norm_city, norm_form] if p]
    return "|".join(parts)


def _first_present(d: dict, *keys):
    """Return first non-empty value from dict for given keys"""
    for k in keys:
        if k in d and d[k]:
            return d[k]
    return ""


class NiedersachsenSpider(SchoolSpider):
    name = "niedersachsen"
    start_urls = ["https://schulen.nibis.de/search/advanced"]
    allowed_domains = ["schulen.nibis.de", "statistik.niedersachsen.de"]

    SHAPEFILE_BASE = os.path.join(
        os.path.dirname(__file__), "..", "..", "cache", "niedersachsen_shapefiles"
    )
    SHAPEFILE_PATHS = {
        "allgemein": os.path.join(SHAPEFILE_BASE, "ABS_Shape2024"),
        "foerder": os.path.join(SHAPEFILE_BASE, "Foerder2024"),
        "berufs": os.path.join(SHAPEFILE_BASE, "BBS2024"),
        "gesundheit": os.path.join(SHAPEFILE_BASE, "SdG2024"),
    }

    SHAPEFILE_URLS = {
        "allgemein": "https://www.statistik.niedersachsen.de/download/194517",
        "foerder": "https://www.statistik.niedersachsen.de/download/194518",
        "berufs": "https://www.statistik.niedersachsen.de/download/194519",
        "gesundheit": "https://www.statistik.niedersachsen.de/download/194520",
    }

    def _detect_dbf_encoding(self, shp_path: str, default="utf-8"):
        """Detect encoding from .cpg file or fallback"""
        cpg = shp_path + ".cpg"
        if os.path.exists(cpg):
            try:
                with open(cpg, "r", encoding="ascii", errors="ignore") as f:
                    enc = f.read().strip() or default
                    return enc.lower()
            except Exception:
                pass
        return default

    def _make_transformer(self, shp_path: str):
        """Create CRS transformer if shapefile is not WGS84"""
        prj = shp_path + ".prj"
        if not os.path.exists(prj):
            return None

        try:
            with open(prj, "r", encoding="utf-8", errors="ignore") as f:
                crs_src = CRS.from_wkt(f.read())
            crs_dst = CRS.from_epsg(4326)
            if crs_src.to_epsg() == 4326:
                return None
            return Transformer.from_crs(crs_src, crs_dst, always_xy=True)
        except Exception:
            return None

    def _safe_extract(self, zf: zipfile.ZipFile, dest: str):
        """Safely extract ZIP avoiding path traversal"""
        dest_real = os.path.realpath(dest)
        for m in zf.infolist():
            target_path = os.path.realpath(os.path.join(dest, m.filename))
            if not target_path.startswith(dest_real + os.sep):
                raise RuntimeError(f"Blocked unsafe path in ZIP: {m.filename}")
        zf.extractall(dest)

    def _download_shapefile(self, response):
        """Callback to handle shapefile ZIP download (async via Scrapy)"""
        category = response.meta["category"]

        try:
            with zipfile.ZipFile(io.BytesIO(response.body)) as zf:
                self._safe_extract(zf, self.SHAPEFILE_BASE)

            self.logger.info(f"Downloaded and extracted {category} shapefile")
        except Exception as e:
            self.logger.error(f"Failed to extract {category} shapefile: {e}")

    def _queue_shapefile_downloads(self):
        """Queue shapefile downloads using Scrapy Requests (non-blocking)"""
        os.makedirs(self.SHAPEFILE_BASE, exist_ok=True)

        requests_to_queue = []
        for category, url in self.SHAPEFILE_URLS.items():
            shapefile_path = self.SHAPEFILE_PATHS[category] + ".shp"

            if os.path.exists(shapefile_path):
                self.logger.info(f"Shapefile {category} already exists, skipping download")
                continue

            self.logger.info(f"Queueing {category} shapefile download from {url}")
            requests_to_queue.append(
                scrapy.Request(
                    url,
                    callback=self._download_shapefile,
                    meta={"category": category},
                    priority=100,  # High priority to download before school requests
                    dont_filter=True
                )
            )

        return requests_to_queue

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
        json_response = json.loads(response.body.decode("utf-8"))
        api_schools = json_response["props"]["schools"]

        # Build API index with collision handling
        api_index = defaultdict(list)
        for school in api_schools:
            # Fixed typo: namenszusatz not namenszuatz
            name = " ".join(
                [school.get("schulname", ""), school.get("namenszusatz", "")]
            ).strip()
            city = school.get("ort", "")
            form = school.get("schulform", "")
            schulnr = school.get("schulnr")

            if not schulnr:
                continue

            key_full = build_match_key(name, city, form, loose=False)
            key_loose = build_match_key(name, city, loose=True)

            api_data = {
                "schulnr": schulnr,
                "name": name,
                "city": city,
                "form": form,
            }

            api_index[key_full].append(api_data)
            api_index[key_loose].append(api_data)

        self.logger.info(
            f"Built API index with {len(api_schools)} schools ({len(api_index)} keys)"
        )

        # Track metrics
        self.crawler.stats.set_value("ni/api_schools_total", len(api_schools))
        self.crawler.stats.set_value("ni/api_index_keys", len(api_index))

        # Queue shapefile downloads asynchronously (non-blocking)
        for req in self._queue_shapefile_downloads():
            yield req

        # Check if all shapefiles are available
        if not all(os.path.exists(p + ".shp") for p in self.SHAPEFILE_PATHS.values()):
            self.logger.warning("Shapefiles not found, falling back to API-only mode")
            for school_data in api_schools:
                yield scrapy.Request(
                    f"https://schulen.nibis.de/school/getInfo/{school_data.get('schulnr')}",
                    callback=self.parse_details,
                )
            return

        matched_count = 0
        unmatched_count = 0
        matched_schulnr = set()

        for category, path in self.SHAPEFILE_PATHS.items():
            try:
                enc = self._detect_dbf_encoding(path, default="iso-8859-1")
                sf = shapefile.Reader(path, encoding=enc)
                field_names = [f[0] for f in sf.fields[1:]]
                transformer = self._make_transformer(path)

                for rec in sf.iterShapeRecords():
                    # Handle non-point shapes
                    if rec.shape.shapeType not in (
                        shapefile.POINT,
                        shapefile.POINTZ,
                        shapefile.POINTM,
                    ):
                        if not rec.shape.points:
                            continue

                    data = dict(zip(field_names, rec.record))
                    coords = rec.shape.points[0] if rec.shape.points else None

                    if not coords:
                        continue

                    # CRS-aware coordinate transformation
                    x, y = coords
                    if transformer:
                        lon, lat = transformer.transform(x, y)
                    else:
                        lon, lat = x, y

                    # Field name portability
                    shp_name = _first_present(data, "Schulname", "Name")
                    shp_city = _first_present(
                        data, "KomName", "GemName", "Gemeinde", "Ort", "Stadt"
                    )
                    shp_form = _first_present(data, "Schulform", "Typ", "Art")

                    if not shp_name or not shp_city:
                        continue

                    key_full = build_match_key(shp_name, shp_city, shp_form, loose=False)
                    key_loose = build_match_key(shp_name, shp_city, loose=True)

                    candidates = api_index.get(key_full) or api_index.get(key_loose) or []
                    api_data = None

                    if candidates:
                        # Prefer same form, otherwise first
                        norm_shp_form = normalize_school_form(shp_form)
                        api_data = next(
                            (
                                c
                                for c in candidates
                                if normalize_school_form(c["form"]) == norm_shp_form
                            ),
                            candidates[0],
                        )

                    shapefile_data = {
                        "shapefile_name": shp_name,
                        "shapefile_city": shp_city,
                        "shapefile_form": shp_form,
                        "shapefile_category": category,
                        "latitude": lat,
                        "longitude": lon,
                    }

                    if api_data:
                        matched_count += 1
                        matched_schulnr.add(api_data["schulnr"])
                        yield scrapy.Request(
                            f"https://schulen.nibis.de/school/getInfo/{api_data['schulnr']}",
                            callback=self.parse_details,
                            meta={"shapefile_data": shapefile_data},
                        )
                    else:
                        unmatched_count += 1
                        yield self._create_shapefile_only_school(shapefile_data)

            except Exception as e:
                self.logger.error(f"Error processing shapefile {category}: {e}")

        # Fetch unmatched API-only schools
        for school in api_schools:
            if school.get("schulnr") not in matched_schulnr:
                yield scrapy.Request(
                    f"https://schulen.nibis.de/school/getInfo/{school['schulnr']}",
                    callback=self.parse_details,
                    meta={"shapefile_data": None},
                )

        self.logger.info(
            f"Shapefile processing complete: {matched_count} matched, {unmatched_count} shapefile-only"
        )

    def _synthetic_id(self, shp_data):
        """Generate stable synthetic ID using hash"""
        raw = f"{shp_data['shapefile_name']}|{shp_data['shapefile_city']}|{shp_data['latitude']:.6f}|{shp_data['longitude']:.6f}"
        h = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]
        return f"NI-SHP-{h}"

    def _create_shapefile_only_school(self, shp_data):
        synthetic_id = self._synthetic_id(shp_data)

        return {
            "schulnr": synthetic_id,
            "schulname": shp_data["shapefile_name"],
            "namenszusatz": "",
            "sdb_adressen": [
                {
                    "strasse": None,
                    "sdb_ort": {
                        "plz": None,
                        "ort": shp_data["shapefile_city"],
                    },
                }
            ],
            "sdb_art": {"art": shp_data["shapefile_form"]},
            "sdb_traeger": {"name": None},
            "sdb_traegerschaft": {"bezeichnung": None},
            "telefon": None,
            "fax": None,
            "email": None,
            "homepage": None,
            "latitude": shp_data["latitude"],
            "longitude": shp_data["longitude"],
            "_source": "shapefile_only",
            "_shapefile_category": shp_data["shapefile_category"],
        }

    def parse_details(self, response: Response):
        try:
            data = json.loads(response.text)
        except Exception as e:
            self.logger.error(f"JSON parse error for {response.url}: {e}")
            return

        shp = response.meta.get("shapefile_data")
        if shp:
            data.update(
                {
                    "latitude": shp["latitude"],
                    "longitude": shp["longitude"],
                    "_source": "api_enriched",
                    "_shapefile_category": shp["shapefile_category"],
                }
            )
        else:
            data["_source"] = "api_only"

        yield data

    @staticmethod
    def _get(dict_like, key, default):
        return dict_like.get(key) or default

    @staticmethod
    def normalize(item: Item) -> School:
        # Fixed typo: namenszusatz not namenszuatz
        name = " ".join(
            [item.get("schulname", ""), item.get("namenszusatz", "")]
        ).strip()
        address = item.get("sdb_adressen", [{}])[0]
        ort = address.get("sdb_ort", {})
        school_type = NiedersachsenSpider._get(item, "sdb_art", {}).get("art")
        provider = NiedersachsenSpider._get(item, "sdb_traeger", {}).get("name")

        schulnr = item.get("schulnr", "")
        if isinstance(schulnr, str) and schulnr.startswith("NI-"):
            school_id = schulnr
        else:
            school_id = f"NI-{schulnr}"

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
            id=school_id,
        )
