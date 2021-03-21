import json
import urllib

import scrapy
from scrapy import Item
from scrapy.http import Response

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class NiedersachsenSpider(SchoolSpider):
    name = 'niedersachsen'
    start_urls = ['https://schulen.nibis.de/search/advanced']

    def parse(self, response: Response):
        parts = [cookie.decode('utf-8').split("=") for cookie in response.headers.getlist('Set-Cookie')]
        headers = {part[0]: part[1].split(';')[0] for part in parts}
        xsrf = urllib.parse.unquote(headers.get('XSRF-TOKEN'))
        yield scrapy.Request(
            "https://schulen.nibis.de/school/search",
            method="POST",
            body="""{"type":"Advanced","eingabe":null,"filters":{"classifications":[],"lschb":["RLSB Braunschweig","RLSB Hannover","RLSB Lüneburg","RLSB Osnabrück"],"towns":[],"countys":[],"regions":[],"features":[],"bbs_classifications":[],"bbs_occupations":[],"bbs_orientations":[],"plz":0,"oeffentlich":"on","privat":"on"}}""",
            headers={
                'X-XSRF-TOKEN': xsrf,
                'X-Inertia': "true",
                'Content-Type': 'application/json;charset=utf-8',
            },
            callback=self.parse_list)

    def parse_list(self, response: Response):
        json_response = json.loads(response.body.decode('utf-8'))
        for school in json_response['props']['schools']:
            yield scrapy.Request(
                f"https://schulen.nibis.de/school/getInfo/{school.get('schulnr')}",
                callback=self.parse_details
            )

    def parse_details(self, response: Response):
        json_response = json.loads(response.body.decode('utf-8'))
        yield json_response

    @staticmethod
    def _get(dict_like, key, default):
        # This is almost like dict_like.get(key, default)
        # but it also returns default if the dictionary's
        # value for the key is `None`.
        # A regular `.get` would just return `None` there
        # as it only fills in if the key is not defined
        # at all.
        return dict_like.get(key) or default

    @staticmethod
    def normalize(item: Item) -> School:
        name = " ".join([item.get('schulname', ''),
                         item.get('namenszuatz', '')]).strip()
        address = item.get('sdb_adressen', [{}])[0]
        ort = address.get('sdb_ort', {})
        school_type = NiedersachsenSpider._get(item, 'sdb_art', {}).get('art')
        provider = NiedersachsenSpider._get(item, 'sdb_traeger', {}).get('name')
        return School(name=name,
                      phone=item.get('telefon'),
                      fax=item.get('fax'),
                      email=item.get('email'),
                      website=item.get('homepage'),
                      address=address.get('strasse'),
                      zip=ort.get('plz'),
                      city=ort.get('ort'),
                      school_type=school_type,
                      provider=provider,
                      legal_status=item.get("sdb_traegerschaft", {}).get('bezeichnung'),
                      id='NI-{}'.format(item.get('schulnr')))
