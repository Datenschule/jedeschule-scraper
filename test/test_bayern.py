import unittest

from scrapy.http import TextResponse

from jedeschule.spiders.bayern import BayernSpider


class TestBayernSpider(unittest.TestCase):
    def test_start_requests_use_km_detail_pages(self):
        spider = BayernSpider(school_numbers="1216,2448")

        requests = list(spider.start_requests())

        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[0].url, "https://www.km.bayern.de/schule/1216")
        self.assertEqual(requests[0].callback, spider.parse_school)

    def test_enumerates_four_digit_candidate_numbers_by_default(self):
        spider = BayernSpider(end_number=3)

        requests = list(spider.start_requests())

        self.assertEqual(
            [request.url for request in requests],
            [
                "https://www.km.bayern.de/schule/0001",
                "https://www.km.bayern.de/schule/0002",
                "https://www.km.bayern.de/schule/0003",
            ],
        )

    def test_parse_school(self):
        html_response = """
            <html>
                <body>
                    <h1>Grundschule Aßling</h1>
                    <div class="articleLeft schoolSearchResult">
                        <section>
                            <div class="rxModule">
                                <h2 class="rxFirstText">Kontakt</h2>
                                <p>Schulstraße 3 - 5<br>85617 Aßling</p>
                                <p>Telefon: 08092/4911<br>Fax: 08092/32806<br>Web:
                                    <a class="website" href="https://www.schule-assling.de" target="_blank">www.schule-assling.de</a>
                                </p>
                                <a class="bigButton" href="https://geoportal.bayern.de/bayernatlas/?lang=de&amp;topic=ba&amp;bgLayer=atkis&amp;crosshair=marker&amp;E=12.0048456&amp;N=47.9903501&amp;zoom=12&amp;catalogNodes=11,122">Standort anzeigen (BayernAtlas)</a>
                                <h2>Verwaltungsangaben</h2>
                                <p>Schulnummer: 2448<br>Schulart: Grund- u. Mittel-/Hauptschulen<br>Rechtlicher Status: öffentliche Schule (staatlich)</p>
                                <h2>Eckdaten im Schuljahr 2025/26</h2>
                                <p>Vollzeit- und überhälftig teilzeitbeschäftigte Lehrkräfte: 012<br>Schüler: 0259</p>
                                <h2>Besondere Betreuungsangebote</h2>
                                <p>Deutsch in (ganzjährigen) Vorkursen<br>Mittagsbetreuung o.ä.</p>
                                <h2>Ausbildungsrichtungen</h2>
                                <p>Grundschule (Jahrgangsstufen 1-4, voll ausgebaut)</p>
                            </div>
                        </section>
                    </div>
                </body>
            </html>
            """
        spider = BayernSpider()
        response = TextResponse(
            url="https://www.km.bayern.de/schule/2448",
            body=html_response,
            encoding="utf-8",
        )

        schools = list(spider.parse_school(response))

        self.assertEqual(len(schools), 1)

        school = schools[0]
        parsed_school = spider.normalize(school)

        self.assertEqual(school["schulnummer"], "2448")
        self.assertEqual(school["schuljahr"], "2025/26")
        self.assertEqual(school["lehrkraefte"], 12)
        self.assertEqual(school["schueler"], 259)
        self.assertEqual(
            school["betreuungsangebote"],
            ["Deutsch in (ganzjährigen) Vorkursen", "Mittagsbetreuung o.ä."],
        )
        self.assertEqual(
            school["ausbildungsrichtungen"],
            ["Grundschule (Jahrgangsstufen 1-4, voll ausgebaut)"],
        )
        self.assertEqual(parsed_school["id"], "BY-2448")
        self.assertEqual(parsed_school["name"], "Grundschule Aßling")
        self.assertEqual(parsed_school["address"], "Schulstraße 3 - 5")
        self.assertEqual(parsed_school["city"], "Aßling")
        self.assertEqual(parsed_school["school_type"], "Grund- u. Mittel-/Hauptschulen")
        self.assertEqual(parsed_school["legal_status"], "öffentliche Schule (staatlich)")
        self.assertEqual(parsed_school["zip"], "85617")
        self.assertEqual(parsed_school["phone"], "08092/4911")
        self.assertEqual(parsed_school["fax"], "08092/32806")
        self.assertEqual(parsed_school["website"], "https://www.schule-assling.de")
        self.assertEqual(parsed_school["latitude"], 47.9903501)
        self.assertEqual(parsed_school["longitude"], 12.0048456)


if __name__ == "__main__":
    unittest.main()
