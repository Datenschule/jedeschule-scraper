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
            url="http://example.com",
            body=json_response.encode("utf-8"),
            encoding="utf-8",
        )


        schools = list(spider.parse(response))
        self.assertEqual(len(schools), 1)

        school = schools[0]
        self.assertAlmostEqual(school["lon"], 13.33391576)
        self.assertAlmostEqual(school["lat"], 52.52672359)
        self.assertEqual(school["bsn"], "01A04")
        self.assertEqual(school["schulname"], "Berlin-Kolleg")
        self.assertEqual(school["plz"], "10551")
        self.assertEqual(school["strasse"], "Turmstraße")
        self.assertEqual(school["hausnr"], "75")
        self.assertEqual(school["telefon"], "+49 30 901838210")
        self.assertEqual(school["fax"], "+49 30 901838222")
        self.assertEqual(school["email"], "sekretariat@berlin-kolleg.de")
        self.assertEqual(school["internet"], "https://www.berlin-kolleg.de")


if __name__ == "__main__":
    unittest.main()
