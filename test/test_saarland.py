import unittest

from scrapy.http import TextResponse

from jedeschule.spiders.saarland import SaarlandSpider


class TestSaarlandSpider(unittest.TestCase):

    def test_parse(self):
        xml = """<?xml version="1.0" encoding="utf-8" ?>
                    <wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0"
                       xmlns:gml="http://www.opengis.net/gml/3.2"
                       xmlns:Staatliche_Dienste="https://geoportal.saarland.de/arcgis/services/Internet/Staatliche_Dienste/MapServer/WFSServer">
                        <wfs:member>
                            <Staatliche_Dienste:Schulen_SL gml:id="Schulen_SL.1">
                                <Staatliche_Dienste:OBJECTID>1</Staatliche_Dienste:OBJECTID>
                                <Staatliche_Dienste:Shape>
                                    <gml:Point gml:id="Schulen_SL.1.pn.0" srsName="urn:ogc:def:crs:EPSG::4326">
                                        <gml:pos>49.24067452 7.02085050</gml:pos>
                                    </gml:Point>
                                </Staatliche_Dienste:Shape>
                                <Staatliche_Dienste:KREIS>41</Staatliche_Dienste:KREIS>
                                <Staatliche_Dienste:PLZ>66123</Staatliche_Dienste:PLZ>
                                <Staatliche_Dienste:ORT_NAME>Saarbrücken</Staatliche_Dienste:ORT_NAME>
                                <Staatliche_Dienste:POST_ORT>St.Johann</Staatliche_Dienste:POST_ORT>
                                <Staatliche_Dienste:STR_NAME>Kohlweg</Staatliche_Dienste:STR_NAME>
                                <Staatliche_Dienste:HNR>7</Staatliche_Dienste:HNR>
                                <Staatliche_Dienste:ADZ> </Staatliche_Dienste:ADZ>
                                <Staatliche_Dienste:SCHULFORM>Hochschule</Staatliche_Dienste:SCHULFORM>
                                <Staatliche_Dienste:SCHULNAME>Deutsch-Französiche Hochschule, Universite´ franco-allemande</Staatliche_Dienste:SCHULNAME>
                                <Staatliche_Dienste:SCHULEN_2> </Staatliche_Dienste:SCHULEN_2>
                                <Staatliche_Dienste:SCHULEN_3> </Staatliche_Dienste:SCHULEN_3>
                                <Staatliche_Dienste:SCHULEN_4> </Staatliche_Dienste:SCHULEN_4>
                                <Staatliche_Dienste:SCHULREGIO>Regionalverband Saarbrücken</Staatliche_Dienste:SCHULREGIO>
                                <Staatliche_Dienste:SCHULKENNZ>0</Staatliche_Dienste:SCHULKENNZ>
                                <Staatliche_Dienste:KARTENERST>Hochschule</Staatliche_Dienste:KARTENERST>
                                <Staatliche_Dienste:RW>2574380.85600000</Staatliche_Dienste:RW>
                                <Staatliche_Dienste:HW>5456457.44000000</Staatliche_Dienste:HW>
                                <Staatliche_Dienste:ERFASSUNG>Geodatenzentrum, Stand: 29.11.2022</Staatliche_Dienste:ERFASSUNG>
                            </Staatliche_Dienste:Schulen_SL>
                        </wfs:member>
                    </wfs:FeatureCollection>
                    """

        spider = SaarlandSpider()
        response = TextResponse(url="https://test.com", body=xml, encoding="utf-8")

        schools = list(spider.parse(response))

        self.assertEqual(len(schools), 1)

        school = schools[0]

        self.assertEqual(school["lat"], "49.24067452")
        self.assertEqual(school["lon"], "7.02085050")

        self.assertEqual(school["OBJECTID"], "1")
        self.assertEqual(school["KREIS"], "41")
        self.assertEqual(school["PLZ"], "66123")
        self.assertEqual(school["ORT_NAME"], "Saarbrücken")
        self.assertEqual(school["POST_ORT"], "St.Johann")
        self.assertEqual(school["STR_NAME"], "Kohlweg")
        self.assertEqual(school["HNR"], "7")
        self.assertEqual(school["SCHULFORM"], "Hochschule")
        self.assertEqual(school["SCHULNAME"],
                         "Deutsch-Französiche Hochschule, Universite´ franco-allemande")
        self.assertEqual(school["SCHULREGIO"], "Regionalverband Saarbrücken")


if __name__ == "__main__":
    unittest.main()
