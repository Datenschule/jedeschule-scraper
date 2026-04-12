import json
import tempfile
import unittest
from pathlib import Path

import shapefile
from scrapy import Request
from scrapy.http import TextResponse

from jedeschule.spiders.niedersachsen import NiedersachsenSpider


class TestNiedersachsenSpider(unittest.TestCase):
    def test_parse_details_enriches_exact_local_match(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            spider = NiedersachsenSpider()
            self._configure_local_shapefiles(spider, Path(tmpdir))
            self._write_abs_shapefile(
                Path(tmpdir) / "ABS_Shape2024",
                [
                    {
                        "Schulname": "Albert-Schweitzer-Schule",
                        "Schulform": "GS",
                        "KomTyp": "Landkreis",
                        "KomName": "Region Hannover",
                        "coords": (9.70, 52.37),
                    }
                ],
            )
            self._write_foerder_shapefile(Path(tmpdir) / "Foerder2024", [])
            self._write_bbs_shapefile(Path(tmpdir) / "BBS2024", [])

            spider._load_local_geodata_index()
            response = self._detail_response(
                5009,
                {
                    "schulname": "Grundschule Albert-Schweitzer",
                    "namensZusatz": "",
                    "sdb_art": {"art": "Grundschule"},
                    "ag": {"sdb_kreis": {"kreis": "Hannover Region"}},
                    "sdb_adressen": [
                        {
                            "strasse": "Liepmannstrasse 6",
                            "sdb_ort": {"plz": 30453, "ort": "Hannover"},
                        }
                    ],
                },
            )

            items = list(spider.parse_details(response))

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["_source"], "api_geodata_exact")
        self.assertEqual(items[0]["latitude"], 52.37)
        self.assertEqual(items[0]["longitude"], 9.70)

    def test_duplicate_match_keys_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            spider = NiedersachsenSpider()
            self._configure_local_shapefiles(spider, Path(tmpdir))
            self._write_abs_shapefile(
                Path(tmpdir) / "ABS_Shape2024",
                [
                    {
                        "Schulname": "Albert-Schweitzer-Schule",
                        "Schulform": "GS",
                        "KomTyp": "Landkreis",
                        "KomName": "Region Hannover",
                        "coords": (9.70, 52.37),
                    },
                    {
                        "Schulname": "Albert-Schweitzer-Schule",
                        "Schulform": "GS",
                        "KomTyp": "Landkreis",
                        "KomName": "Region Hannover",
                        "coords": (9.71, 52.38),
                    },
                ],
            )
            self._write_foerder_shapefile(Path(tmpdir) / "Foerder2024", [])
            self._write_bbs_shapefile(Path(tmpdir) / "BBS2024", [])

            spider._load_local_geodata_index()
            geodata = spider._find_local_geodata(
                {
                    "schulname": "Grundschule Albert-Schweitzer",
                    "namensZusatz": "",
                    "sdb_art": {"art": "Grundschule"},
                    "ag": {"sdb_kreis": {"kreis": "Hannover Region"}},
                }
            )

        self.assertIsNone(geodata)

    def test_parse_details_keeps_api_only_when_local_geodata_is_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            spider = NiedersachsenSpider()
            self._configure_local_shapefiles(spider, Path(tmpdir))

            spider._load_local_geodata_index()
            response = self._detail_response(
                5009,
                {
                    "schulname": "Grundschule Albert-Schweitzer",
                    "namensZusatz": "",
                    "sdb_art": {"art": "Grundschule"},
                    "ag": {"sdb_kreis": {"kreis": "Hannover Region"}},
                    "sdb_adressen": [
                        {
                            "strasse": "Liepmannstrasse 6",
                            "sdb_ort": {"plz": 30453, "ort": "Hannover"},
                        }
                    ],
                },
            )

            items = list(spider.parse_details(response))

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["_source"], "api_only")
        self.assertNotIn("latitude", items[0])
        self.assertNotIn("longitude", items[0])

    def test_loader_matches_bbs_name_field(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            spider = NiedersachsenSpider()
            self._configure_local_shapefiles(spider, Path(tmpdir))
            self._write_bbs_shapefile(
                Path(tmpdir) / "BBS2024",
                [
                    {
                        "Name": "Johannes-Selenka-Schule",
                        "KomTyp": "Kreisfreie Stadt",
                        "KomName": "Braunschweig",
                        "Schulform": "Berufsschule",
                        "coords": (10.52, 52.27),
                    }
                ],
            )
            self._write_abs_shapefile(Path(tmpdir) / "ABS_Shape2024", [])
            self._write_foerder_shapefile(Path(tmpdir) / "Foerder2024", [])

            spider._load_local_geodata_index()
            geodata = spider._find_local_geodata(
                {
                    "schulname": "Johannes-Selenka-Schule",
                    "namensZusatz": "",
                    "sdb_art": {"art": "Berufsschule"},
                    "ag": {"sdb_kreis": {"kreis": "Braunschweig"}},
                }
            )

        self.assertEqual(geodata["latitude"], 52.27)
        self.assertEqual(geodata["longitude"], 10.52)

    def test_normalize_uses_namens_zusatz_and_coordinates(self):
        parsed_school = NiedersachsenSpider.normalize(
            {
                "schulnr": 5101,
                "schulname": "Montessori Wedemark",
                "namensZusatz": "Grundschule",
                "telefon": "05130 12-34",
                "fax": "05130 12-35",
                "email": "info@example.org",
                "homepage": "https://example.org",
                "sdb_art": {"art": "Grundschule"},
                "sdb_traeger": {"name": "Gemeinde Wedemark"},
                "sdb_traegerschaft": {"bezeichnung": "Offentlich"},
                "sdb_adressen": [
                    {
                        "strasse": "Musterstrasse 1",
                        "sdb_ort": {"plz": 30900, "ort": "Wedemark"},
                    }
                ],
                "latitude": 52.54,
                "longitude": 9.73,
            }
        )

        self.assertEqual(parsed_school["id"], "NI-5101")
        self.assertEqual(parsed_school["name"], "Montessori Wedemark Grundschule")
        self.assertEqual(parsed_school["city"], "Wedemark")
        self.assertEqual(parsed_school["latitude"], 52.54)
        self.assertEqual(parsed_school["longitude"], 9.73)

    def _configure_local_shapefiles(self, spider: NiedersachsenSpider, tmp_path: Path):
        spider.LOCAL_SHAPEFILE_PATHS = {
            "allgemein": str(tmp_path / "ABS_Shape2024"),
            "foerder": str(tmp_path / "Foerder2024"),
            "berufs": str(tmp_path / "BBS2024"),
        }

    def _detail_response(self, schulnr: int, payload: dict) -> TextResponse:
        payload = {
            "schulnr": schulnr,
            "telefon": None,
            "fax": None,
            "email": None,
            "homepage": None,
            "sdb_traeger": {"name": None},
            "sdb_traegerschaft": {"bezeichnung": None},
            **payload,
        }
        return TextResponse(
            url=f"https://schulen.nibis.de/school/getInfo/{schulnr}",
            request=Request(url=f"https://schulen.nibis.de/school/getInfo/{schulnr}"),
            body=json.dumps(payload).encode("utf-8"),
            encoding="utf-8",
        )

    def _write_abs_shapefile(self, base_path: Path, rows: list[dict]):
        self._write_shapefile(
            base_path,
            [
                ("Schulname", "C"),
                ("Schulform", "C"),
                ("KomTyp", "C"),
                ("KomName", "C"),
            ],
            rows,
            lambda writer, row: writer.record(
                row["Schulname"],
                row["Schulform"],
                row["KomTyp"],
                row["KomName"],
            ),
        )

    def _write_foerder_shapefile(self, base_path: Path, rows: list[dict]):
        self._write_abs_shapefile(base_path, rows)

    def _write_bbs_shapefile(self, base_path: Path, rows: list[dict]):
        self._write_shapefile(
            base_path,
            [
                ("Name", "C"),
                ("KomTyp", "C"),
                ("KomName", "C"),
                ("Schulform", "C"),
            ],
            rows,
            lambda writer, row: writer.record(
                row["Name"],
                row["KomTyp"],
                row["KomName"],
                row["Schulform"],
            ),
        )

    def _write_shapefile(self, base_path: Path, fields, rows: list[dict], record_writer):
        with shapefile.Writer(str(base_path), shapeType=shapefile.POINT) as writer:
            for field_name, field_type in fields:
                writer.field(field_name, field_type)

            for row in rows:
                longitude, latitude = row["coords"]
                writer.point(longitude, latitude)
                record_writer(writer, row)


if __name__ == "__main__":
    unittest.main()
