# -*- coding: utf-8 -*-
import io
import re
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

    start_urls = [ZIP_URL]

    def parse(self, response):
        # CRS: EPSG:25832 → EPSG:4326
        transformer = Transformer.from_crs(25832, 4326, always_xy=True)

        # Read both shapefiles directly from ZIP (no extractall)
        with zipfile.ZipFile(io.BytesIO(response.body), "r") as zf:
            for stem in ("gdi_schulen_hb", "gdi_schulen_bhv"):
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

                sf = shapefile.Reader(
                    shp=shp_bytes, shx=shx_bytes, dbf=dbf_bytes, encoding=encoding
                )

                field_names = [f[0] for f in sf.fields[1:]]  # skip DeletionFlag
                for sr in sf.iterShapeRecords():
                    rec = dict(zip(field_names, sr.record))

                    # geometry
                    shp = sr.shape
                    if shp and shp.points:
                        # Expect Point; take first coordinate defensively
                        x, y = shp.points[0]
                        rec['lon'], rec['lat'] = transformer.transform(x, y)
                    yield rec

    @staticmethod
    def normalize(item: Item) -> School:
        # Create case-insensitive lookup
        item_lower = {k.lower(): v for k, v in item.items()}

        # Extract and validate school ID
        snr_txt = (item_lower.get("snr_txt") or "").strip()
        if not snr_txt or not re.fullmatch(r"\d{3}", snr_txt):
            raise ValueError(f"Invalid or missing SNR_TXT: '{snr_txt}'")

        school_id = f"HB-{snr_txt}"

        return School(
            id=school_id,
            name=(item_lower.get("nam") or "").strip(),
            address=(item_lower.get("strasse") or "").strip(),
            zip=(item_lower.get("plz") or "").strip(),
            city=(item_lower.get("ort") or "").strip(),
            school_type=(item_lower.get("schulart_2") or "").strip(),
            provider=(item_lower.get("traegernam") or "").strip(),
            latitude=item.get("lat"),
            longitude=item.get("lon"),
        )
