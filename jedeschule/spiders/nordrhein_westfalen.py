from csv import DictReader

from scrapy import Item
from pyproj import Transformer

from jedeschule.spiders.nordrhein_westfalen_helper import NordRheinWestfalenHelper
from jedeschule.spiders.school_spider import SchoolSpider
from jedeschule.items import School


# for an overview of the data provided by the State of
# Nordrhein-Westfalen, check out the overview page here:
# https://www.schulministerium.nrw.de/ministerium/open-government/offene-daten


class NordrheinWestfalenSpider(SchoolSpider):
    name = "nordrhein-westfalen"

    start_urls = [
        "https://www.schulministerium.nrw.de/BiPo/OpenData/Schuldaten/schuldaten.csv",
    ]

    def parse(self, response):
        body = response.body.decode("utf-8").splitlines()
        # skip the first line which contains information about the separator
        reader = DictReader(body[1:], delimiter=";")
        for line in reader:
            yield line

    @staticmethod
    def normalize(item: Item) -> School:
        name = " ".join(
            [
                item.get("Schulbezeichnung_1", ""),
                item.get("Schulbezeichnung_2", ""),
                item.get("Schulbezeichnung_3", ""),
            ]
        ).strip()
        helper = NordRheinWestfalenHelper()
        right, high = item.get("UTMRechtswert"), item.get("UTMHochwert")
        # There are some entries which have the string "null" in the EPSG
        # column. All others have "EPSG:25832". It seems save enough to assume
        # that this is a mistake in the data and should also be "EPSG:25832".
        source_crs = item.get("EPSG")
        if source_crs == 'null':
            source_crs = "EPSG:25832"
        transformer = Transformer.from_crs(source_crs, "EPSG:4326")
        lon, lat = transformer.transform(right, high)

        return School(
            name=name,
            id="NW-{}".format(item.get("Schulnummer")),
            address=item.get("Strasse"),
            zip=item.get("PLZ"),
            city=item.get("Ort"),
            website=item.get("Homepage"),
            email=item.get("E-Mail"),
            legal_status=helper.resolve("rechtsform", item.get("Rechtsform")),
            school_type=helper.resolve("schulform", item.get("Schulform")),
            provider=helper.resolve("provider", item.get("Traegernummer")),
            fax=f"{item.get('Faxvorwahl')}{item.get('Fax')}",
            phone=f"{item.get('Telefonvorwahl')}{item.get('Telefon')}",
            latitude=lat,
            longitude=lon,
        )
