import unittest
from scrapy.http import TextResponse
from jedeschule.spiders.berlin import BerlinSpider


class TestBerlinSpider(unittest.TestCase):
    def test_parse(self):
        json_response = """
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": "schulen.01A04",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [13.33391576, 52.52672359]
                    },
                    "geometry_name": "geom",
                    "properties": {
                        "bsn": "01A04",
                        "schulname": "Berlin-Kolleg",
                        "schulart": "Kolleg",
                        "traeger": "öffentlich",
                        "schultyp": "Andere Schule",
                        "bezirk": "Mitte",
                        "ortsteil": "Moabit",
                        "plz": "10551",
                        "strasse": "Turmstraße",
                        "hausnr": "75",
                        "telefon": "+49 30 901838210",
                        "fax": "+49 30 901838222",
                        "email": "sekretariat@berlin-kolleg.de",
                        "internet": "https://www.berlin-kolleg.de",
                        "schuljahr": "2024/25"
                    },
                    "bbox": [
                        13.33391576,
                        52.52672359,
                        13.33391576,
                        52.52672359
                    ]
                }
            ],
            "totalFeatures": 925,
            "numberMatched": 925,
            "numberReturned": 1,
            "timeStamp": "2025-06-13T14:59:35.045Z",
            "crs": {
                "type": "name",
                "properties": {
                    "name": "urn:ogc:def:crs:EPSG::4326"
                }
            },
            "bbox": [
                13.33391576,
                52.52672359,
                13.33391576,
                52.52672359
            ]
        }
        """

        spider = BerlinSpider()
        response = TextResponse(
            url="http://test_webserver.com",
            body=json_response.encode("utf-8"),
            encoding="utf-8",
        )

        schools = list(spider.parse(response))
        self.assertEqual(len(schools), 1)

        school = schools[0]
        parsed_school = spider.normalize(school)

        self.assertEqual(parsed_school["id"], "BE-01A04")
        self.assertEqual(parsed_school["name"], "Berlin-Kolleg")
        self.assertEqual(parsed_school["address"], "Turmstraße 75")
        self.assertEqual(parsed_school["city"], "Berlin")
        self.assertEqual(parsed_school["fax"], "+49 30 901838222")
        self.assertEqual(parsed_school["phone"], "+49 30 901838210")
        self.assertEqual(parsed_school["school_type"], "Kolleg")
        self.assertEqual(parsed_school["website"], "https://www.berlin-kolleg.de")
        self.assertEqual(parsed_school["zip"], "10551")
        self.assertEqual(parsed_school["latitude"], 52.52672359)
        self.assertEqual(parsed_school["longitude"], 13.33391576)


if __name__ == "__main__":
    unittest.main()
