import json
import unittest
import urllib.parse

from scrapy.http import TextResponse

from jedeschule.spiders.niedersachsen import NiedersachsenSpider


def json_response(url, payload):
    return TextResponse(url=url, body=json.dumps(payload).encode(), encoding="utf-8")


class TestNiedersachsenSpider(unittest.TestCase):
    def test_parse_list_requests_coordinates_for_all_schools(self):
        spider = NiedersachsenSpider()
        response = json_response(
            "https://schulen.nibis.de/school/search",
            {"props": {"schools": [{"schulnr": 5009}, {"schulnr": 5101}]}},
        )

        requests = list(spider.parse_list(response))

        self.assertEqual(len(requests), 1)
        self.assertEqual(
            requests[0].url, "https://karten.nibis.de/fetchAddresses.ajax.php"
        )
        form = urllib.parse.parse_qs(requests[0].body.decode())
        self.assertEqual(json.loads(form["input"][0])["aSNo"], [5009, 5101])

    def test_parse_map_coordinates_passes_coordinates_to_details(self):
        spider = NiedersachsenSpider()
        response = json_response(
            "https://karten.nibis.de/fetchAddresses.ajax.php",
            [["5009", "52.3729052", "9.6973732"], ["78320", None, None]],
        )

        requests = list(
            spider.parse_map_coordinates(response, school_numbers=[5009, 78320, 5101])
        )

        self.assertEqual(
            [request.url for request in requests],
            [
                "https://schulen.nibis.de/school/getInfo/5009",
                "https://schulen.nibis.de/school/getInfo/78320",
                "https://schulen.nibis.de/school/getInfo/5101",
            ],
        )
        self.assertEqual(
            [request.cb_kwargs["coordinates"] for request in requests],
            [(52.3729052, 9.6973732), None, None],
        )

    def test_parse_details_attaches_coordinates(self):
        spider = NiedersachsenSpider()
        url = "https://schulen.nibis.de/school/getInfo/5009"

        [with_coordinates] = spider.parse_details(
            json_response(url, {"schulnr": 5009}), coordinates=(52.37, 9.69)
        )
        [without_coordinates] = spider.parse_details(
            json_response(url, {"schulnr": 5009}), coordinates=None
        )

        self.assertEqual(with_coordinates["latitude"], 52.37)
        self.assertEqual(with_coordinates["longitude"], 9.69)
        self.assertNotIn("latitude", without_coordinates)

    def test_normalize(self):
        school = NiedersachsenSpider.normalize(
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
                "sdb_traegerschaft": {"bezeichnung": "öffentlich"},
                "sdb_adressen": [
                    {
                        "strasse": "Musterstraße 1",
                        "sdb_ort": {"plz": "30900", "ort": "Wedemark"},
                    }
                ],
                "latitude": 52.54,
                "longitude": 9.73,
            }
        )

        self.assertEqual(school["id"], "NI-5101")
        self.assertEqual(school["name"], "Montessori Wedemark Grundschule")
        self.assertEqual(school["address"], "Musterstraße 1")
        self.assertEqual(school["zip"], "30900")
        self.assertEqual(school["city"], "Wedemark")
        self.assertEqual(school["school_type"], "Grundschule")
        self.assertEqual(school["provider"], "Gemeinde Wedemark")
        self.assertEqual(school["legal_status"], "öffentlich")
        self.assertEqual(school["latitude"], 52.54)
        self.assertEqual(school["longitude"], 9.73)

    def test_normalize_handles_missing_metadata(self):
        school = NiedersachsenSpider.normalize(
            {
                "schulnr": 5009,
                "schulname": "Beispielschule",
                "namensZusatz": None,
                "sdb_art": None,
                "sdb_traeger": None,
                "sdb_traegerschaft": None,
                "sdb_adressen": None,
            }
        )

        self.assertEqual(school["id"], "NI-5009")
        self.assertEqual(school["name"], "Beispielschule")
        self.assertIsNone(school["address"])
        self.assertIsNone(school["legal_status"])
        self.assertIsNone(school["latitude"])


if __name__ == "__main__":
    unittest.main()
