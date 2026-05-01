"""Build the Niedersachsen coordinate caches.

The final coordinates written by the spider are official NLS shapefile points.
Photon is used only as a bridge:

1. Geocode every NiBiS school address into ``niedersachsen_nibis_geocoded.jsonl``
2. Match those geocoded points against the official NLS shapefiles
3. Write only the successful official matches into
   ``niedersachsen_nls_coords.jsonl``

Usage:

    from jedeschule.spiders.niedersachsen_helper import (
        geocode_all_schools,
        build_official_coords_cache,
    )

    geocode_all_schools()
    build_official_coords_cache()
"""

import json
import io
import math
import re
import time
import unicodedata
import urllib.parse
import zipfile
from collections import defaultdict
from pathlib import Path

import requests
import shapefile


NIBIS_SEARCH_URL = "https://schulen.nibis.de/school/search"
NIBIS_DETAIL_URL = "https://schulen.nibis.de/school/getInfo/{schulnr}"
NIBIS_ADVANCED_URL = "https://schulen.nibis.de/search/advanced"
PHOTON_URL = "https://photon.komoot.io/api"
USER_AGENT = "jedeschule-scraper-ni-helper/0.1"

GEOCODE_CACHE = Path("cache/niedersachsen_nibis_geocoded.jsonl")
NLS_CACHE = Path("cache/niedersachsen_nls_coords.jsonl")
SHAPEFILE_DIR = Path("cache/niedersachsen_shapefiles")

NI_LSCHB = ["RLSB Braunschweig", "RLSB Hannover", "RLSB Lüneburg", "RLSB Osnabrück"]

SHAPEFILE_DOWNLOADS = {
    "ABS_Shape2024": "https://www.statistik.niedersachsen.de/download/167954",
    "BBS2024": "https://www.statistik.niedersachsen.de/download/169459",
    "Foerder2024": "https://www.statistik.niedersachsen.de/download/167953",
    "SdG2024": "https://www.statistik.niedersachsen.de/download/167952",
}

SHAPEFILE_NAME_FIELDS = {
    "ABS_Shape2024": "Schulname",
    "BBS2024": "Name",
    "Foerder2024": "Schulname",
    "SdG2024": "Name",
}

# 0.01-degree cells are much larger than the 100-150 m match radii, so scanning
# the 3x3 neighboring cells comfortably covers every candidate we could accept.
GRID_CELL_DEGREES = 0.01
MATCH_DISTANCE_METERS = 100.0
NAME_MATCH_DISTANCE_METERS = 150.0
NAME_DROP_TOKENS = {
    "am",
    "an",
    "bbs",
    "berufsbildende",
    "das",
    "der",
    "des",
    "die",
    "foerderzentrum",
    "foerderschule",
    "fuer",
    "fur",
    "gesamtschule",
    "grundschule",
    "gymnasium",
    "hauptschule",
    "igs",
    "im",
    "in",
    "integrierte",
    "kgs",
    "kooperative",
    "obs",
    "oberschule",
    "realschule",
    "rs",
    "schule",
    "schulzentrum",
    "studienseminar",
    "und",
}


