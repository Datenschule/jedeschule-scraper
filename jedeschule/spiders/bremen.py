# -*- coding: utf-8 -*-
import os
import hashlib
import zipfile
import shapefile
import scrapy
from scrapy import Item
from pyproj import Transformer

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class BremenSpider(SchoolSpider):
    name = "bremen"

    # INSPIRE Download Service - Schulstandorte (Schools) for Bremen and Bremerhaven
    # ZIP contains two shapefiles: gdi_schulen_hb.shp (Bremen) and gdi_schulen_bhv.shp (Bremerhaven)
    ZIP_URL = "https://gdi2.geo.bremen.de/inspire/download/Schulstandorte/data/Schulstandorte_HB_BHV.zip"
    CACHE_DIR = "cache"
    CACHE_FILE = "cache/Schulstandorte_HB_BHV.zip"

    # Required for Scrapy - we'll download the ZIP in parse()
    start_urls = [ZIP_URL]

    def parse(self, response):
        """Download ZIP file with caching and read both shapefiles"""
        # Create cache directory
        os.makedirs(self.CACHE_DIR, exist_ok=True)

        # Download ZIP with SHA256 verification
        hash_obj = hashlib.sha256()
        with open(self.CACHE_FILE, "wb") as f:
            f.write(response.body)
            hash_obj.update(response.body)

        self.logger.info(f"Downloaded ZIP with SHA256: {hash_obj.hexdigest()}")

        # Extract shapefiles
        with zipfile.ZipFile(self.CACHE_FILE, 'r') as z:
            z.extractall(self.CACHE_DIR)

        # EPSG:25832 (UTM zone 32N) to EPSG:4326 (WGS84) transformer
        transformer = Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True)

        # Read both shapefiles
        shapefiles = [
            (f"{self.CACHE_DIR}/gdi_schulen_hb.shp", "Bremen"),
            (f"{self.CACHE_DIR}/gdi_schulen_bhv.shp", "Bremerhaven")
        ]

        for shapefile_path, city_name in shapefiles:
            sf = shapefile.Reader(shapefile_path)
            self.logger.info(f"Reading {len(sf.shapes())} schools from {city_name}")

            for shape, record in zip(sf.shapes(), sf.records()):
                rec = record.as_dict()

                # Transform coordinates from EPSG:25832 to WGS84
                latitude = None
                longitude = None
                if shape.points:
                    x, y = shape.points[0]
                    longitude, latitude = transformer.transform(x, y)

                # Use snr_txt (zero-padded 3-digit Schulnummer) as official ID
                snr_txt = rec.get("snr_txt")
                if not snr_txt or len(snr_txt) != 3 or not snr_txt.isdigit():
                    self.logger.warning(f"Invalid SNR format: {snr_txt} for {rec.get('nam')}")
                    continue

                yield {
                    "snr": snr_txt,
                    "name": rec.get("nam"),
                    "address": rec.get("strasse"),
                    "zip": rec.get("plz"),
                    "city": rec.get("ort"),
                    "district": rec.get("ortsteilna"),
                    "school_type": rec.get("schulart_2"),
                    "provider": rec.get("traegernam"),
                    "latitude": latitude,
                    "longitude": longitude,
                }

    @staticmethod
    def normalize(item: Item) -> School:
        """Normalize shapefile data to School item"""
        # Use SNR (Schulnummer) as stable ID - zero-padded 3-digit format (e.g., "002", "117")
        school_id = f"HB-{item.get('snr')}"

        return School(
            name=item.get("name"),
            id=school_id,
            address=item.get("address"),
            zip=item.get("zip"),
            city=item.get("city"),
            school_type=item.get("school_type"),
            provider=item.get("provider"),
            latitude=item.get("latitude"),
            longitude=item.get("longitude"),
        )
