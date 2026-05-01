import io
import re
import zipfile
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

                for record in sf.records():
                    yield record.as_dict()

    @staticmethod
    def normalize(item: Item) -> School:
        item_lower = {k.lower(): v for k, v in item.items()}
        snr_txt = (item_lower.get("snr_txt") or "").strip()
        if not snr_txt or not re.fullmatch(r"\d{3}", snr_txt):
            raise ValueError(f"Invalid or missing SNR_TXT: '{snr_txt}'")

        transformer = Transformer.from_crs(25832, 4326, always_xy=True)
        lon, lat = transformer.transform(item.get('x_etrs'), item.get('y_etrs'))


        return School(
            id=f"HB-{snr_txt}",
            name=(item_lower.get("nam") or "").strip(),
            address=(item_lower.get("strasse") or "").strip(),
            zip=(item_lower.get("plz") or "").strip(),
            city=(item_lower.get("ort") or "").strip(),
            school_type=(item_lower.get("schulart_2") or "").strip(),
            provider=(item_lower.get("traegernam") or "").strip(),
            latitude=lat,
            longitude=lon,
        )
