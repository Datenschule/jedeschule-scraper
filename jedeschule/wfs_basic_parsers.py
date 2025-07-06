import json

from scrapy.http import Response


def parse_geojson_features(response: Response):
    geojson = json.loads(response.text)

    for feature in geojson.get("features", []):
        properties = feature.get("properties", {})
        coords = feature.get("geometry", {}).get("coordinates", [])

        properties["lon"] = coords[0]
        properties["lat"] = coords[1]


        yield properties
