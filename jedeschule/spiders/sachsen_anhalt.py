# -*- coding: utf-8 -*-
import scrapy
from scrapy import Item
from pyproj import Transformer
from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class SachsenAnhaltSpider(SchoolSpider):
    name = "sachsen-anhalt"

    # ArcGIS FeatureServer API - contains 857 schools with coordinates
    # Note: This dataset excludes vocational schools (Berufsbildende Schulen)
    # but includes all primary, secondary, grammar, and special needs schools
    start_urls = [
        "https://services-eu1.arcgis.com/3jNCHSftk0N4t7dd/arcgis/rest/services/"
        "Schulenstandorte_EPSG25832_2024_25_Sicht/FeatureServer/44/query?"
        "where=1%3D1&outFields=*&f=json"
    ]

    def parse(self, response):
        """Parse ArcGIS FeatureServer JSON response"""
        data = response.json()

        # EPSG:25832 (UTM zone 32N) to EPSG:4326 (WGS84) transformer
        transformer = Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True)

        for feature in data.get("features", []):
            attrs = feature["attributes"]
            geom = feature.get("geometry", {})

            # Transform coordinates from EPSG:25832 to WGS84
            latitude = None
            longitude = None
            if geom and "x" in geom and "y" in geom:
                longitude, latitude = transformer.transform(geom["x"], geom["y"])

            # Extract school information from ArcGIS attributes
            yield {
                "name": attrs.get("Name"),
                "city": attrs.get("Ort"),
                "school_type": attrs.get("Schulform"),
                "category": attrs.get("Kategorie"),
                "provider": attrs.get("Traeg_Anw"),
                "latitude": latitude,
                "longitude": longitude,
                "object_id": attrs.get("OBJECTID"),
            }

    @staticmethod
    def normalize(item: Item) -> School:
        """Normalize ArcGIS data to School item"""
        # Generate ID from OBJECTID
        school_id = f"ST-ARC{item.get('object_id', 0):05d}"

        return School(
            name=item.get("name"),
            id=school_id,
            city=item.get("city"),
            school_type=item.get("school_type"),
            legal_status=item.get("category"),
            provider=item.get("provider"),
            latitude=item.get("latitude"),
            longitude=item.get("longitude"),
        )
