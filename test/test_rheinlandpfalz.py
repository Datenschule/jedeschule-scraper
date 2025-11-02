import unittest

from scrapy.http import TextResponse

from jedeschule.spiders.rheinland_pfalz import RheinlandPfalzSpider


class TestRheinlandPfalzSpider(unittest.TestCase):
    def test_parse(self):
        json_response = """
    {
    "serviceTitle": "WFS zur Bereitstellung von Schulstandorten",
    "collectionId": "1435",
    "collectionName": "schulstandorte",
    "collectionTitle": "Standorte der Schulen in RLP",
    "title": "Standorte der Schulen in RLP",
    "id": "schulstandorte",
    "description": "",
    "extent": {
        "spatial": {
            "minx": "6",
            "miny": "48",
            "maxx": "8",
            "maxy": "51"
        },
        "temporal": []
    },
    "type": "FeatureCollection",
    "links": [
        {
            "rel": "self",
            "type": "application/geo+json",
            "title": "this document",
            "href": "https://www.geoportal.rlp.de/spatial-objects/350/collections/schulstandorte/items?limit=1&f=json"
        },
        {
            "rel": "next",
            "type": "application/geo+json",
            "title": "next page",
            "href": "https://www.geoportal.rlp.de/spatial-objects/350/collections/schulstandorte/items?limit=1&f=json&offset=1"
        },
        {
            "rel": "last",
            "type": "application/geo+json",
            "title": "last page",
            "href": "https://www.geoportal.rlp.de/spatial-objects/350/collections/schulstandorte/items?limit=1&f=json&offset=1628"
        }
    ],
    "numberMatched": 1629,
    "numberReturned": 1,
    "timeStamp": "2025-11-02T18:11:01.3600Z",
    "genTime": 0.3082730770111084,
    "features": [
        {
            "type": "Feature",
            "properties": {
                "gml_id": "schulstandorte.10148",
                "gid": "7",
                "identifikator": "10148",
                "name": "Grundschule Mainz-Lerchenberg",
                "strasse": "Hindemithstr. 1",
                "plz": "55127",
                "schulort": "Mainz",
                "telefon": "(06131)364660",
                "mail": "schule.gs-lerchenberg@stadt.mainz.de",
                "schulart": "GS",
                "anzahl": "2",
                "marker-size": "34",
                "marker-symbol": "marker",
                "marker-color": "#7e7e7e"
            },
            "bbox": [
                8.19553,
                49.95999,
                8.19553,
                49.95999
            ],
            "geometry": {
                "type": "MultiPoint",
                "coordinates": [
                    [
                        8.19553,
                        49.95999
                    ]
                ]
            },
            "$schema": null,
            "$context": null
        }
    ]
}
            """

        spider = RheinlandPfalzSpider()
        response = TextResponse(url="https://test.com", body=json_response, encoding="utf-8")
        schools = list(spider.parse_json(response))
        self.assertEqual(len(schools), 1)

        school = schools[0]
        parsed_school = spider.normalize(school)

        self.assertEqual(parsed_school["id"], "RP-10148")
        self.assertEqual(parsed_school["name"], "Grundschule Mainz-Lerchenberg")
        self.assertEqual(parsed_school["address"], "Hindemithstr. 1")
        self.assertEqual(parsed_school["city"], "Mainz")
        self.assertEqual(parsed_school["zip"], "55127")
        self.assertEqual(parsed_school["latitude"], 49.95999)
        self.assertEqual(parsed_school["longitude"], 8.19553)
        self.assertEqual(parsed_school["phone"], "(06131)364660")
        self.assertEqual(parsed_school["email"], "schule.gs-lerchenberg@stadt.mainz.de")
        self.assertEqual(parsed_school["school_type"], "Grundschule")
        self.assertIsNone(parsed_school["fax"])
        self.assertIsNone(parsed_school["website"])
        self.assertIsNone(parsed_school["provider"])



if __name__ == "__main__":
    unittest.main()
