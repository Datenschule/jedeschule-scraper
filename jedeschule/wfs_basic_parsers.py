import json

from scrapy.http import Response


def parse_geojson_features(response: Response):
    geojson = json.loads(response.text)

    for feature in geojson.get("features", []):
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        coords = geometry.get("coordinates", [])

        lon = lat = None

        if geometry.get("type") == "Point" and len(coords) >= 2:
            lon, lat = coords[0], coords[1]
        elif geometry.get("type") == "MultiPoint" and len(coords) > 0:
            first_point = coords[0]
            if len(first_point) >= 2:
                lon, lat = first_point[0], first_point[1]

        properties["lon"] = lon
        properties["lat"] = lat

        yield properties
