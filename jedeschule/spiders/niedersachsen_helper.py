"""Small NiBiS API helpers used by offline comparison tools.

The Niedersachsen spider itself uses Scrapy requests in
``niedersachsen.py``. These helpers are intentionally limited to retrieving
source records; coordinate matching and geocoding do not belong in the
production spider.
"""

import json
import urllib.parse

import requests


NIBIS_SEARCH_URL = "https://schulen.nibis.de/school/search"
NIBIS_DETAIL_URL = "https://schulen.nibis.de/school/getInfo/{schulnr}"
NIBIS_ADVANCED_URL = "https://schulen.nibis.de/search/advanced"
NI_LSCHB = [
    "RLSB Braunschweig",
    "RLSB Hannover",
    "RLSB Lüneburg",
    "RLSB Osnabrück",
]


def _nibis_session() -> tuple[requests.Session, str]:
    session = requests.Session()
    session.headers["User-Agent"] = "jedeschule-scraper-ni-tools/1.0"
    session.get(NIBIS_ADVANCED_URL, timeout=30).raise_for_status()
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
