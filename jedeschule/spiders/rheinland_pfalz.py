from scrapy import Item
from scrapy.linkextractors import LinkExtractor
import re

from scrapy.spiders import CrawlSpider, Rule

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider

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
    # Note, one could also use the geo portal:
    # https://www.geoportal.rlp.de/spatial-objects/350/collections/schulstandorte/items?f=html&limit=4000
    start_urls = ["https://bildung.rlp.de/schulen"]
    rules = [
        Rule(
            LinkExtractor(allow="https://bildung.rlp.de/schulen/einzelanzeige.*"),
            callback="parse_school",
            follow=False,
        )
    ]

    # get the information
    def parse_school(self, response):
        container = response.css(".rlp-schooldatabase-detail")
        item = {"name": container.css("h1::text").get()}
        for row in container.css("tr"):
            key, value = row.css("td")
            value_parts = value.css("*::text").extract()
            cleaned = [part.strip() for part in value_parts]
            item[key.css("::text").extract_first().replace(":", "")] = (
                cleaned[0] if len(cleaned) == 1 else cleaned
            )
        item["id"] = item["Schulnummer"]

        osm_url = container.css('a[href*="openstreetmap"]::attr(href)').extract_first()
        *rest, lat, lon = osm_url.split("/")
        item["lat"] = lat
        item["lon"] = lon
        yield item

    def normalize(self, item: Item) -> School:
        zip, city = item.get("Anschrift")[-1].split(" ", 1)
        email = item.get("E-Mail", "").replace("(at)", "@")

        kurzbezeichnung = item.get('Kurzbezeichnung')
        if kurzbezeichnung:
            first_part = kurzbezeichnung.split(" ")[0]
            # special handling for special education schools
            if first_part.startswith('SF'):
                school_type = 'Förderschule'
            else:
                school_type = school_types.get(first_part, None)
        else:
            school_type = None

        return School(
            name=item.get("name"),
            id="RP-{}".format(item.get("id")),
            address=item.get("Anschrift")[1],
            city=city,
            zip=zip,
            latitude=item.get("lat"),
            longitude=item.get("lon"),
            website=item.get("Internet"),
            email=email,
            provider=item.get("Träger"),
            fax=item.get("Telefax"),
            phone=item.get("Telefon"),
            school_type=school_type
        )
