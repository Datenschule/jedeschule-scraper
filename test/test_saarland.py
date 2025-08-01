import unittest

from scrapy.http import TextResponse

from jedeschule.spiders.saarland import SaarlandSpider


class TestSaarlandSpider(unittest.TestCase):
    def test_parse(self):
        xml_response = """<?xml version="1.0" encoding="utf-8" ?>
                <wfs:FeatureCollection xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:wfs="http://www.opengis.net/wfs/2.0" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:Staatliche_Dienste="https://geoportal.saarland.de/arcgis/services/Internet/Staatliche_Dienste/MapServer/WFSServer" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" timeStamp="2025-07-20T17:40:21Z" numberMatched="317" numberReturned="1" xsi:schemaLocation="http://www.opengis.net/wfs/2.0 http://schemas.opengis.net/wfs/2.0/wfs.xsd http://www.opengis.net/gml/3.2 http://schemas.opengis.net/gml/3.2.1/gml.xsd https://geoportal.saarland.de/arcgis/services/Internet/Staatliche_Dienste/MapServer/WFSServer https://geoportal.saarland.de/arcgis/services/Internet/Staatliche_Dienste/MapServer/WFSServer?service=wfs%26version=2.0.0%26request=DescribeFeatureType">
                    <wfs:member>
                        <Staatliche_Dienste:Schulen_SL gml:id="Schulen_SL.1">
                            <Staatliche_Dienste:SHAPE>
                                <gml:Point gml:id="Schulen_SL.1.pn.0" srsName="urn:ogc:def:crs:EPSG::4326">
                                    <gml:pos>49.24067452 7.02085050</gml:pos>
                                </gml:Point>
                            </Staatliche_Dienste:SHAPE>
                            <Staatliche_Dienste:OBJECTID>1</Staatliche_Dienste:OBJECTID>
                            <Staatliche_Dienste:fid>1.00000000</Staatliche_Dienste:fid>
                            <Staatliche_Dienste:Gemeindenu>1100.00000000</Staatliche_Dienste:Gemeindenu>
                            <Staatliche_Dienste:PLZ>66123.00000000</Staatliche_Dienste:PLZ>
                            <Staatliche_Dienste:Ort>Saarbrücken</Staatliche_Dienste:Ort>
                            <Staatliche_Dienste:Straße>Kohlweg 7</Staatliche_Dienste:Straße>
                            <Staatliche_Dienste:Bezeichnun>Deutsch-Französiche Hochschule, Université franco-allemande</Staatliche_Dienste:Bezeichnun>
                            <Staatliche_Dienste:Telefon>0681-93812100</Staatliche_Dienste:Telefon>
                            <Staatliche_Dienste:Fax>0681-93812111</Staatliche_Dienste:Fax>
                            <Staatliche_Dienste:Email>info@dfh-ufa.org</Staatliche_Dienste:Email>
                            <Staatliche_Dienste:Schulform>Hochschule</Staatliche_Dienste:Schulform>
                            <Staatliche_Dienste:Homepage>https://www.dfh-ufa.org/</Staatliche_Dienste:Homepage>
                            <Staatliche_Dienste:Schulregio>Saarbrücken</Staatliche_Dienste:Schulregio>
                            <Staatliche_Dienste:KARTENERST>Hochschule</Staatliche_Dienste:KARTENERST>
                            <Staatliche_Dienste:Rechtswert>355942.97630000</Staatliche_Dienste:Rechtswert>
                            <Staatliche_Dienste:Hochwert>5456095.93600000</Staatliche_Dienste:Hochwert>
                            <Staatliche_Dienste:Aktualisie>20.05.2025</Staatliche_Dienste:Aktualisie>
                        </Staatliche_Dienste:Schulen_SL>
                    </wfs:member>
                </wfs:FeatureCollection>
            """

        spider = SaarlandSpider()
        response = TextResponse(url="https://test.com", body=xml_response, encoding="utf-8")
        schools = list(spider.parse(response))
        self.assertEqual(len(schools), 1)

        school = schools[0]

        self.assertEqual(school["OBJECTID"], "1")
        self.assertEqual(school["fid"], "1.00000000")
        self.assertEqual(school["Gemeindenu"], "1100.00000000")
        self.assertEqual(school["PLZ"], "66123")
        self.assertEqual(school["Ort"], "Saarbrücken")
        self.assertEqual(school["Straße"], "Kohlweg 7")
        self.assertEqual(school["Bezeichnun"], "Deutsch-Französiche Hochschule, Université franco-allemande")
        self.assertEqual(school["Telefon"], "0681-93812100")
        self.assertEqual(school["Fax"], "0681-93812111")
        self.assertEqual(school["Email"], "info@dfh-ufa.org")
        self.assertEqual(school["Schulform"], "Hochschule")
        self.assertEqual(school["Homepage"], "https://www.dfh-ufa.org/")
        self.assertEqual(school["Schulregio"], "Saarbrücken")
        self.assertEqual(school["KARTENERST"], "Hochschule")
        self.assertEqual(school["Rechtswert"], "355942.97630000")
        self.assertEqual(school["Hochwert"], "5456095.93600000")
        self.assertEqual(school["Aktualisie"], "20.05.2025")
        self.assertAlmostEqual(school["lat"], 49.24067452)
        self.assertAlmostEqual(school["lon"], 7.02085050)


if __name__ == "__main__":
    unittest.main()
