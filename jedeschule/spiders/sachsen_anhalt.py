# -*- coding: utf-8 -*-
import re

import scrapy
from scrapy.shell import inspect_response

import requests
import sys
from lxml import html


try:
    import HTMLParser # to parse content from HTML school-types
    from urlparse import parse_qs 
except ImportError: # for Python 3
    from html.parser import HTMLParser
    from urllib.parse import parse_qs 


class SachsenAnhaltSpider(scrapy.Spider):
    
    name = "sachsen-anhalt"
    detail_url = "https://www.bildung-lsa.de/ajax.php?m=getSSDetails&id={}&timestamp=1480082332787"
    

   # must return an iterable with the first Requests to crawl for this spider
    def start_requests(self):
        page = requests.get('https://www.bildung-lsa.de/schule.html')
        tree = html.fromstring(page.content)
        self.TYPES_DICT = {}

        options = tree.xpath('//form[@name="SSFORM"]/select[@name="sf"]/option') #content + id
        
        self.TYPES_DICT = dict([(o.get('value'), o.text.replace("nur ", "")) for o in options if o.get('value') != '-1'])

        for i in self.TYPES_DICT.keys():
            yield scrapy.Request('https://www.bildung-lsa.de/ajax.php?m=getSSResult&q=&lk=-1&sf='+str(i)+'&so=-1&timestamp=1480082332787')

        


    def parse(self, response):
        
        js_callbacks = response.css("span ::attr(onclick)").extract()
        pattern = "getSSResultItemDetail\((\d+)\)"
        ids = [re.match(pattern, text).group(1) for text in js_callbacks]
        names = response.css("b::text").extract()
        for id, name in zip(ids, names):
            #dontfilter = true : Gemeinschaftschulen sind Sekundarschulen (Sekundarschulen sind nicht immer Gemeinschaftschulen)
            request = scrapy.Request(self.detail_url.format(id), callback=self.parse_detail)
            
            request.meta['name'] = name.strip()
            #added ID
            request.meta['id'] = id.strip()

            args=parse_qs(response.url) #args=urlparse.parse_qs(response.url)

            match=args['sf'][0] 


            request.meta['schulform']=match.strip()
            yield request
            
            
    def parse_detail(self, response):
        tables = response.css("table")

        content = {}
        # Only the second and third table contain interesting data
        for table in tables[1:3]:
            trs = table.css("tr")
            for tr in trs:
                tds = tr.css("td")
                key = tds[0].css("::text").extract_first()[:-2]
                value = " ".join(tds[1].css("::text").extract())
                content[key] = value
        content['Name'] = response.meta['name']
        # The name is included in the "Adresse" field so we remove that
        # in order to get only the address
        content['Adresse'] = content['Adresse'].replace(response.meta['name'], "").strip()
        # Schulform + ID added
        content['official_id']=response.meta['id']
 
        # would also fill the school_type_entity 
        # content["school_type_entity"]=TYPES_DICT.get(response.meta['schulform'], 'n/a')
        content["school_type"]=self.TYPES_DICT.get(response.meta['schulform'], 'n/a')

        yield content