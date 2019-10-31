import scrapy
from scrapy.shell import inspect_response
from jedeschule.utils import cleanjoin
import logging
import time
import json

class BadenWürttembergSpider(scrapy.Spider):
    name = "baden-württemberg"
    root_url = "https://www.statistik.rlp.de/"
    url = 'https://lobw.kultus-bw.de/didsuche/'
    start_urls = [
                  url,
                 ]

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
                        "dscPageSize":"1213",
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
        item = json.loads(json.loads(response.body_as_unicode())['d'])
        data = {
            'name'             : item['NAME'], 
            'id'               : item['DISCH'],
            'Strasse'          : item['DISTR'],
            'PLZ'              : item['PLZSTR'],
            'Ort'              : item['DIORT'],
            'Telefon'          : item['TELGANZ'], 
            'Fax'              : item['FAXGANZ'], 
            'E-Mail'           : item['VERWEMAIL'], 
            'Internet'         : item['INTERNET'], 
            'Schulamt'         : item['UEBERGEORDNET'],
            'Schulamt_Website' : item['UEBERGEORDNET_INTERNET'],
            'Kreis'            : item['KREISBEZEICHNUNG'],
            'Schulleitung'     : item['SLFAMVOR'],
            'Schulträger'      : item['STR_KURZ_BEZEICHNUNG'],
            'Postfach'         : item['PFACH'],
            'PLZ_Postfach'     : item['PLZPFACH'],
            'Schueler'         : item['SCHUELER'],
            'Klassen'          : item['KLASSEN'],
            'Lehrer'           : item['LEHRER'],
        }
        yield data