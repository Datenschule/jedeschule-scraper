import scrapy
from scrapy import Item
import wget
import xlrd
import json
import os
from jedeschule.items import School
import requests
from urllib.parse import urljoin
from io import StringIO
import csv
from lxml import etree

# [2020-12-05, htw-kevkev]
#   Created separate nw scraper for harmonization and to normalize data via school pipeline

class NordrheinWestfalenSpider(scrapy.Spider):
    name = "nordrhein-westfalen"
    base_url = 'https://www.schulministerium.nrw.de/BiPo/OpenData/Schuldaten/'
    start_urls = ['https://www.schulministerium.nrw.de']

    def parse(self, response):
        # get Schulbetriebssschluessel
        r = requests.get(urljoin(self.base_url, 'key_schulbetriebsschluessel.csv'))
        r.encoding = 'utf-8'
        sio = StringIO(r.content.decode('utf-8'))
        sb_csv = csv.reader(sio, delimiter=';')
        # Skip the first two lines
        next(sb_csv)
        next(sb_csv)
        schulbetrieb = {row[0]: row[1] for row in sb_csv}

        # get Schulformschluessel
        r = requests.get(urljoin(self.base_url, 'key_schulformschluessel.csv'))
        r.encoding = 'utf-8'
        sio = StringIO(r.content.decode('utf-8'))
        sb_csv = csv.reader(sio, delimiter=';')
        # Skip the first two lines
        next(sb_csv)
        next(sb_csv)
        schulform = {row[0]: row[1] for row in sb_csv}

        # get rechtsform
        r = requests.get(urljoin(self.base_url, 'key_rechtsform.csv'))
        r.encoding = 'utf-8'
        sio = StringIO(r.content.decode('utf-8'))
        sb_csv = csv.reader(sio, delimiter=';')
        # Skip the first two lines
        next(sb_csv)
        next(sb_csv)
        rechtsform = {row[0]: row[1] for row in sb_csv}

        # get schuelerzahl
        r = requests.get(urljoin(self.base_url, 'SchuelerGesamtZahl/anzahlen.csv'))
        r.encoding = 'utf-8'
        sio = StringIO(r.content.decode('utf-8'))
        sb_csv = csv.reader(sio, delimiter=';')
        # Skip the first two lines
        next(sb_csv)
        next(sb_csv)
        schuelerzahl = {row[0]: row[1] for row in sb_csv}

        # get traeger
        r = requests.get(urljoin(self.base_url, 'key_traeger.xml'))
        r.encoding = 'utf-8'
        elem = etree.fromstring(r.content)
        traeger_raw = []
        for member in elem:
            data_elem = {}
            for attr in member:
                data_elem[attr.tag] = attr.text
            traeger_raw.append(data_elem)
        traeger = {x['Traegernummer']: x for x in traeger_raw}


        r = requests.get(urljoin(self.base_url, 'schuldaten.xml'))
        r.encoding = 'utf-8'
        elem = etree.fromstring(r.content)
        data = []
        for member in elem:
            data_elem = {}

            for attr in member:
                data_elem[attr.tag] = attr.text

                if attr.tag == 'Schulnummer':
                    data_elem['Schuelerzahl'] = schuelerzahl.get(attr.text)

                if attr.tag == 'Schulbetriebsschluessel':
                    data_elem['Schulbetrieb'] = schulbetrieb[attr.text]

                if attr.tag == 'Schulform':
                    data_elem['Schulformschluessel'] = attr.text
                    data_elem['Schulform'] = schulform[attr.text]

                if attr.tag == 'Rechtsform':
                    data_elem['Rechtsformschluessel'] = attr.text
                    data_elem['Rechtsform'] = rechtsform[attr.text]

                if attr.tag == 'Traegernummer':
                    data_elem['Traeger'] = traeger.get(attr.text)

            data.append(data_elem)


        for row in data:
            yield row

    @staticmethod
    def normalize(item: Item) -> School:
        schoolname = item.get('Schulbezeichnung_1')+' '+item.get('Schulbezeichnung_2')+' '+ item.get('Schulbezeichnung_3')

        schoolfax = ''
        if item.get('Faxvorwahl') and item.get('Fax'):
            schoolfax = item.get('Faxvorwahl') + item.get('Fax')

        schoolphone = ''
        if item.get('Telefonvorwahl') and item.get('Telefon'):
            schoolphone = item.get('Telefonvorwahl') + item.get('Telefon')

        legal = 'öffentlich'
        if 'privat' in item.get('Rechtsform'):
            legal = 'privat'

        schoolprovider = item.get('Traeger').get('Traegerbezeichnung_1')+' '+item.get('Traeger').get('Traegerbezeichnung_2')+' '+item.get('Traeger').get('Traegerbezeichnung_3')

        return School(name=schoolname.strip(),
                      id='NW-{}'.format(item.get('Schulnummer')),
                      address=item.get('Strasse'),
                      address2='',
                      zip=item.get('PLZ'),
                      city=item.get('Ort'),
                      website=item.get('Homepage'),
                      email=item.get('E-Mail'),
                      school_type=item.get('Schulform'),
                      fax=schoolfax.strip(),
                      phone=schoolphone.strip(),
                      provider=schoolprovider.strip(),
                      legal_status = legal,
                      director='')