def _append(path: Path, rec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _seen(path: Path, key_fn) -> set:
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8") as fh:
        return {key_fn(json.loads(line)) for line in fh if line.strip()}


def _nibis_session() -> tuple[requests.Session, str]:
    session = requests.Session()
    session.headers["User-Agent"] = "jedeschule (+http://jedeschule.codefor.de/docs)"
    session.get(NIBIS_ADVANCED_URL, timeout=30)
    xsrf = urllib.parse.unquote(session.cookies.get("XSRF-TOKEN") or "")
    return session, xsrf


def _nibis_school_list(session: requests.Session, xsrf: str) -> list[dict]:
    body = {
        "type": "Advanced",
        "eingabe": None,
        "filters": {
            "classifications": [],
            "lschb": NI_LSCHB,
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
    response = session.post(
        NIBIS_SEARCH_URL,
        headers={
            "X-XSRF-TOKEN": xsrf,
            "X-Inertia": "true",
            "X-Inertia-Version": "207fd484b7c2ceeff7800b8c8a11b3b6",
            "Content-Type": "application/json;charset=utf-8",
            "Accept": "text/html, application/xhtml+xml",
            "Origin": "https://schulen.nibis.de",
            "Referer": NIBIS_ADVANCED_URL,
            "X-Requested-With": "XMLHttpRequest",
        },
        data=json.dumps(body),
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["props"]["schools"]


def _nibis_detail(session: requests.Session, schulnr: int) -> dict:
    response = session.get(NIBIS_DETAIL_URL.format(schulnr=schulnr), timeout=60)
    response.raise_for_status()
    return response.json()


def _photon_forward(
    session: requests.Session, query: str, *, only_school: bool = True
) -> list[dict]:
    params = {"q": query, "limit": 1, "lang": "de"}
    if only_school:
        params["osm_tag"] = "amenity:school"
    response = session.get(PHOTON_URL, params=params, timeout=20)
    response.raise_for_status()
    return (response.json() or {}).get("features") or []


def _school_address(detail: dict) -> str | None:
    addr = detail.get("hauptsitz") or (detail.get("sdb_adressen") or [{}])[0]
    ort = addr.get("sdb_ort") or {}
    parts = [
        addr.get("strasse"),
        str(ort.get("plz")) if ort.get("plz") else None,
        ort.get("ort"),
    ]
    return " ".join(part for part in parts if part) or None


def _school_name(detail: dict) -> str:
    suffix = detail.get("namensZusatz") or detail.get("namenszusatz") or ""
    return " ".join(part for part in [detail.get("schulname", ""), suffix] if part).strip()


def _normalize_name(text: str) -> str:
    text = (text or "").lower().strip().replace("ß", "ss")
    text = "".join(
        char
        for char in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(char)
    )
    text = re.sub(r"[^a-z0-9]+", " ", text)
    tokens = [token for token in text.split() if token not in NAME_DROP_TOKENS]
    return " ".join(tokens)


def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6_371_000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(a))


def _download_shapefiles(shape_dir: Path = SHAPEFILE_DIR) -> None:
    shape_dir.mkdir(parents=True, exist_ok=True)

    for stem, url in SHAPEFILE_DOWNLOADS.items():
        if all((shape_dir / f"{stem}{suffix}").exists() for suffix in (".shp", ".shx", ".dbf")):
            continue

        response = requests.get(url, timeout=120)
        response.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            for member in archive.namelist():
                if not member.lower().endswith((".shp", ".shx", ".dbf", ".prj", ".cpg")):
                    continue
                target = shape_dir / Path(member).name
                with archive.open(member) as src, target.open("wb") as dst:
                    dst.write(src.read())


def _load_official_points(shape_dir: Path = SHAPEFILE_DIR) -> list[dict]:
    _download_shapefiles(shape_dir)

    grouped: dict[tuple[float, float], dict] = {}
    for stem, name_field in SHAPEFILE_NAME_FIELDS.items():
        reader = shapefile.Reader(str(shape_dir / stem), encoding="iso-8859-1")
        fields = [field[0] for field in reader.fields[1:]]
        for shape_record in reader.iterShapeRecords():
            if not shape_record.shape.points:
                continue
            record = dict(zip(fields, shape_record.record))
            lon, lat = shape_record.shape.points[0]
            key = (round(lat, 7), round(lon, 7))
            point = grouped.setdefault(
                key,
                {"latitude": lat, "longitude": lon, "names": set(), "sources": set()},
            )
            point["names"].add(_normalize_name(record.get(name_field) or ""))
            point["sources"].add(stem)

    return [
        {
            "latitude": point["latitude"],
            "longitude": point["longitude"],
            "names": point["names"],
            "sources": sorted(point["sources"]),
        }
        for point in grouped.values()
    ]


def _build_grid(points: list[dict]) -> dict[tuple[int, int], list[dict]]:
    grid: dict[tuple[int, int], list[dict]] = defaultdict(list)
    for point in points:
        key = (
            round(point["latitude"] / GRID_CELL_DEGREES),
            round(point["longitude"] / GRID_CELL_DEGREES),
        )
        grid[key].append(point)
    return grid


def _nearby_points(grid: dict[tuple[int, int], list[dict]], lat: float, lon: float) -> list[dict]:
    center = (round(lat / GRID_CELL_DEGREES), round(lon / GRID_CELL_DEGREES))
    candidates: list[dict] = []
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            candidates.extend(grid.get((center[0] + dy, center[1] + dx), []))
    return candidates


def geocode_all_schools(output: Path = GEOCODE_CACHE, *, photon_delay: float = 0.2) -> dict:
    """Forward-geocode every NiBiS school address with Photon, write JSONL."""
    seen = _seen(output, lambda record: int(record["schulnr"]))
    nibis, xsrf = _nibis_session()
    schools = _nibis_school_list(nibis, xsrf)

    photon = requests.Session()
    photon.headers["User-Agent"] = USER_AGENT
    resolved = skipped = 0

    for school in schools:
        schulnr = int(school["schulnr"])
        if schulnr in seen:
            skipped += 1
            continue

        detail = _nibis_detail(nibis, schulnr)
        query = _school_address(detail)
        record = {
            "schulnr": schulnr,
            "name": _school_name(detail),
            "query": query,
            "status": "missing_address",
        }

        if query:
            try:
                features = _photon_forward(photon, query, only_school=True) or _photon_forward(
                    photon, query, only_school=False
                )
            except (requests.RequestException, ValueError) as exc:
                record.update({"status": "geocoder_error", "error": str(exc)})
            else:
                if features:
                    coords = (features[0].get("geometry") or {}).get("coordinates") or []
                    if len(coords) == 2:
                        record.update(
                            {
                                "status": "ok",
                                "longitude": coords[0],
                                "latitude": coords[1],
                                "raw": features[0].get("properties") or {},
                            }
                        )
                        resolved += 1
                    else:
                        record["status"] = "no_geometry"
                else:
                    record["status"] = "not_found"

        _append(output, record)
        seen.add(schulnr)
        time.sleep(photon_delay)

    return {
        "considered": len(schools),
        "resolved": resolved,
        "skipped": skipped,
        "output": str(output),
    }


def build_official_coords_cache(
    output: Path = NLS_CACHE,
    geocode_cache: Path = GEOCODE_CACHE,
    shape_dir: Path = SHAPEFILE_DIR,
) -> dict:
    """Match geocoded NiBiS schools to official NLS points, write only official coords."""
    if not geocode_cache.exists():
        raise FileNotFoundError(
            f"Missing geocode cache at {geocode_cache}. Run geocode_all_schools() first."
        )

    points = _load_official_points(shape_dir)
    grid = _build_grid(points)
    seen = _seen(output, lambda record: int(record["schulnr"]))

    matched = skipped = no_nearby = ambiguous = 0
    with geocode_cache.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("status") != "ok":
                continue

            schulnr = int(record["schulnr"])
            if schulnr in seen:
                skipped += 1
                continue

            lat = float(record["latitude"])
            lon = float(record["longitude"])
            nearby = []
            for point in _nearby_points(grid, lat, lon):
                distance = _haversine_meters(
                    lat, lon, point["latitude"], point["longitude"]
                )
                if distance <= MATCH_DISTANCE_METERS:
                    nearby.append({**point, "distance_meters": distance})

            normalized_name = _normalize_name(record.get("name") or "")

            if len(nearby) == 1:
                match = nearby[0]
                status = "matched_by_distance"
            elif len(nearby) > 1:
                named = [
                    point
                    for point in nearby
                    if normalized_name and normalized_name in point["names"]
                ]
                if len(named) == 1:
                    match = named[0]
                    status = "matched_by_distance_and_name"
                else:
                    match = None
                    status = "ambiguous_nearby_points"
            else:
                match = None
                status = "no_official_point_within_radius"

            if match is None and normalized_name:
                named_nearby = []
                for point in _nearby_points(grid, lat, lon):
                    distance = _haversine_meters(
                        lat, lon, point["latitude"], point["longitude"]
                    )
                    if (
                        distance <= NAME_MATCH_DISTANCE_METERS
                        and normalized_name in point["names"]
                    ):
                        named_nearby.append({**point, "distance_meters": distance})
                if len(named_nearby) == 1:
                    match = named_nearby[0]
                    status = "matched_by_name_within_radius"

            if match is None:
                if status == "ambiguous_nearby_points":
                    ambiguous += 1
                else:
                    no_nearby += 1
                continue

            _append(
                output,
                {
                    "schulnr": schulnr,
                    "latitude": match["latitude"],
                    "longitude": match["longitude"],
                    "status": status,
                    "distance_meters": round(match["distance_meters"], 2),
                    "name": record.get("name"),
                    "sources": match["sources"],
                },
            )
            seen.add(schulnr)
            matched += 1

    return {
        "matched": matched,
        "skipped": skipped,
        "no_nearby": no_nearby,
        "ambiguous": ambiguous,
        "output": str(output),
    }
