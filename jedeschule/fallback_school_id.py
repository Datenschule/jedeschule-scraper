"""
Deterministic fallback school ids when a publisher does not expose a stable code.

Used e.g. for Baden-Württemberg when DISCH cannot be read from the email domain:
WFS feature UUIDs can change when the provider re-imports data, so ids like
``BW-UUID-…`` create duplicate logical schools. A hash of coarse location +
normalized name + normalized school type stays stable across re-imports unless
the "core" of the record (name, type, or ~1 km cell) changes.
"""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata


def km_grid_indices(lat: float, lon: float) -> tuple[int, int]:
    """
    Approximate 1 km grid cell in Germany (WGS84).

    Uses local meters-per-degree (latitude-dependent for east-west).
    """
    m_per_deg_lat = 111_320.0
    m_per_deg_lon = 111_320.0 * math.cos(math.radians(lat))
    i_ns = round(lat * m_per_deg_lat / 1000.0)
    i_ew = round(lon * m_per_deg_lon / 1000.0)
    return (i_ns, i_ew)


def normalize_school_name_for_id(name: str | None) -> str:
    if not name:
        return ""
    n = unicodedata.normalize("NFKD", name)
    n = "".join(ch for ch in n if not unicodedata.combining(ch))
    n = n.casefold()
    n = re.sub(r"[^a-z0-9]+", " ", n)
    return re.sub(r"\s+", " ", n).strip()


def normalize_school_type_for_id(school_type: str | None) -> str:
    if not school_type:
        return ""
    s = school_type.strip().casefold()
    if "://" in s:
        s = s.rstrip("/").split("/")[-1]
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def normalize_address_for_id(address: str | None) -> str:
    if not address:
        return ""
    a = unicodedata.normalize("NFKD", address)
    a = "".join(ch for ch in a if not unicodedata.combining(ch))
    a = a.casefold()
    a = re.sub(r"[^a-z0-9]+", " ", a)
    return re.sub(r"\s+", " ", a).strip()


def normalize_zip_for_id(zip_code: str | None) -> str:
    if not zip_code:
        return ""
    z = zip_code.strip()
    return re.sub(r"[^0-9a-z]+", "", z.casefold())


def stable_fallback_id(
    state_prefix: str,
    lat: float,
    lon: float,
    name: str | None,
    school_type: str | None,
    *,
    digest_chars: int = 16,
) -> str:
    """
    Build ``{STATE}-FB-{hex}`` from 1 km grid + normalized name + type.

    ``state_prefix`` is two letters, e.g. ``BW`` (no ``DE-``).
    """
    st = state_prefix.strip().upper()
    if len(st) != 2:
        raise ValueError("state_prefix must be two letters")
    i_ns, i_ew = km_grid_indices(lat, lon)
    nn = normalize_school_name_for_id(name)
    nt = normalize_school_type_for_id(school_type)
    payload = f"{st}|{i_ns}|{i_ew}|{nn}|{nt}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:digest_chars]
    return f"{st}-FB-{digest}"


def stable_no_coord_fallback_id(
    state_prefix: str,
    name: str | None,
    school_type: str | None,
    address: str | None,
    zip_code: str | None,
    *,
    digest_chars: int = 16,
) -> str | None:
    """
    Build ``{STATE}-FBA-{hex}`` without coordinates from normalized name/type/address/zip.

    Returns ``None`` if the signal is too weak for a deterministic fallback.
    """
    st = state_prefix.strip().upper()
    if len(st) != 2:
        raise ValueError("state_prefix must be two letters")
    nn = normalize_school_name_for_id(name)
    nt = normalize_school_type_for_id(school_type)
    na = normalize_address_for_id(address)
    nz = normalize_zip_for_id(zip_code)

    # Guardrail: do not create no-coordinate deterministic ids from very weak data.
    if not nn:
        return None
    if not na and not nz:
        return None

    payload = f"{st}|NOC|{nn}|{nt}|{na}|{nz}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:digest_chars]
    return f"{st}-FBA-{digest}"


def baden_wuerttemberg_school_id(
    disch: str | None,
    lat: float | None,
    lon: float | None,
    name: str | None,
    school_type: str | None,
    address: str | None,
    zip_code: str | None,
    feature_uuid: str | None,
) -> str:
    """
    Preferred order:
    DISCH from email → deterministic FB hash (with coords) →
    deterministic FBA hash (no coords; address+zip) → WFS UUID.
    """
    if disch:
        return f"BW-{disch}"
    try:
        lat_f = float(lat) if lat is not None else None
        lon_f = float(lon) if lon is not None else None
    except (TypeError, ValueError):
        lat_f, lon_f = None, None
    if lat_f is not None and lon_f is not None:
        return stable_fallback_id("BW", lat_f, lon_f, name, school_type)
    no_coord_id = stable_no_coord_fallback_id("BW", name, school_type, address, zip_code)
    if no_coord_id:
        return no_coord_id
    if feature_uuid:
        return f"BW-UUID-{feature_uuid}"
    return "BW-FB-UNKNOWN"
