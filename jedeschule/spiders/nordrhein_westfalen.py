from csv import DictReader

from scrapy import Item

from jedeschule.spiders.nordrhein_westfalen_helper import NordRheinWestfalenHelper
from jedeschule.spiders.school_spider import SchoolSpider
from jedeschule.items import School

# for an overview of the data provided by the State of
# Nordrhein-Westfalen, check out the overview page here:
# https://www.schulministerium.nrw.de/ministerium/open-government/offene-daten


class NordrheinWestfalenSpider(SchoolSpider):
    name = 'nordrhein-westfalen'

    start_urls = [
        'https://www.schulministerium.nrw.de/BiPo/OpenData/Schuldaten/schuldaten.csv',
    ]

    def parse(self, response):
        # TODO: This data provider actually provides coordinate values that
        # we can use at a later point. Extract them from here so that we don't
        # have to fall back to geocoding

        body = response.body.decode('utf-8').splitlines()
        # skip the first line which contains information about the separator
        reader = DictReader(body[1:], delimiter=';')
        for line in reader:
            yield line

    @staticmethod
    def normalize(item: Item) -> School:
        name = " ".join([item.get("Schulbezeichnung_1", ""),
                         item.get("Schulbezeichnung_2", ""),
                         item.get("Schulbezeichnung_3", "")])
        helper = NordRheinWestfalenHelper()
        return School(name=name,
                      id='NW-{}'.format(item.get('Schulnummer')),
                      address=item.get('Strasse'),
                      zip=item.get("PLZ"),
                      city=item.get('Ort'),
                      website=item.get('Homepage'),
                      email=item.get('E-Mail'),
                      legal_status=helper.resolve('rechtsform', item.get('Rechtsform')),
                      school_type=helper.resolve('schulform', item.get('Schulform')),
                      fax=f"{item.get('Faxvorwahl')}{item.get('Fax')}",
                      phone=f"{item.get('Telefonvorwahl')}{item.get('Telefon')}")
