from scrapy import Item, Request
from scrapy.spiders import CrawlSpider

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider
from jedeschule.wfs_basic_parsers import parse_geojson_features

school_types = {
    'BEA': 'BEA',  # I could not find the meaning of this abbreviation
    'BBS': 'Berufsbildende Schule',
    'FWS': 'Freie Waldorfschule',
    'GHS': 'Grund- und Hauptschule (org. verbunden)',
    'GRS+': 'Grund- und Realschule plus (org. verbunden)',
    'GS': 'Grundschule',
    'GY': 'Gymnasium',
    'HS': 'Hauptschule',
    'IGS': 'Integrierte Gesamtschule',
    'Koll': 'Kolleg',
    'Koll/AGY': 'Kolleg und Abendgymnasium (org.verbunden)',
    'RS': 'Realschule',
    'RS+': 'Realschule plus',
    'RS+FOS': 'Realschule plus mit Fachoberschule',
    'StudSem': 'Studienseminar'

    # Förderschulen (special education schools) come in a variety of abbreviations
    # The following are some examples from the dataset
    # SFGLS, SFG, SFGM, SFE, SFL, SFLG, SFBLS, SFMG, SFLS
    # so we will treat them a bit differently, see below in the normalize step
}


class RheinlandPfalzSpider(CrawlSpider, SchoolSpider):
    name = "rheinland-pfalz"
    start_urls = [
        "https://www.geoportal.rlp.de/spatial-objects/350/collections/schulstandorte/items?&"
        "limit=1&"
        "f=html"
    ]

    # We have to first try and get a PHPSESSID. Only after that we are able to request schools as json
    def parse_start_url(self, response, **kwargs):
        json_url = (
            "https://www.geoportal.rlp.de/spatial-objects/350/collections/schulstandorte/items?"
            "limit=4000&"
            "f=json"
        )

        print("Requesting JSON after initial HTML load (cookies handled by Scrapy)")
        yield Request(json_url, callback=self.parse_json)

    @staticmethod
    def parse_json(response):
        yield from parse_geojson_features(response)

    def normalize(self, item: Item) -> School:
        email = item.get("mail", "").replace("(at)", "@").strip() or None
        school_type_raw = item.get("schulart")

        if school_type_raw:
            # special handling for special education schools
            if school_type_raw.startswith("SF"):
                school_type = "Förderschule"
            else:
                school_type = school_types.get(school_type_raw, school_type_raw)
        else:
            school_type = None

        return School(
            name=item.get("name"),
            id=f"RP-{item.get('identifikator')}",
            address=item.get("strasse"),
            city=item.get("schulort"),
            zip=item.get("plz"),
            latitude=item.get("lat"),
            longitude=item.get("lon"),
            website=None,
            email=email,
            provider=None,
            fax=None,
            phone=item.get("telefon"),
            school_type=school_type,
        )
