import json
import logging
from io import BytesIO
import xmltodict
from typing import Generator

from lxml import etree
from scrapy.http import Response


def parse_geojson_features(response: Response):
    geojson = json.loads(response.text)

    for feature in geojson.get("features", []):
        properties = feature.get("properties", {})
        coords = feature.get("geometry", {}).get("coordinates", [])

        try:
            properties["lon"] = coords[0]
            properties["lat"] = coords[1]
        except (TypeError, IndexError):
            logging.warning("Skipping feature with invalid geometry")

        yield properties


def parse_gml_features(response_body: bytes, geom_tag: str = "the_geom",
                       pos_path=("gml:Point", "gml:pos"), swap_latlon=False) -> Generator[dict, None, None]:
    doc = xmltodict.parse(response_body)
    features = doc.get("wfs:FeatureCollection", {}).get("gml:featureMember", [])

    if isinstance(features, dict):  # Only one feature
        features = [features]

    for feature in features:
        data = {}
        feature_data = next(iter(feature.values()))  # e.g. de.hh.up:nicht_staatliche_schulen

        for tag, value in feature_data.items():
            clean_tag = tag.split(":")[-1]  # strip namespace

            if clean_tag == geom_tag:
                for key in pos_path:
                    value = value.get(key)
                    if value is None:
                        break
                if value:
                    coords = value.split()
                    if swap_latlon:
                        lat, lon = coords
                    else:
                        lon, lat = coords
                    data["lat"] = lat
                    data["lon"] = lon
            else:
                if isinstance(value, dict):
                    value = value.get("#text", "")
                data[clean_tag] = value

        yield data
