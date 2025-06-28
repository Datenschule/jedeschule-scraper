import json
import logging

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