import json
import unittest
import urllib.parse

from scrapy import Request
from scrapy.http import TextResponse

from jedeschule.spiders.niedersachsen import NiedersachsenSpider


class TestNiedersachsenSpider(unittest.TestCase):
    def test_parse_api_search_requests_map_coordinates_by_school_number(self):
        spider = NiedersachsenSpider()
        response = TextResponse(
            url="https://schulen.nibis.de/school/search",
            request=Request(url="https://schulen.nibis.de/school/search"),
            body=json.dumps({"props": {"schools": [{"schulnr": 5009}]}}).encode(),
            encoding="utf-8",
        )

        requests = list(spider.parse_api_search(response))

        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].url, "https://karten.nibis.de/fetchAddresses.ajax.php")
        form = urllib.parse.parse_qs(requests[0].body.decode())
        self.assertEqual(json.loads(form["input"][0])["aSNo"], ["5009"])

    def test_parse_map_coords_joins_coordinates_by_school_number(self):
        spider = NiedersachsenSpider()
        response = TextResponse(
            url="https://karten.nibis.de/fetchAddresses.ajax.php",
            request=Request(url="https://karten.nibis.de/fetchAddresses.ajax.php"),
            body=json.dumps(
                [
                    ["5009", "52.37", "9.70"],
                    ["5010", None, None],
                    ["bad", "not-a-number", "9.0"],
                    ["outside", "91", "9.0"],
                ]
            ).encode(),
            encoding="utf-8",
        )

        requests = list(spider.parse_map_coords(response, [{"schulnr": 5009}, {"schulnr": 5010}]))

        self.assertEqual(spider._coords, {"5009": (52.37, 9.70)})
        self.assertEqual(len(requests), 2)
        self.assertTrue(requests[0].url.endswith("/5009"))

    def test_parse_map_coords_failure_still_requests_school_details(self):
        spider = NiedersachsenSpider()
        failure = type("Failure", (), {"getErrorMessage": lambda self: "503"})()

        requests = list(spider.parse_map_coords_failure(failure, [{"schulnr": 5009}]))

        self.assertEqual(len(requests), 1)
        self.assertTrue(requests[0].url.endswith("/5009"))

    def test_parse_details_attaches_nibis_coordinates(self):
        spider = NiedersachsenSpider()
        spider._coords = {"5009": (52.37, 9.70)}

        items = list(spider.parse_details(self._detail_response(5009)))

        self.assertEqual(items[0]["latitude"], 52.37)
        self.assertEqual(items[0]["longitude"], 9.70)

    def test_parse_details_keeps_item_when_coordinate_is_missing(self):
        spider = NiedersachsenSpider()
        spider._coords = {}

        items = list(spider.parse_details(self._detail_response(5009)))

        self.assertEqual(len(items), 1)
        self.assertNotIn("latitude", items[0])

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

    def test_normalize_handles_missing_addresses(self):
        school = NiedersachsenSpider.normalize({"schulnr": 5102, "schulname": "Ohne Adresse"})

        self.assertEqual(school["id"], "NI-5102")
        self.assertIsNone(school["address"])
        self.assertIsNone(school["city"])

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
            body=json.dumps(payload).encode(),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
