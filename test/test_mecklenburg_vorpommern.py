import unittest

from scrapy.http import TextResponse

from jedeschule.spiders.mecklenburg_vorpommern import MecklenburgVorpommernSpider


class TestMecklenburgVorpommernSpider(unittest.TestCase):
    def test_parse(self):
        xml_response = """<?xml version='1.0' encoding="UTF-8" ?>
<wfs:FeatureCollection
   xmlns:ms="http://mapserver.gis.umn.edu/mapserver"
   xmlns:gml="http://www.opengis.net/gml/3.2"
   xmlns:wfs="http://www.opengis.net/wfs/2.0"
   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
   xsi:schemaLocation="http://mapserver.gis.umn.edu/mapserver https://www.geodaten-mv.de/dienste/schulstandorte_wfs?SERVICE=WFS&amp;VERSION=2.0.0&amp;REQUEST=DescribeFeatureType&amp;TYPENAME=ms:schultyp_grund,ms:schultyp_regional,ms:schultyp_gymnasium,ms:schultyp_gesamt,ms:schultyp_waldorf,ms:schultyp_foerder,ms:schultyp_abendgym,ms:schultyp_berufs&amp;OUTPUTFORMAT=application%2Fgml%2Bxml%3B%20version%3D3.2 http://www.opengis.net/wfs/2.0 http://schemas.opengis.net/wfs/2.0/wfs.xsd http://www.opengis.net/gml/3.2 http://schemas.opengis.net/gml/3.2.1/gml.xsd"
   timeStamp="2025-10-10T15:56:47" numberMatched="unknown" numberReturned="1"
   next="https://www.geodaten-mv.de/dienste/schulstandorte_wfs?SERVICE=WFS&amp;REQUEST=GetFeature&amp;VERSION=2.0.0&amp;srsname=EPSG%3A4326&amp;typeNames=ms%3Aschultyp_grund%2Cms%3Aschultyp_regional%2Cms%3Aschultyp_gymnasium%2Cms%3Aschultyp_gesamt%2Cms%3Aschultyp_waldorf%2Cms%3Aschultyp_foerder%2Cms%3Aschultyp_abendgym%2Cms%3Aschultyp_berufs&amp;count=1&amp;STARTINDEX=1">
    <wfs:boundedBy>
        <gml:Envelope srsName="urn:ogc:def:crs:EPSG::4326">
            <gml:lowerCorner>53.846900 11.977407</gml:lowerCorner>
            <gml:upperCorner>53.846900 11.977407</gml:upperCorner>
        </gml:Envelope>
    </wfs:boundedBy>
    <!-- WARNING: No featureid defined for typename 'schultyp_grund'. Output will not validate. -->
    <wfs:member>
        <ms:schultyp_grund>
            <gml:boundedBy>
                <gml:Envelope srsName="urn:ogc:def:crs:EPSG::4326">
                    <gml:lowerCorner>53.846900 11.977407</gml:lowerCorner>
                    <gml:upperCorner>53.846900 11.977407</gml:upperCorner>
                </gml:Envelope>
            </gml:boundedBy>
            <ms:msGeometry>
                <gml:Point gml:id=".1" srsName="urn:ogc:def:crs:EPSG::4326">
                    <gml:pos>53.846900 11.977407</gml:pos>
                </gml:Point>
            </ms:msGeometry>
            <ms:orgform>Grundschule</ms:orgform>
            <ms:schultraeger></ms:schultraeger>
            <ms:rechtsstatus>Öffentlich</ms:rechtsstatus>
            <ms:schulname>Grundschule und Freizeithaus am Schloßplatz   </ms:schulname>
            <ms:strassehnr>Schloßplatz 3</ms:strassehnr>
            <ms:plz>18246</ms:plz>
            <ms:ort>Bützow</ms:ort>
            <ms:besonderheiten></ms:besonderheiten>
            <ms:schulleiter>Frau Beuster</ms:schulleiter>
            <ms:telefon>038461 - 52006</ms:telefon>
            <ms:emailadresse>schulleitung1108@hotmail.de</ms:emailadresse>
            <ms:internet></ms:internet>
            <ms:anzahl_klassen>12</ms:anzahl_klassen>
            <ms:anzahl_schueler>247</ms:anzahl_schueler>
            <ms:strasse>Schloßplatz</ms:strasse>
            <ms:hnr>3</ms:hnr>
            <ms:dstnr>75135304</ms:dstnr>
        </ms:schultyp_grund>
    </wfs:member>
</wfs:FeatureCollection>"""

        spider = MecklenburgVorpommernSpider()
        response = TextResponse(url="https://test.com", body=xml_response, encoding="utf-8")
        schools = list(spider.parse(response))
        self.assertEqual(len(schools), 1)

        school = schools[0]
        parsed_school = spider.normalize(school)

        self.assertEqual(parsed_school["id"], "MV-75135304")
        self.assertEqual(parsed_school["name"], "Grundschule und Freizeithaus am Schloßplatz")
        self.assertEqual(parsed_school["address"], "Schloßplatz 3")
        self.assertEqual(parsed_school["city"], "Bützow")
        self.assertEqual(parsed_school["school_type"], "Grundschule")
        self.assertEqual(parsed_school["zip"], "18246")
        self.assertEqual(parsed_school["latitude"], 53.846900)
        self.assertEqual(parsed_school["longitude"], 11.977407)
        self.assertEqual(parsed_school["legal_status"], "Öffentlich")
        self.assertEqual(parsed_school["director"], "Frau Beuster")
        self.assertEqual(parsed_school["phone"], "038461 - 52006")
        self.assertEqual(parsed_school["email"], "schulleitung1108@hotmail.de")
        self.assertEqual(parsed_school["website"], "")


if __name__ == "__main__":
    unittest.main()
