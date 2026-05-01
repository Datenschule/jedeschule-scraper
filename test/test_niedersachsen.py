import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scrapy import Request
from scrapy.http import TextResponse

from jedeschule.spiders import niedersachsen as niedersachsen_module
from jedeschule.spiders.niedersachsen import NiedersachsenSpider


class TestNiedersachsenSpider(unittest.TestCase):
    def test_parse_details_attaches_coords_when_official_match_exists(self):
        spider = self._spider_with_cache(
            [
                {
                    "schulnr": 5009,
                    "status": "matched_by_distance",
                    "latitude": 52.37,
                    "longitude": 9.70,
                }
            ]
        )

        items = list(spider.parse_details(self._detail_response(5009)))

        self.assertEqual(items[0]["latitude"], 52.37)
        self.assertEqual(items[0]["longitude"], 9.70)

    def test_parse_details_keeps_item_when_geocode_missing(self):
        spider = self._spider_with_cache([])

        items = list(spider.parse_details(self._detail_response(5009)))

        # Unmatched schools must still flow through — no coord, but still yielded.
        self.assertEqual(len(items), 1)
        self.assertNotIn("latitude", items[0])

    def test_parse_details_ignores_non_matched_cache_rows(self):
        spider = self._spider_with_cache(
            [
                {"schulnr": 5009, "status": "skipped"},
                {"schulnr": 5010, "status": "not_a_match"},
            ]
        )

        for schulnr in (5009, 5010):
            items = list(spider.parse_details(self._detail_response(schulnr)))
            self.assertEqual(len(items), 1)
            self.assertNotIn("latitude", items[0])

    def test_load_coords_logs_warning_when_cache_missing(self):
        spider = NiedersachsenSpider()
        with patch.object(niedersachsen_module, "NLS_CACHE", Path("/nonexistent/path.jsonl")):
            spider._load_coords()
        self.assertEqual(spider._coords, {})

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
                    {"strasse": "Musterstrasse 1", "sdb_ort": {"plz": 30900, "ort": "Wedemark"}}
                ],
                "latitude": 52.54,
                "longitude": 9.73,
            }
        )

        self.assertEqual(parsed_school["id"], "NI-5101")
        self.assertEqual(parsed_school["name"], "Montessori Wedemark Grundschule")
        self.assertEqual(parsed_school["latitude"], 52.54)
        self.assertEqual(parsed_school["longitude"], 9.73)

    def _spider_with_cache(self, records: list[dict]) -> NiedersachsenSpider:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8")
        try:
            for rec in records:
                tmp.write(json.dumps(rec) + "\n")
            tmp.close()
            self.addCleanup(lambda path=tmp.name: Path(path).unlink(missing_ok=True))
            with patch.object(niedersachsen_module, "NLS_CACHE", Path(tmp.name)):
                spider = NiedersachsenSpider()
                spider._load_coords()
            return spider
        except Exception:
            Path(tmp.name).unlink(missing_ok=True)
            raise

    def _detail_response(self, schulnr: int) -> TextResponse:
        payload = {
            "schulnr": schulnr,
            "schulname": "Beispielschule",
            "namensZusatz": "",
            "telefon": None,
            "fax": None,
            "email": None,
            "homepage": None,
            "sdb_traeger": {"name": None},
            "sdb_traegerschaft": {"bezeichnung": None},
            "sdb_art": {"art": "Grundschule"},
            "sdb_adressen": [{"strasse": "Musterstr. 1", "sdb_ort": {"plz": 30000, "ort": "Beispielort"}}],
        }
        return TextResponse(
            url=f"https://schulen.nibis.de/school/getInfo/{schulnr}",
            request=Request(url=f"https://schulen.nibis.de/school/getInfo/{schulnr}"),
            body=json.dumps(payload).encode("utf-8"),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
