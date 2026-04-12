import tempfile
import unittest
import zipfile
from pathlib import Path

import shapefile
from pyproj import Transformer
from scrapy.http import Response

from jedeschule.spiders.bremen import BremenSpider


class TestBremenSpider(unittest.TestCase):
    def test_parse(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            transformer = Transformer.from_crs(4326, 25832, always_xy=True)

            self._write_shapefile(
                tmp_path / "gdi_schulen_hb",
                [
                    {
                        "SNR_TXT": "002",
                        "NAM": "Schule an der Admiralstrasse",
                        "STRASSE": "Winterstr. 20",
                        "PLZ": "28215",
                        "ORT": "Bremen",
                        "ORTSTEILNA": "Findorff",
                        "TRAEGERNAM": "Stadt Bremen",
                        "SCHULART_2": "Grundschule",
                        "coords": transformer.transform(8.807362345274395, 53.09026336124759),
                    }
                ],
            )
            self._write_shapefile(
                tmp_path / "gdi_schulen_bhv",
                [
                    {
                        "SNR_TXT": "150",
                        "NAM": "Amerikanische Schule",
                        "STRASSE": "Kleiner Blink 8",
                        "PLZ": "27580",
                        "ORT": "Bremerhaven",
                        "ORTSTEILNA": "Lehe",
                        "TRAEGERNAM": "Stadt Bremerhaven",
                        "SCHULART_2": "Grundschule",
                        "coords": transformer.transform(8.587648, 53.579061),
                    }
                ],
            )

            response = Response(
                url=BremenSpider.ZIP_URL,
                body=self._build_zip(tmp_path),
            )

            spider = BremenSpider()
            schools = list(spider.parse(response))

        self.assertEqual(len(schools), 2)

        first_school = spider.normalize(schools[0])
        second_school = spider.normalize(schools[1])

        self.assertEqual(first_school["id"], "HB-002")
        self.assertEqual(first_school["name"], "Schule an der Admiralstrasse")
        self.assertEqual(first_school["address"], "Winterstr. 20")
        self.assertEqual(first_school["zip"], "28215")
        self.assertEqual(first_school["city"], "Bremen")
        self.assertEqual(first_school["provider"], "Stadt Bremen")
        self.assertEqual(first_school["school_type"], "Grundschule")
        self.assertAlmostEqual(first_school["latitude"], 53.09026336124759)
        self.assertAlmostEqual(first_school["longitude"], 8.807362345274395)

        self.assertEqual(second_school["id"], "HB-150")
        self.assertEqual(second_school["city"], "Bremerhaven")
        self.assertEqual(second_school["provider"], "Stadt Bremerhaven")
        self.assertEqual(second_school["school_type"], "Grundschule")
        self.assertAlmostEqual(second_school["latitude"], 53.579061, places=5)
        self.assertAlmostEqual(second_school["longitude"], 8.587648, places=5)

    def _write_shapefile(self, base_path: Path, rows: list[dict]):
        with shapefile.Writer(str(base_path), shapeType=shapefile.POINT) as writer:
            writer.field("SNR_TXT", "C")
            writer.field("NAM", "C")
            writer.field("STRASSE", "C")
            writer.field("PLZ", "C")
            writer.field("ORT", "C")
            writer.field("ORTSTEILNA", "C")
            writer.field("TRAEGERNAM", "C")
            writer.field("SCHULART_2", "C")

            for row in rows:
                x, y = row["coords"]
                writer.point(x, y)
                writer.record(
                    row["SNR_TXT"],
                    row["NAM"],
                    row["STRASSE"],
                    row["PLZ"],
                    row["ORT"],
                    row["ORTSTEILNA"],
                    row["TRAEGERNAM"],
                    row["SCHULART_2"],
                )

        (base_path.with_suffix(".cpg")).write_text("UTF-8", encoding="ascii")

    def _build_zip(self, tmp_path: Path) -> bytes:
        zip_path = tmp_path / "bremen.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for stem in ("gdi_schulen_hb", "gdi_schulen_bhv"):
                for suffix in (".shp", ".shx", ".dbf", ".cpg"):
                    path = tmp_path / f"{stem}{suffix}"
                    zf.write(path, arcname=path.name)
        return zip_path.read_bytes()


if __name__ == "__main__":
    unittest.main()
