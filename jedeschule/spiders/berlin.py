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
    custom_settings = {'USER_AGENT': 'jedeschule (open data project)', 'DOWNLOAD_DELAY': 1 }
    base_url = 'https://www.bildung.berlin.de/Schulverzeichnis/'
    start_url = base_url + 'SchulListe.aspx'
    start_urls = [start_url]
    url_parse_staff = base_url + 'schulpersonal.aspx?view=pers'

    def parse(self, response):
        schools = response.css('td a::attr(href)').extract()
        for i, school in enumerate(schools):
            # school = school.replace(' ','')
            yield scrapy.Request(self.base_url + school, callback=self.parse_detail, meta={'cookiejar': i})

    def parse_detail(self, response):
        meta = {}
        name = response.css(
            '#ContentPlaceHolderMenuListe_lblSchulname::text').extract_first().strip()  # .rsplit('-', 1)
        meta['name'] = self.fix_data(name)
        meta['id'] = self._parse_school_no(response.url)
        meta['address'] = self.fix_data(response.css('#ContentPlaceHolderMenuListe_lblStrasse::text').extract_first())
        meta['zip'], meta['city'] = self.fix_data(
            response.css('#ContentPlaceHolderMenuListe_lblOrt::text').extract_first()).split(" ", 1)
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
        yield scrapy.Request(self.base_url + 'schuelerschaft.aspx?view=jgs', callback=self.parse_students, meta=meta,
                             dont_filter=True)

    def parse_students(self, response):
        # inspect_response(response, self)
        years = response.css('#portrait_hauptnavi li a::attr(href)').extract()
        relevant = []
        for i, year in enumerate(years):
            if (re.search('.*view=jgs&jahr.*', year)):
                relevant.append(year)
        meta = response.meta
        if (len(relevant) > 0):
            meta['student_years'] = relevant[1:]
            yield scrapy.Request(self.base_url + relevant[0], callback=self.parse_student_year, meta=meta,
                                 dont_filter=True)
        else:
            yield scrapy.Request(self.url_parse_staff, callback=self.parse_staff, meta=meta, dont_filter=True)

    def parse_student_year(self, response):
        # inspect_response(response, self)
        meta = response.meta
        if (len(meta['student_years']) > 0):
            headers = response.css('th::text').extract()
            rows = response.css('table tr.odd, table tr.even')
            title = self.fix_data(response.css('table caption::text').extract_first()).replace('Jahrgangsstufen',
                                                                                               '').strip()
            if not 'students' in meta.keys():
                meta['students'] = []
            for i, row in enumerate(rows):
                result = {}
                entries = row.css('td::text').extract()
                for j, header in enumerate(headers):
                    result[header] = entries[j]
                result['year'] = title
                meta['students'].append(result)
            relevant = meta['student_years']
            meta['student_years'] = relevant[1:]
            yield scrapy.Request(self.base_url + relevant[0], callback=self.parse_student_year, meta=meta,
                                 dont_filter=True)
        else:
            yield scrapy.Request(self.url_parse_staff, callback=self.parse_staff, meta=meta, dont_filter=True)

    def parse_staff(self, response):
        years = response.css('#NaviSchulpersonal ul')[0].css('li a[href*="jahr"]::attr(href)').extract()
        meta = response.meta
        if (len(years) > 0):
            meta['staff_years'] = years[1:]
            yield scrapy.Request(self.base_url + years[0], callback=self.parse_staff_year, meta=meta, dont_filter=True)
        else:
            yield response.meta

    def parse_staff_year(self, response):
        inspect_response(response, self)
        meta = response.meta
        headers = response.css('th::text').extract()
        rows = response.css('table tr.odd, table tr.even')
        title_raw = self.fix_data(response.css('table caption::text').extract_first())
        title = ''
        if title_raw == None:
            title = title_raw.replace('Jahrgangsstufen','').strip()
        if not 'staff' in meta.keys():
            meta['staff'] = []
        for i, row in enumerate(rows):
            result = {}
            entries = row.css('td::text').extract()
            for j, header in enumerate(headers):
                result[header] = entries[j]
            result['year'] = title
            meta['staff'].append(result)
        relevant = meta['staff_years']
        if (len(relevant) > 0):
            meta['staff_years'] = relevant[1:]
            yield scrapy.Request(self.base_url + relevant[0], callback=self.parse_staff_year, meta=meta,
                                 dont_filter=True)
        else:
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
            string.replace('\r', '')
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
