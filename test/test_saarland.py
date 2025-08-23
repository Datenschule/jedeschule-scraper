import unittest

from scrapy.http import TextResponse

from jedeschule.spiders.saarland import SaarlandSpider


class TestSaarlandSpider(unittest.TestCase):
    def test_parse(self):
        json_response = """
    {
  "serviceTitle": "Staatliche_Dienste",
  "collectionId": "1125",
  "collectionName": "Staatliche_Dienste:Schulen_SL",
  "collectionTitle": "Schulen_SL",
  "title": "Schulen_SL",
  "id": "Staatliche_Dienste:Schulen_SL",
  "description": "Schulen im Saarland",
  "extent": {
    "spatial": {
      "minx": "6.37990222",
      "miny": "49.10626268",
      "maxx": "7.37397862",
      "maxy": "49.61541418"
    },
    "temporal": []
  },
  "type": "FeatureCollection",
  "links": [
    {
      "rel": "self",
      "type": "application/geo+json",
      "title": "this document",
      "href": "https://geoportal.saarland.de/spatial-objects/257/collections/Staatliche_Dienste:Schulen_SL/items?f=json&limit=2500"
    },
    {
      "rel": "next",
      "type": "application/geo+json",
      "title": "next page",
      "href": "https://geoportal.saarland.de/spatial-objects/257/collections/Staatliche_Dienste:Schulen_SL/items?f=json&limit=2500&offset=2500"
    },
    {
      "rel": "last",
      "type": "application/geo+json",
      "title": "last page",
      "href": "https://geoportal.saarland.de/spatial-objects/257/collections/Staatliche_Dienste:Schulen_SL/items?f=json&limit=2500&offset=0"
    }
  ],
  "numberMatched": 368,
  "numberReturned": 368,
  "timeStamp": "2025-08-20T12:21:36.7200Z",
  "genTime": 0.7143468856811523,
  "features": [
    {
      "type": "Feature",
      "properties": {
        "gml_id": "Schulen_SL.1",
        "OBJECTID": 1,
        "Gemeindenr": 1100,
        "PLZ": 66123,
        "Ort": "Saarbrücken",
        "Straße": "Kohlweg 7",
        "Bezeichnung": "Deutsch-Französiche Hochschule, Université franco-allemande",
        "Telefon": "0681-93812100",
        "Fax": "0681-93812111",
        "Email": "info@dfh-ufa.org",
        "Schulform": "Hochschule",
        "Homepage": "https://www.dfh-ufa.org/",
        "Schulregion": "Saarbrücken",
        "KARTENERST": "Hochschule",
        "Ost": 355942.9763,
        "Nord": 5456095.936,
        "ERFASSUNG": "20.05.2025"
      },
      "bbox": [
        7.0208505,
        49.24067452,
        7.0208505,
        49.24067452
      ],
      "geometry": {
        "type": "Point",
        "coordinates": [
          7.0208505,
          49.24067452
        ]
      },
      "$schema": null,
      "$context": null
    }
  ]
}
            """

        spider = SaarlandSpider()
        response = TextResponse(url="https://test.com", body=json_response, encoding="utf-8")
        schools = list(spider.parse(response))
        self.assertEqual(len(schools), 1)

        school = schools[0]
        parsed_school = spider.normalize(school)

        self.assertEqual(parsed_school["id"], "SL-1")
        self.assertEqual(parsed_school["name"], "Deutsch-Französiche Hochschule, Université franco-allemande")
        self.assertEqual(parsed_school["address"], "Kohlweg 7")
        self.assertEqual(parsed_school["city"], "Saarbrücken")
        self.assertEqual(parsed_school["fax"], "0681-93812111")
        self.assertEqual(parsed_school["phone"], "0681-93812100")
        self.assertEqual(parsed_school["school_type"], "Hochschule")
        self.assertEqual(parsed_school["website"], "https://www.dfh-ufa.org/")
        self.assertEqual(parsed_school["zip"], 66123)
        self.assertEqual(parsed_school["latitude"], 49.24067452)
        self.assertEqual(parsed_school["longitude"], 7.0208505)






if __name__ == "__main__":
    unittest.main()
