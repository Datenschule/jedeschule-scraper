import json
import unittest
import urllib.parse

from scrapy import Request
from scrapy.http import TextResponse
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import TimeoutError
from twisted.python.failure import Failure

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
        for error in (TimeoutError(), HttpError(TextResponse(url="https://karten.nibis.de/", status=503))):
            with self.subTest(error=type(error).__name__):
                spider = NiedersachsenSpider()
                request = next(spider.parse_api_search(self._json_response(
                    {"props": {"schools": [{"schulnr": 5009}, {"schulnr": 5010}]}}
                )))
                failure = Failure(error)
                failure.request = request
                # Scrapy passes only Failure to errbacks, not cb_kwargs.
                with self.assertLogs(spider.name, level="ERROR"):
                    requests = list(request.errback(failure))

                self.assertEqual(len(requests), 2)
                self.assertTrue(requests[0].url.endswith("/5009"))
                self.assertTrue(requests[1].url.endswith("/5010"))
                for detail in requests:
                    number = detail.cb_kwargs["school_number"]
                    items = list(detail.callback(self._detail_response(int(number)), **detail.cb_kwargs))
                    school = spider.normalize(items[0])
                    self.assertEqual(school["id"], f"NI-{number}")
                    self.assertIsNone(school["latitude"])
                    self.assertIsNone(school["longitude"])

    def test_malformed_map_responses_still_schedule_details(self):
        for body in (b"null", b"false", b"42", b'"unavailable"', b'{"error":"unavailable"}', b"<html>error</html>"):
            with self.subTest(body=body):
                spider = NiedersachsenSpider()
                response = TextResponse(url="https://karten.nibis.de/", body=body, encoding="utf-8")
                with self.assertLogs(spider.name, level="ERROR"):
                    requests = list(spider.parse_map_coords(response, [{"schulnr": 5009}]))
                self.assertEqual(len(requests), 1)
                self.assertEqual(spider._coords, {})

    def test_map_ignores_invalid_coordinates_and_unrequested_ids(self):
        spider = NiedersachsenSpider()
        rows = [[None, 52, 9], [9999, 52, 9], [5009, True, 9], [5009, 52, False],
                [5009, "NaN", 9], [5009, 52, "Infinity"], [5009, 91, 9],
                [5009, 52, 181], [5009, None, 9], [5009], None,
                [5009, "52.37", "9.70"]]
        requests = list(spider.parse_map_coords(self._json_response(rows), [{"schulnr": 5009}]))
        self.assertEqual(len(requests), 1)
        self.assertEqual(spider._coords, {"5009": (52.37, 9.70)})

    def test_search_ignores_invalid_ids(self):
        spider = NiedersachsenSpider()
        schools = [{}, None, {"schulnr": True}, {"schulnr": "invalid"}, {"schulnr": 5009}]
        with self.assertLogs(spider.name, level="WARNING"):
            request = next(spider.parse_api_search(self._json_response({"props": {"schools": schools}})))
        self.assertEqual(request.cb_kwargs["schools"], [{"schulnr": 5009}])
        form = urllib.parse.parse_qs(request.body.decode())
        self.assertEqual(json.loads(form["input"][0])["aSNo"], ["5009"])

    def test_empty_search_does_not_request_all_map_coordinates(self):
        spider = NiedersachsenSpider()
        self.assertEqual(list(spider.parse_api_search(self._json_response({"props": {"schools": []}}))), [])

    def test_malformed_search_is_reported_without_requests(self):
        spider = NiedersachsenSpider()
        for payload in (None, False, [], {}, {"props": None}, {"props": {"schools": None}}):
            with self.subTest(payload=payload), self.assertLogs(spider.name, level="ERROR"):
                self.assertEqual(list(spider.parse_api_search(self._json_response(payload))), [])

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

    def test_invalid_detail_payloads_never_yield_schools(self):
        spider = NiedersachsenSpider()
        payloads = [None, [], False, {}, {"message": "Temporary error"}]
        payloads += [{"schulnr": value} for value in (None, "", "abc", "NI-5009", -1, 0, True, 5009.0)]
        for payload in payloads:
            with self.subTest(payload=payload), self.assertLogs(spider.name, level="ERROR"):
                self.assertEqual(list(spider.parse_details(self._json_response(payload))), [])

    def test_mismatched_detail_school_is_rejected(self):
        spider = NiedersachsenSpider()
        request = next(spider._detail_requests([{"schulnr": 5009}]))
        with self.assertLogs(spider.name, level="ERROR"):
            items = list(request.callback(self._detail_response(5010), **request.cb_kwargs))
        self.assertEqual(items, [])

    def test_valid_numeric_ids_remain_stable(self):
        spider = NiedersachsenSpider()
        for value in (5009, "5009", "05009"):
            with self.subTest(value=value):
                items = list(spider.parse_details(self._json_response({"schulnr": value})))
                self.assertEqual(spider.normalize(items[0])["id"], f"NI-{value}")

    def test_normalize_rejects_missing_or_invalid_ids(self):
        for item in ({}, {"schulnr": None}, {"schulnr": "invalid"}, {"schulnr": False}):
            with self.subTest(item=item), self.assertRaises(ValueError):
                NiedersachsenSpider.normalize(item)

    def test_normalize_handles_null_optional_metadata(self):
        school = NiedersachsenSpider.normalize({"schulnr": 5009, "sdb_traegerschaft": None,
                                               "sdb_traeger": None, "sdb_art": None,
                                               "hauptsitz": None, "sdb_adressen": None})
        self.assertEqual(school["id"], "NI-5009")
        self.assertIsNone(school["legal_status"])
        self.assertIsNone(school["address"])

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

    def _json_response(self, payload):
        url = "https://schulen.nibis.de/school/search"
        return TextResponse(url=url, request=Request(url), body=json.dumps(payload).encode(), encoding="utf-8")

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
