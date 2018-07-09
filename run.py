import json
import sys
import wget
import xlrd
from xlrd import open_workbook
import requests
from lxml import etree

from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings

from jedeschule.spiders.bayern2 import Bayern2Spider
from jedeschule.spiders.bremen import BremenSpider
from jedeschule.spiders.brandenburg import BrandenburgSpider
from jedeschule.spiders.niedersachsen import NiedersachsenSpider
from jedeschule.spiders.nrw import NRWSpider
from jedeschule.spiders.sachsen import SachsenSpider
from jedeschule.spiders.sachsen_anhalt import SachsenAnhaltSpider
from jedeschule.spiders.thueringen import ThueringenSpider
from jedeschule.spiders.schleswig_holstein import SchleswigHolsteinSpider
from jedeschule.spiders.berlin import BerlinSpider


configure_logging()
settings = get_project_settings()
runner = CrawlerRunner(settings)

url_mv = 'https://www.regierung-mv.de/serviceassistent/download?id=1599568'

def get_hamburg():
    url = 'https://geoportal-hamburg.de/geodienste_hamburg_de/HH_WFS_Schulen?REQUEST=GetFeature&SERVICE=WFS&SRSNAME=EPSG%3A25832&TYPENAME=staatliche_schulen&VERSION=1.1.0&outpuFormat=application/json'
    r = requests.get(url)
    r.encoding = 'utf-8'
    elem = etree.fromstring(r.content)
    data = []
    for member in elem:
        data_elem = {}
        for attr in member[0]:
            data_elem[attr.tag.split('}', 1)[1]] = attr.text
        data.append(data_elem)
    print('Parsed ' + str(len(data)) + ' data elements')
    with open('data/hamburg.json', 'w') as json_file:
        json_file.write(json.dumps(data))


