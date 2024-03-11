import time
import json

import scrapy
from scrapy import Item

from jedeschule.spiders.school_spider import SchoolSpider
from jedeschule.items import School


class BadenWuerttembergSpider(SchoolSpider):
    name = "baden-wuerttemberg"
    url = 'https://lobw.kultus-bw.de/didsuche/'
    start_urls = [url]

    # click the search button to return all results
    def parse(self, response):
        links_url = 'https://lobw.kultus-bw.de/didsuche/DienststellenSucheWebService.asmx/SearchDienststellen'
        timestamp = str(int(time.time())) 
        body = {"command":"QUICKSEARCH",
                    "data":{
                        "dscSearch":"",
                        "dscPlz":"",
                        "dscOrt":"",
                        "dscDienststellenname":"",
                        "dscSchulartenSelected":"",
                        "dscSchulstatusSelected":"",
                        "dscSchulaufsichtSelected":"",
                        "dscOrtSelected":"",
                        "dscEntfernung":"",
                        "dscAusbildungsSchulenSelected":"",
                        "dscAusbildungsSchulenSelectedSart":"",
                        "dscPageNumber":"1",
                        "dscPageSize":"10000",                    # crawl at least the number of existing schools
                        "dscUnique":timestamp
                        }
                }
        payload = json.dumps({'json':str(body)})
        req = scrapy.Request(links_url,
                    method='POST',
                    body=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Host":"lobw.kultus-bw.de",
                        "Connection":"keep-alive",
                        "Accept":"application/json, text/javascript, */*; q=0.01",
                        "Origin":"https://lobw.kultus-bw.de",
                        "Referer":"https://lobw.kultus-bw.de/didsuche/"
                       },
                    callback=self.parse_schoolist)
        yield req

    # go on each schools details side
    def parse_schoolist(self, response):
        school_data_url = 'https://lobw.kultus-bw.de/didsuche/DienststellenSucheWebService.asmx/GetDienststelle'
        items = json.loads(json.loads(response.text)['d'])['Rows']
        for item in items:
            disch = item['DISCH'][1:-1]  # remove ''
            payload = json.dumps({'disch':disch})
            req = scrapy.Request(school_data_url,
                        method='POST',
                        body=payload,
                        headers={
                            "Content-Type": "application/json",
                            "Host":"lobw.kultus-bw.de",
                            "Connection":"keep-alive",
                            "Accept":"application/json, text/javascript, */*; q=0.01",
                            "Origin":"https://lobw.kultus-bw.de",
                            "Referer":"https://lobw.kultus-bw.de/didsuche/"
                        },
                        callback=self.parse_school_data)
            yield req

    # get the information
    def parse_school_data(self, response):
        item = json.loads(json.loads(response.text)['d'])
        data = {
            'name'             : self.fix_data(item['NAME']), 
            'id'               : self.fix_data(item['DISCH']),
            'Strasse'          : self.fix_data(item['DISTR']),
            'PLZ'              : self.fix_data(item['PLZSTR']),
            'Ort'              : self.fix_data(item['DIORT']),
            'Telefon'          : self.fix_data(item['TELGANZ']), 
            'Fax'              : self.fix_data(item['FAXGANZ']), 
            'E-Mail'           : self.fix_data(item['VERWEMAIL']), 
            'Internet'         : self.fix_data(item['INTERNET']), 
            'Schulamt'         : self.fix_data(item['UEBERGEORDNET']),
            'Schulamt_Website' : self.fix_data(item['UEBERGEORDNET_INTERNET']),
            'Kreis'            : self.fix_data(item['KREISBEZEICHNUNG']),
            'Schulleitung'     : self.fix_data(item['SLFAMVOR']),
            'Schulträger'      : self.fix_data(item['STR_KURZ_BEZEICHNUNG']),
            'Postfach'         : self.fix_data(item['PFACH']),
            'PLZ_Postfach'     : self.fix_data(item['PLZPFACH']),
            'Schueler'         : item['SCHUELER'],
            'Klassen'          : item['KLASSEN'],
            'Lehrer'           : item['LEHRER'],
        }
        yield data

    # fix wrong tabs, spaces and new lines
    def fix_data(self, string):
        if string:
            string = ' '.join(string.split())
            string.replace('\n', '')
        return string

    def normalize(self, item: Item) -> School:
        return School(name=item.get('name'),
                      id='BW-{}'.format(item.get('id')),
                      address=item.get('Strasse'),
                      zip=item.get('PLZ'),
                      city=item.get('Ort'),
                      website=item.get('Internet'),
                      email=item.get('E-Mail'),
                      fax=item.get('Fax'),
                      phone=item.get('Telefon'),
                      provider=item.get('Schulamt'),
                      director=item.get('Schulleitung'),
                      school_type='')    