# -*- coding: utf-8 -*-
import urllib.parse as urlparse
from typing import List
from urllib.parse import parse_qs
import scrapy
from scrapy.shell import inspect_response
from jedeschule.items import School
from scrapy import Item
import re


class BerlinSpider(scrapy.Spider):
    name = "berlin"
    # Potential errors of Berlin:
    # 502 with user agent = default (scrapy) -> use a real user agent like "jedeschule"
    # 429 with download delay = default -> set download delay to slow down scrapy
    # custom settings avoid other spiders from being affected of solving a spider individual problem
    custom_settings = {'USER_AGENT': 'jedeschule (open data project)', 'DOWNLOAD_DELAY': 1,}
    base_url = 'https://www.berlin.de/sen/bildung/schule/berliner-schulen/schulverzeichnis/'
    start_url = base_url + 'SchulListe.aspx'
    start_urls = [start_url]

    def parse(self, response):
        schools = response.css('td a::attr(href)').extract()
        for i, school in enumerate(schools):
            # school = school.replace(' ','')
            yield scrapy.Request(self.base_url + school, callback=self.parse_detail, meta={'cookiejar': i})

    def parse_detail(self, response):
        meta = {}
        name = response.css('#ContentPlaceHolderMenuListe_lblSchulname::text').extract_first().strip()#.rsplit('-', 1)
        meta['name'] = self.fix_data(name)
        meta['id'] = self._parse_school_no(response.url)
        meta['address'] = self.fix_data(response.css('#ContentPlaceHolderMenuListe_lblStrasse::text').extract_first())
        meta['zip'], meta['city'] = self.fix_data(response.css('#ContentPlaceHolderMenuListe_lblOrt::text').extract_first()).split(" ", 1)
        schooltype = re.split('[()]', response.css('#ContentPlaceHolderMenuListe_lblSchulart::text').extract_first())
        meta['schooltype'] = self.fix_data(schooltype[0].strip())
        meta['legal_status'] = self.fix_data(schooltype[1].strip())
        meta['telephone'] = self.fix_data(response.css('#ContentPlaceHolderMenuListe_lblTelefon::text').extract_first())
        meta['fax'] = self.fix_data(response.css('#ContentPlaceHolderMenuListe_lblFax::text').extract_first())
        meta['mail'] = self.fix_data(response.css('#ContentPlaceHolderMenuListe_HLinkEMail::text').extract_first())
        meta['web'] = self.fix_data(response.css('#ContentPlaceHolderMenuListe_HLinkWeb::attr(href)').extract_first())
        headmaster = response.css('#ContentPlaceHolderMenuListe_lblLeitung::text').extract_first()
        if headmaster:
            meta['headmaster'] = self.fix_data(' '.join(headmaster.split(',')[::-1]).strip())  
        meta['cookiejar'] = response.meta['cookiejar']
        meta['data_url'] = response.url
        activities = self.fix_data(response.css('#ContentPlaceHolderMenuListe_lblAGs::text').extract_first())
        if activities:
            meta['activities'] = [x.strip() for x in activities.split(';')]
        partner = self.fix_data(response.css('#ContentPlaceHolderMenuListe_lblPartner::text').extract_first())
        if partner:
            meta['partner'] = [x.strip() for x in partner.split(';')]
        yield meta

    def _parse_school_no(self, url):
        """Parses the school number from the 'IDSchulzweig' parameter in the url"""
        parsed = urlparse.urlparse(url)
        id_in_url: List[str] = parse_qs(parsed.query, max_num_fields=1)['IDSchulzweig']
        assert len(id_in_url) == 1

        return id_in_url[0].strip()

    # fix wrong tabs, spaces and new lines
    def fix_data(self, string):
        if string:
            string = ' '.join(string.split())
            string.replace('\n', '')
            string.replace('\t', '')
        return string

    def normalize(self, item: Item) -> School:
        return School(name=item.get('name'),
                      id='BE-{}'.format(item.get('id')),
                      address=item.get('address'),
                      zip=item.get('zip'),
                      city=item.get('city'),
                      website=item.get('web'),
                      email=item.get('mail'),
                      school_type=item.get('schooltype'),
                      fax=item.get('fax'),
                      phone=item.get('telephone'),
                      director=item.get('headmaster'),
                      legal_status=item.get('legal_status'))