def get_mv():
    url_mv = 'https://www.regierung-mv.de/serviceassistent/download?id=1599568'
    wget.download(url_mv, 'mv.xls')
    workbook = xlrd.open_workbook('mv.xls')
    sheets = ['Schulverzeichnis öffentl. ABS', 'Schulverzeichnis öffentl. BLS','Schulverzeichnis freie ABS']

    legend = {
        'schulart': {
            'Agy': 'Abendgymnasium',
            'FöL': 'Schule mit dem Förderschwerpunkt Lernen',
            'FöS': 'Schule mit dem Förderschwerpunkt Sehen',
            'FöSp': 'Schule mit dem Förderschwerpunkt Sprache',
            'FöK': 'Schule mit dem Förderschwerpunkt körperliche und motorische Entwicklung',
            'FöK/GS': 'Schule mit dem Förderschwerpunkt körperliche und motorische Entwicklung mit Grundschule',
            'FöG': 'Schule mit dem Förderschwerpunkt geistige Entwicklung',
            'FöKr': 'Schule mit dem Förderschwerpunkt Unterricht kranker Schülerinnen und Schüler',
            'FöL/FöG': 'Schule mit dem Förderschwerpunkt Lernen und  dem Förderschwerpunkt geistige Entwicklung',
            'FöV': 'Schule mit dem Förderschwerpunkt emotionale und soziale Entwicklung',
            'FöV/FöKr': 'Schule mit dem Förderschwerpunkt emotionale und soziale Entwicklung und dem Förderschwerpunkt Unterricht kranker Schülerinnen und Schüler',
            'FöV/FöL': 'Schule mit dem Förderschwerpunkt emotionale und soziale Entwicklung und dem Förderschwerpunkt Lernen)',
            'FöL/FöV/FöKr': 'Schule mit den Förderschwerpunkten Lernen, dem Förderschwerpunkt emotionale und soziale Entwicklung sowie dem Förderschwerpunkt Unterricht kranker Schülerinnen und Schüler',
            'FöH': 'Schule mit dem Förderschwerpunkt Hören',
            'GS': 'Grundschule',
            'GS/OS': 'Grundschule mit schulartunabhängiger Orientierungsstufe',
            'GS/FöSp': 'Grundschule mit selbstständigen Klassen mit dem Förderschwerpunkt Sprache',
            'GS/OS/Gy': 'Grundschule mit schulartunabhängiger Orientierungsstufe und Gymnasium',
            'Gy': 'Gymnasium',
            'Gy/GS/OS': 'Gymnasium mit Grundschule und schulartunabhängiger Orientierungsstufe',
            'Gy/RegS/GS': 'Gymnasium mit Regionaler Schule und Grundschule',
            'IGS': 'Integrierte Gesamtschule',
            'IGS/GS': 'Integrierte Gesamtschule mit Grundschule',
            'IGS/GS/FöG': 'Integrierte Gesamtschule mit Grundschule  und Schule mit dem Förderschwerpunkt geistige Entwicklung',
            'KGS': 'Kooperative Gesamtschule',
            'KGS/GS': 'Kooperative Gesamtschule mit Grundschule',
            'KGS/GS/\nFöL': 'Kooperative Gesamtschule mit Grundschule und Schule mit dem Förderschwerpunkt Lernen',
            'RegS': 'Regionale Schule',
            'RegS/GS': 'Regionale Schule mit Grundschule',
            'RegS/Gy': 'Regionale Schule mit Gymnasium',
            'WS': 'Waldorfschule'
        },
        'schulamt': {
            'GW': 'Greifswald',
            'NB': 'Neubrandenburg',
            'RO': 'Rostock',
            'SN': 'Schwerin'
        },
        'landkreis': {
            'HRO': 'Hansestadt Rostock',
            'SN': 'Landeshauptstadt Schwerin',
            'LRO': 'Landkreis Rostock',
            'LUP': 'Landkreis Ludwigslust-Parchim',
            'MSE': 'Landkreis Mecklenburgische Seenplatte',
            'NWM': 'Landkreis Nordwestmecklenburg',
            'VG': 'Landkreis Vorpommern-Greifswald',
            'VR': 'Landkreis Vorpommern-Rügen'
        }
    }
    data = []
    for sheet in sheets:
        worksheet = workbook.sheet_by_name(sheet)
        keys = [v.value for v in worksheet.row(0)]
        for row_number in range(worksheet.nrows):
            if row_number == 0:
                continue
            row_data = {}
            for col_number, cell in enumerate(worksheet.row(row_number)):
                row_data[keys[col_number]] = cell.value
            if (row_data['Schulname'] != ''):
                row_data['Staatl. Schulamt'] = legend['schulamt'][row_data['Staatl. Schulamt']]
                row_data['Landkreis/ kreisfr. Stadt'] = legend['landkreis'][row_data['Landkreis/ kreisfr. Stadt']]
                if sheet != 'Schulverzeichnis öffentl. BLS':
                    row_data['Schulart/ Org.form'] = legend['schulart'][row_data['Schulart/ Org.form']]
                else:
                    row_data['Schulart/ Org.form'] = 'Berufliche Schule'
                data.append(row_data)

    with open('data/mecklenburg-vorpommern.json', 'w') as json_file:
        json_file.write(json.dumps(data))

@defer.inlineCallbacks
def crawl():
    yield runner.crawl(BremenSpider)
    yield runner.crawl(BrandenburgSpider)
    yield runner.crawl(Bayern2Spider)
    yield runner.crawl(NiedersachsenSpider)
    yield runner.crawl(NRWSpider)
    yield runner.crawl(SachsenSpider)
    yield runner.crawl(SachsenAnhaltSpider)
    yield runner.crawl(ThueringenSpider)
    yield runner.crawl(SchleswigHolsteinSpider)
    yield runner.crawl(BerlinSpider)
    reactor.stop()

crawl()
reactor.run() # the script will block here until the last crawl call is finished
get_mv()
get_hamburg()
