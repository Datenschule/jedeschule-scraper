#!/usr/bin/env python
# -*- coding: utf-8 -*-
import csv
import json
import os
from io import StringIO
from urllib.parse import urljoin

import wget
import xlrd
import requests
from lxml import etree

from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings

from jedeschule.spiders.bayern import BayernSpider
from jedeschule.spiders.bremen import BremenSpider
from jedeschule.spiders.brandenburg import BrandenburgSpider
from jedeschule.spiders.hamburg import HamburgSpider
from jedeschule.spiders.niedersachsen import NiedersachsenSpider
from jedeschule.spiders.sachsen import SachsenSpider
from jedeschule.spiders.sachsen_anhalt import SachsenAnhaltSpider
from jedeschule.spiders.thueringen import ThueringenSpider
from jedeschule.spiders.schleswig_holstein import SchleswigHolsteinSpider
from jedeschule.spiders.berlin import BerlinSpider
from jedeschule.spiders.rheinland_pfalz import RheinlandPfalzSpider
from jedeschule.spiders.mecklenburg_vorpommern import MecklenburgVorpommernSpider

configure_logging()
settings = get_project_settings()
runner = CrawlerRunner(settings)


def __retrieve_keys(url):
    r = requests.get(url)
    r.encoding = 'utf-8'

    sio = StringIO(r.content.decode('utf-8'))
    sb_csv = csv.reader(sio, delimiter=';')

    # Skip the first two lines
    next(sb_csv)
    next(sb_csv)

    result = {row[0]: row[1] for row in sb_csv}
    return result


def __retrieve_xml(url):
    r = requests.get(url)
    r.encoding = 'utf-8'
    elem = etree.fromstring(r.content)
    data = []
    for member in elem:
        data_elem = {}
        for attr in member:
            data_elem[attr.tag] = attr.text

        data.append(data_elem)

    return data


def get_nrw():
    base_url_nrw = 'https://www.schulministerium.nrw.de/BiPo/OpenData/Schuldaten/'

    schulbetrieb = __retrieve_keys(urljoin(base_url_nrw, 'key_schulbetriebsschluessel.csv'))
    schulform = __retrieve_keys(urljoin(base_url_nrw, 'key_schulformschluessel.csv'))
    rechtsform = __retrieve_keys(urljoin(base_url_nrw, 'key_rechtsform.csv'))
    schuelerzahl = __retrieve_keys(urljoin(base_url_nrw, 'SchuelerGesamtZahl/anzahlen.csv'))

    traeger_raw = __retrieve_xml(urljoin(base_url_nrw, 'key_traeger.xml'))
    traeger = {x['Traegernummer']: x for x in traeger_raw}

    r = requests.get(urljoin(base_url_nrw, 'schuldaten.xml'))
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
    print('Parsed ' + str(len(data)) + ' data elements')
    with open('data/nrw.json', 'w', encoding='utf-8') as json_file:
        json_file.write(json.dumps(data))

@defer.inlineCallbacks
def crawl():
    yield runner.crawl(BremenSpider)
    yield runner.crawl(BrandenburgSpider)
    yield runner.crawl(BayernSpider)
    yield runner.crawl(HamburgSpider)
    yield runner.crawl(NiedersachsenSpider)
    yield runner.crawl(SachsenSpider)
    yield runner.crawl(SachsenAnhaltSpider)
    yield runner.crawl(ThueringenSpider)
    yield runner.crawl(SchleswigHolsteinSpider)
    yield runner.crawl(BerlinSpider)
    yield runner.crawl(RheinlandPfalzSpider)
    yield runner.crawl(MecklenburgVorpommernSpider)
    reactor.stop()


if __name__ == '__main__':
    crawl()
    reactor.run()  # the script will block here until the last crawl call is finished
    get_nrw()
