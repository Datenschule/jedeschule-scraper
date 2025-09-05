import unittest

from scrapy.http import TextResponse

from jedeschule.spiders.bayern import BayernSpider


class TestBayernSpider(unittest.TestCase):
    def test_parse(self):
        xml_response = """<?xml version='1.0' encoding='UTF-8'?>
                <wfs:FeatureCollection xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                       xsi:schemaLocation="http://www.opengis.net/wfs/2.0"
                                       xmlns:wfs="http://www.opengis.net/wfs/2.0" timeStamp="2025-08-11T09:35:15Z"
                                       xmlns:gml="http://www.opengis.net/gml/3.2" numberMatched="unknown" numberReturned="0">
                    <wfs:member>
                        <schul:SchulstandorteFoerderzentren xmlns:schul="http://gdi.bayern/brbschul"
                                                            gml:id="SCHUL_SCHULSTANDORTEFOERDERZENTREN_3721b800-751d-49a1-a6d2-19d237e7bcc8">
                            <schul:schulname>Bayerische Landesschule</schul:schulname>
                            <schul:strasse>Kurzstr. 2</schul:strasse>
                            <schul:postleitzahl>81547</schul:postleitzahl>
                            <schul:ort>München</schul:ort>
                            <schul:schulart>Förderzentren</schul:schulart>
                            <schul:geometry>
                                <gml:Point
                                        gml:id="SCHUL_SCHULSTANDORTEFOERDERZENTREN_3721b800-751d-49a1-a6d2-19d237e7bcc8_SCHUL_GEOMETRY"
                                        srsName="EPSG:4326">
                                    <gml:pos>11.5686076923 48.1047906989</gml:pos>
                                </gml:Point>
                            </schul:geometry>
                        </schul:SchulstandorteFoerderzentren>
                    </wfs:member>
                </wfs:FeatureCollection>
            """

        spider = BayernSpider()
        response = TextResponse(url="https://test.com", body=xml_response, encoding="utf-8")
        schools = list(spider.parse(response))
        self.assertEqual(len(schools), 1)

        school = schools[0]
        parsed_school = spider.normalize(school)

        self.assertEqual(parsed_school["id"], "BY-SCHUL_SCHULSTANDORTEFOERDERZENTREN_3721b800-751d-49a1-a6d2-19d237e7bcc8")
        self.assertEqual(parsed_school["name"], "Bayerische Landesschule")
        self.assertEqual(parsed_school["address"], "Kurzstr. 2")
        self.assertEqual(parsed_school["city"], "München")
        self.assertEqual(parsed_school["school_type"], "Förderzentren")
        self.assertEqual(parsed_school["zip"], "81547")
        self.assertEqual(parsed_school["latitude"], 48.1047906989)
        self.assertEqual(parsed_school["longitude"], 11.5686076923)


if __name__ == "__main__":
    unittest.main()
