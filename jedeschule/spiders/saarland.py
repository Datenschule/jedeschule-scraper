# -*- coding: utf-8 -*-
import copy
from scrapy import Item
from jedeschule.items import School
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from lxml import html

# School types: Berufliche Schule, Erweitere Realschule, Förderschule, Freie Waldorfschule,
# Gemeinschatsschule, Grundschule, Gymnasium, Lyzeum, Realschule, Studienseminare

class SaarlandSpider(CrawlSpider):
    name = "saarland"
    # allowed_domains = ["www.saarland.de/4526.htm"]
    start_urls = ['https://www.saarland.de/mbk/DE/portale/bildungsserver/themen/schulen-und-bildungswege/schuldatenbank/_functions/Schulsuche_Formular.html']
    
    rules = (Rule(LinkExtractor(allow=(), restrict_xpaths=('//a[@class="forward button"]',)), callback="parse_start_url", follow= True),)
    
    def parse_start_url(self, response):
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
                    school["homepage"] = card_copy.xpath('//a[@target="_blank"]/text()')[0]

                if key == "e-mail" : 
                    school["e-mail"] = card_copy.xpath('//a[contains(@title, "E-Mail senden an:")]/@href')[0].strip("mailto:")

                if key != "homepage" and key != "e-mail" :
                    school[key] = info[index]
            
            #schools.append(school)
            yield school

    @staticmethod
    def normalize(item: Item) -> School:
        if item.get('homepage'):
            hp = item.get('homepage')
        else:
            hp = 'N.N.'

        if item.get('e-mail'):
            mail = item.get('e-mail')
        else:
            mail = 'N.N.'

        if item.get('telefon'):
            tel = item.get('telefon')
        else:
            tel = 'N.N.'

        if item.get('telefax'):
            fax = item.get('telefax')
        else:
            fax = 'N.N.'

        if item.get('schulleitung'):
            leitung = item.get('schulleitung')
        else:
            leitung = 'N.N.'

        return School(name=item.get('name'),
                      phone=tel,
                      fax=fax,
                      website=hp,
                      email=mail,
                      address=item.get('straße'),
                      city=item.get('ort'),
                      zip=item.get('plz'),
                      school_type=item.get('schultyp'),
                      director=leitung,
                      id='SL-{}'.format(tel.replace(" ", "-")))