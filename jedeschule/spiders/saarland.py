# -*- coding: utf-8 -*-
import copy
from scrapy import Item
from jedeschule.items import School
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from lxml import html


class SaarlandSpider(CrawlSpider):
    name = "saarland"
    # allowed_domains = ["www.saarland.de/4526.htm"]
    start_url = 'https://www.saarland.de/mbk/DE/portale/bildungsserver/themen/schulen-und-bildungswege/schuldatenbank/_functions/Schulsuche_Formular.html?pageLocale=de&submit=Suchen&templateQueryString='
    schools = 'Grundschule+OR+Förderschule+OR+Gemeinschaftsschule+OR+Gymnasium+OR+"Berufliche+Schule"'
    start_urls = [start_url + schools]
    
    rules = (Rule(LinkExtractor(allow=(), restrict_xpaths=('//a[@class="forward button"]',)), callback="parse_page", follow= True),)
    
    def parse_page(self, response):
        #schools = []
        cards =  html.fromstring(response.text).xpath('//div[@class="c-teaser-card"]')
        
        for card in cards:
            card_copy = copy.deepcopy(card)           
            c_badge = card_copy.xpath('//span[@class="c-badge"]/text()')
            
            school = {}
            school["name"] = card_copy.xpath('//h3/text()')[0].strip("\n").strip()
            school["schultyp"] = c_badge[0]
            school["ort"] = c_badge[1]
            
            adress = card_copy.xpath('//p/text()')[0].split(", ")
            
            school["straße"] = adress[0]
            school["plz"] = adress[1].strip(" " + school['ort'])
            
            keys = card_copy.xpath('//dt/text()')
            info = card_copy.xpath('//dd/text()')
            
            for index in range(0, len(keys)):
                key = keys[index].strip(":").lower()
                
                if key == "homepage" :
                    school[key] = card_copy.xpath('//a[@target="_blank"]/text()')[0]
                elif key == "e-mail" : 
                    school[key] = card_copy.xpath('//a[contains(@title, "E-Mail senden an:")]/@href')[0].strip("mailto:")
                else:
                    school[key] = info[index]
            
            #schools.append(school)
            yield school
        
        
        
    @staticmethod
    def normalize(item: Item) -> School:
        return School(name=item.get('name'),
                      phone=item.get('telefon'),
                      website=item.get('homepage'),
                      address=item.get('straße'),
                      city=item.get('ort'),
                      zip=item.get('plz'),
                      id='SL-{' + item.get('telefon').replace(" ", "-") + '}')