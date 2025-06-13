import unittest

from scrapy.http import TextResponse, Request

from jedeschule.spiders.hamburg import HamburgSpider


class TestHamburgSpider(unittest.TestCase):

    def test_parse(self):
        xml_body = """
        <wfs:FeatureCollection xmlns:wfs="wfs"
            xmlns:gml="gml"
            xmlns:de.hh.up="de.hh.up">
            <gml:featureMember>
            <de.hh.up:nicht_staatliche_schulen xmlns:de.hh.up="https://registry.gdi-de.org/id/de.hh.up" gml:id="DE.HH.UP_NICHT_STAATLICHE_SCHULEN_863826">
                <de.hh.up:adresse_ort>22159 Hamburg</de.hh.up:adresse_ort>
                <de.hh.up:adresse_strasse_hausnr>Rahlstedter Weg 15</de.hh.up:adresse_strasse_hausnr>
                <de.hh.up:anzahl_schueler>417</de.hh.up:anzahl_schueler>
                <de.hh.up:anzahl_schueler_gesamt>417 an 1 Standort</de.hh.up:anzahl_schueler_gesamt>
                <de.hh.up:bezirk>Wandsbek</de.hh.up:bezirk>
                <de.hh.up:fax>+49 40 53 30 43-29</de.hh.up:fax>
                <de.hh.up:is_rebbz>true</de.hh.up:is_rebbz>
                <de.hh.up:kapitelbezeichnung>Grundschulen</de.hh.up:kapitelbezeichnung>
                <de.hh.up:lgv_standortk_erwachsenenbildung>No</de.hh.up:lgv_standortk_erwachsenenbildung>
                <de.hh.up:rebbz_homepage>http://rebbz-wandsbek-sued.hamburg.de/</de.hh.up:rebbz_homepage>
                <de.hh.up:rechtsform>staatlich anerkannte Ersatzschule</de.hh.up:rechtsform>
                <de.hh.up:schueleranzahl_schuljahr>2024</de.hh.up:schueleranzahl_schuljahr>
                <de.hh.up:schul_email>sekretariat@kath-schule-farmsen.kseh.de</de.hh.up:schul_email>
                <de.hh.up:schul_homepage>http://www.ksfhh.de</de.hh.up:schul_homepage>
                <de.hh.up:schul_id>3213-0</de.hh.up:schul_id>
                <de.hh.up:schul_telefonnr>+49 40 53 30 43-10</de.hh.up:schul_telefonnr>
                <de.hh.up:schulaufsicht>Berend Loges</de.hh.up:schulaufsicht>
                <de.hh.up:schulform>Grundschule|Vorschulklasse</de.hh.up:schulform>
                <de.hh.up:schulname>Katholische Schule Farmsen</de.hh.up:schulname>
                <de.hh.up:schultyp>Hauptstandort</de.hh.up:schultyp>
                <de.hh.up:sozialindex>Stufe 4</de.hh.up:sozialindex>
                <de.hh.up:stadtteil>Farmsen-Berne</de.hh.up:stadtteil>
                <de.hh.up:standort_id>451</de.hh.up:standort_id>
                <de.hh.up:zustaendiges_rebbz>ReBBZ Wandsbek-Süd</de.hh.up:zustaendiges_rebbz>
                <de.hh.up:the_geom>
                    <!--Inlined geometry 'DE.HH.UP_NICHT_STAATLICHE_SCHULEN_863826_DE.HH.UP_THE_GEOM'-->
                    <gml:Point gml:id="DE.HH.UP_NICHT_STAATLICHE_SCHULEN_863826_DE.HH.UP_THE_GEOM" srsName="EPSG:4326">
                        <gml:pos>10.121824 53.606715</gml:pos>
                    </gml:Point>
                </de.hh.up:the_geom>
            </de.hh.up:nicht_staatliche_schulen>
    </gml:featureMember>
        </wfs:FeatureCollection>
        """

        spider = HamburgSpider()
        response = TextResponse(
            url="https://test.com",
            request=Request(url="https://test.com"),
            body=xml_body,
            encoding="utf-8"
        )

        schools = list(spider.parse(response))
        self.assertEqual(len(schools), 1)

        school_in_hamburg = schools[0]
        self.assertEqual(school_in_hamburg["schulname"], "Katholische Schule Farmsen")
        self.assertEqual(school_in_hamburg["schul_id"], "3213-0")
        self.assertEqual(school_in_hamburg["adresse_strasse_hausnr"], "Rahlstedter Weg 15")
        self.assertEqual(school_in_hamburg["adresse_ort"], "22159 Hamburg")
        self.assertEqual(school_in_hamburg["schul_homepage"], "http://www.ksfhh.de")
        self.assertEqual(school_in_hamburg["schul_email"], "sekretariat@kath-schule-farmsen.kseh.de")
        self.assertEqual(school_in_hamburg["schulform"], "Grundschule|Vorschulklasse")
        self.assertEqual(school_in_hamburg["fax"], "+49 40 53 30 43-29")
        self.assertEqual(school_in_hamburg["schul_telefonnr"], "+49 40 53 30 43-10")
        self.assertEqual(school_in_hamburg["lat"], 53.606715)
        self.assertEqual(school_in_hamburg["lon"], 10.121824)


if __name__ == '__main__':
    unittest.main()
