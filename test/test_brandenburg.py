import unittest
from scrapy.http import TextResponse
import json

from jedeschule.spiders.brandenburg import BrandenburgSpider


class TestBrandenburgSpider(unittest.TestCase):

    def test_parse(self):
        json_text = json.dumps({
            "type": "FeatureCollection",
            "name": "Schul_Standorte",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "schul_nr": "100020",
                        "schulname": "Grundschule Forst Mitte",
                        "strasse_hausnr": "Max-Fritz-Hammer-Straße 15",
                        "plz": "03149",
                        "ort": "Forst (Lausitz)",
                        "telefonnummer": "(03562) 7163",
                        "faxnummer": "(03562) 691288",
                        "dienst_email": "s100020@schulen.brandenburg.de",
                        "homepage": "http://www.grundschule-forst-mitte.de",
                        "schulamtname": "Staatliches Schulamt Cottbus",
                        "kreis": "Spree-Neiße",
                        "schulform_kurzbez": "G",
                        "schulform": "Grundschule",
                        "traeger": "Gemeinde",
                        "schultraeger_grp": "o",
                        "schueler": "288 (Stand: 2022)",
                        "besonderheiten_sl": "(763),(561),(132),(201)",
                        "besonderheiten": [
                            "Einstiegsphase Startchancen",
                            "Schule mit Nutzung Schul-Cloud Brandenburg",
                            "verlässliche Halbtagsschule und Hort",
                            "FLEX - Optimierung des Schulanfangs"
                        ],
                        "studienseminar": "2",
                        "fremdsprachen": ["Englisch"],
                        "fremdsprachen_sl": "(EN)",
                        "fremdsprachen_timestmp": "(Schuljahr: 2020/2021)"
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [14.651148207215728, 51.74023651973522]
                    }
                }
            ]
        })

        spider = BrandenburgSpider()
        response = TextResponse(
            url="http://test_webserver.com",
            body=json_text.encode("utf-8"),
            encoding="utf-8",
        )

        results = list(spider.parse(response))

        self.assertEqual(len(results), 1)
        school = results[0]

        self.assertAlmostEqual(school["lat"], 51.74023651973522)
        self.assertAlmostEqual(school["lon"], 14.651148207215728)

        self.assertEqual(school["schul_nr"], "100020")
        self.assertEqual(school["schulname"], "Grundschule Forst Mitte")
        self.assertEqual(school["plz"], "03149")
        self.assertEqual(school["ort"], "Forst (Lausitz)")
        self.assertEqual(school["dienst_email"], "s100020@schulen.brandenburg.de")
        self.assertEqual(school["schulform"], "Grundschule")
        self.assertEqual(school["traeger"], "Gemeinde")


if __name__ == '__main__':
    unittest.main()
