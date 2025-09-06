import unittest

from scrapy.http import TextResponse

from jedeschule.spiders.hamburg import HamburgSpider


class TestHamburgSpider(unittest.TestCase):
    def test_parse(self):
        json_response = """
        {
            "type": "FeatureCollection",
            "numberReturned": 1,
            "numberMatched": 453,
            "timeStamp": "2025-07-14T19:20:02Z",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            10.047106063058099,
                            53.601522503676144
                        ]
                    },
                    "properties": {
                        "abschluss": "Allgemeine Hochschulreife|erster allgemeinbildender Schulabschluss|Erweiterter erster allgemeinbildender Schulabschluss|mittlerer Schulabschluss|schulischer Teil der Fachhochschulreife",
                        "adresse_ort": "22307 Hamburg",
                        "adresse_strasse_hausnr": "Benzenbergweg 2",
                        "ansprechp_klasse_5": "Nadine Kalsow",
                        "ansprechp_buero": "Janka Gierck",
                        "anzahl_schueler": 996,
                        "anzahl_schueler_gesamt": "1261 an 2 Standorten",
                        "bezirk": "Hamburg-Nord",
                        "fax": "+49 40 428 88 15 22",
                        "fremdsprache": "Englisch|Französisch|Spanisch|Spanisch",
                        "fremdsprache_mit_klasse": "Englisch ab Klasse  5|Französisch ab Klasse  7|Spanisch ab Klasse  11|Spanisch ab Klasse  7",
                        "ganztagsform": "GTS teilweise gebunden",
                        "is_rebbz": "true",
                        "kapitelbezeichnung": "Stadtteilschulen",
                        "lgv_standortk_erwachsenenbildung": "No",
                        "name_schulleiter": "Bianca Thies",
                        "name_stellv_schulleiter": "Christian Pape",
                        "name_oberstufenkoordinator": "Frau Scheuermann-Andersen *49 40 428 88 15-61",
                        "name_verwaltungsleitung": "Grit Sobottka",
                        "rebbz_homepage": "http://rebbz-winterhude.hamburg.de/",
                        "rechtsform": "staatlich",
                        "schueleranzahl_schuljahr": "2024",
                        "schul_email": "stadtteilschule-helmuth-huebener@bsb.hamburg.de",
                        "schul_homepage": "https://helmuthhuebener.de",
                        "schul_id": "5043-0",
                        "schul_telefonnr": "+49 40 428 88 15 0",
                        "schulaufsicht": "Christine Zopff",
                        "schulform": "Stadtteilschule",
                        "schulinspektion_link": "https://www.hamburg.de/politik-und-verwaltung/behoerden/schulbehoerde/themen/schulaufsicht/inspektionsberichte/weiterfuehrende-schulen-hamburg-nord",
                        "schulname": "Stadtteilschule Helmuth Hübener",
                        "schultyp": "Hauptstandort",
                        "sozialindex": "Stufe 2",
                        "stadtteil": "Barmbek-Nord",
                        "standort_id": "431",
                        "zuegigkeit_kl_5": "7",
                        "zustaendiges_rebbz": "ReBBZ Winterhude"
                    },
                    "id": 875415
                }
            ],
            "links": []
        }
        """

        spider = HamburgSpider()
        response = TextResponse(
            url="http://test_webserver.com",
            body=json_response.encode("utf-8"),
            encoding="utf-8",
        )

        schools = list(spider.parse(response))
        self.assertEqual(len(schools), 1)

        school = schools[0]
        parsed_school = spider.normalize(school)

        self.assertEqual(parsed_school["id"], "HH-5043-0")
        self.assertEqual(parsed_school["name"], "Stadtteilschule Helmuth Hübener")
        self.assertEqual(parsed_school["address"], "Benzenbergweg 2")
        self.assertEqual(parsed_school["city"], "Hamburg")
        self.assertEqual(parsed_school["fax"], "+49 40 428 88 15 22")
        self.assertEqual(parsed_school["phone"], "+49 40 428 88 15 0")
        self.assertEqual(parsed_school["school_type"], "Stadtteilschule")
        self.assertEqual(parsed_school["website"], "https://helmuthhuebener.de")
        self.assertEqual(parsed_school["zip"], "22307")
        self.assertEqual(parsed_school["latitude"], 53.601522503676144)
        self.assertEqual(parsed_school["longitude"], 10.047106063058099)


if __name__ == "__main__":
    unittest.main()
