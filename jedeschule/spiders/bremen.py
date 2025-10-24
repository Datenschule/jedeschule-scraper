# -*- coding: utf-8 -*-
import io
import os
import re
import hashlib
import zipfile
import scrapy
from scrapy import Item
import shapefile
from pyproj import Transformer

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class BremenSpider(SchoolSpider):
    name = "bremen"
    ZIP_URL = "https://gdi2.geo.bremen.de/inspire/download/Schulstandorte/data/Schulstandorte_HB_BHV.zip"
    CACHE_DIR = "cache"
    CACHE_FILE = os.path.join(CACHE_DIR, "Schulstandorte_HB_BHV.zip")

    start_urls = [ZIP_URL]

    def parse(self, response):
        os.makedirs(self.CACHE_DIR, exist_ok=True)

        # Save ZIP and compute checksum
        sha256 = hashlib.sha256(response.body).hexdigest()
        with open(self.CACHE_FILE, "wb") as f:
            f.write(response.body)
        self.logger.info(f"Downloaded ZIP SHA256={sha256}")

        # CRS: EPSG:25832 → EPSG:4326
        transformer = Transformer.from_crs(25832, 4326, always_xy=True)

        # Read both shapefiles directly from ZIP (no extractall)
        with zipfile.ZipFile(io.BytesIO(response.body), "r") as zf:
            for stem, city_name in (("gdi_schulen_hb", "Bremen"),
                                    ("gdi_schulen_bhv", "Bremerhaven")):
                shp_bytes = io.BytesIO(zf.read(f"{stem}.shp"))
                shx_bytes = io.BytesIO(zf.read(f"{stem}.shx"))
                dbf_bytes = io.BytesIO(zf.read(f"{stem}.dbf"))

                # Detect encoding from .cpg if present
                encoding = None
                try:
                    cpg = zf.read(f"{stem}.cpg").decode("ascii", "ignore").strip()
                    encoding = cpg or None
                except KeyError:
                    pass

                sf = shapefile.Reader(shp=shp_bytes, shx=shx_bytes, dbf=dbf_bytes, encoding=encoding)

                # Build robust field-name map
                # sf.fields: [("DeletionFlag","C",1,0), ("NAM","C",80,0), ...]
                field_names = [f[0].lower() for f in sf.fields[1:]]  # skip DeletionFlag
                required = {"snr_txt", "nam", "strasse", "plz", "ort"}
                missing = required.difference(field_names)
                if missing:
                    self.logger.error(f"Missing expected fields in {stem}: {missing}. Found: {field_names}")
                    continue

                # Iterate records
                seen_ids = set()
                for sr in sf.iterShapeRecords():
                    rec = dict(zip(field_names, sr.record))

                    snr_txt = (rec.get("snr_txt") or "").strip()
                    if not re.fullmatch(r"\d{3}", snr_txt):
                        self.logger.warning(f"[{city_name}] Invalid SNR '{snr_txt}' for {rec.get('nam')}")
                        continue
                    if snr_txt in seen_ids:
                        self.logger.warning(f"[{city_name}] Duplicate SNR '{snr_txt}'")
                        continue
                    seen_ids.add(snr_txt)

                    # geometry
                    shp = sr.shape
                    lat = lon = None
                    if shp and shp.points:
                        # Expect Point; take first coordinate defensively
                        x, y = shp.points[0]
                        lon, lat = transformer.transform(x, y)

                    yield {
                        "snr": snr_txt,
                        "name": rec.get("nam"),
                        "address": rec.get("strasse"),
                        "zip": rec.get("plz"),
                        "city": rec.get("ort"),
                        "district": rec.get("ortsteilna"),
                        "school_type": rec.get("schulart_2"),
                        "provider": rec.get("traegernam"),
                        "latitude": lat,
                        "longitude": lon,
                    }

    @staticmethod
    def normalize(item: Item) -> School:
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
