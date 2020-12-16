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
from jedeschule.spiders.nordrhein_westfalen import NordrheinWestfalenSpider

configure_logging()
settings = get_project_settings()
runner = CrawlerRunner(settings)

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
    yield runner.crawl(NordrheinWestfalenSpider)
    reactor.stop()


if __name__ == '__main__':
    crawl()
    reactor.run()  # the script will block here until the last crawl call is finished
