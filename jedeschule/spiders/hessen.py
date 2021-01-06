# -*- coding: utf-8 -*-
"""
Created on Tue Dec  8 14:58:47 2020

@author: Ioannis
"""
import scrapy
import copy
import re
from lxml import html
from scrapy import Item
from jedeschule.items import School


class HessenSpider(scrapy.Spider):
    name = "hessen"
    
    start_urls = ['https://schul-db.bildung.hessen.de/schul_db.html']
    
        
    def parse(self, response):
        search_page = html.fromstring(response.text)
        
        school_types = search_page.xpath('//select[@id="id_school_type"]/option/@value')

        form = {
            'school_name' : '',
            'school_town' : '',
            'school_zip' : '',
            'school_number' : '',
            'csrfmiddlewaretoken' : search_page.xpath('//input[@name="csrfmiddlewaretoken"]/@value'),
            'submit_hesse' : 'Hessische+Schule+suchen+...'
        }
        
        for school_type in school_types:
            form['school_type'] = school_type
            
            yield scrapy.FormRequest( self.start_urls[0], formdata = form, callback = self.parse_list)


    def parse_list(self, response):
        schools = copy.deepcopy(html.fromstring(response.text).xpath('//tbody/tr/td/a/@href'))
        
        for school in schools:
            yield scrapy.Request(school, callback = self.parse_details)
    
    def parse_details(self, response):
        details_page = html.fromstring(response.text)
        
        contact_text_nodes = details_page.xpath('//pre/text()')
        adress = contact_text_nodes[0].split('\n')
        
        matches = re.search(r"(\d+) (.+)", adress[3])
        
        school = {
            'name' : adress[1],
            'straße' : adress[2],
            'ort' : matches.group(2),
            'plz' : matches.group(1),
        }
        
        for text_node in contact_text_nodes:
            if "Fax: " in text_node:
                school['fax'] = text_node.split('\n')[1].replace("Fax: ", "").strip()
        
        contact_links = details_page.xpath('//pre/a/@href')
        for link in contact_links:
            if "tel:" in link:
                school['telefon'] = link.replace("tel:", "")
                
            if "http" in link:
                school['homepage'] = link
                
        school['schultyp'] = details_page.xpath('//main//div[@class="col-md-9 col-lg-9"]/text()')[0].replace("\n", "").strip()
        school['id'] = response.request.url.split("=")[-1]
        
        yield school
        
    @staticmethod
    def normalize(item: Item) -> School:
        return School(name = item.get('name'),
                      phone = item.get('telefon'),
                      website = item.get('homepage'),
                      address = item.get('straße'),
                      city = item.get('ort'),
                      zip = item.get('plz'),
                      id = 'HE-{}'.format(item.get('id')))