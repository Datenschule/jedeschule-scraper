# -*- coding: utf-8 -*-
import scrapy
from scrapy.shell import inspect_response
import re

class BerlinSpider(scrapy.Spider):
    name = "berlin"
    # allowed_domains = ["www.berlin.de/sen/bildung/schule/berliner-schulen/schulverzeichnis/SchulListe.aspx"]
    base_url = 'http://www.berlin.de/sen/bildung/schule/berliner-schulen/schulverzeichnis/'
    start_url = base_url + 'SchulListe.aspx/'
    start_urls = [start_url]

    def parse(self, response):
        schools = response.css('td a::attr(href)').extract()
        for i, school in enumerate(schools):
            yield scrapy.Request(self.start_url + school, callback=self.parse_detail, meta={'cookiejar': i})

    def parse_detail(self, response):
        meta = {}
        name = response.css('#ContentPlaceHolderMenuListe_lblSchulname::text').extract_first().strip().rsplit('-', 1)
        meta['name'] = name[0]
        meta['id'] = self.remove_Spaces(name[1])
        strasse = response.css('#ContentPlaceHolderMenuListe_lblStrasse::text').extract_first()
        ort = response.css('#ContentPlaceHolderMenuListe_lblOrt::text').extract_first()
        meta['address'] = strasse + " " + ort
        schooltype = re.split('[()]', response.css('#ContentPlaceHolderMenuListe_lblSchulart::text').extract_first())
        meta['schooltype'] = schooltype[0].strip()
        meta['legal_status'] = schooltype[1].strip()
        meta['telephone'] = response.css('#ContentPlaceHolderMenuListe_lblTelefon::text').extract_first()
        meta['fax'] = response.css('#ContentPlaceHolderMenuListe_lblFax::text').extract_first()
        meta['mail'] = response.css('#ContentPlaceHolderMenuListe_HLinkEMail::text').extract_first()
        meta['web'] = response.css('#ContentPlaceHolderMenuListe_HLinkWeb::attr(href)').extract_first()
        headmaster = response.css('#ContentPlaceHolderMenuListe_lblLeitung::text').extract_first().strip()
        meta['headmaster'] = ' '.join(headmaster.split(',')[::-1]).strip()
        meta['cookiejar'] = response.meta['cookiejar']
        activities = response.css('#ContentPlaceHolderMenuListe_lblAGs::text').extract_first()
        if activities:
            meta['activities'] = [x.strip() for x in activities.split(';')]
        partner = response.css('#ContentPlaceHolderMenuListe_lblPartner::text').extract_first()
        if partner:
            meta['partner'] = [x.strip() for x in partner.split(';')]
        yield scrapy.Request('https://www.berlin.de/sen/bildung/schule/berliner-schulen/schulverzeichnis/schuelerschaft.aspx?view=jgs',
                             meta=meta, callback=self.call_students, dont_filter=True)

    def call_students(self, response):
        links = response.css('#NaviSchuelerschaft ul ul li a::attr(href)').extract()
        meta = response.meta
        meta['cookiejar'] = response.meta['cookiejar']
        if len(links) > 0:
            meta['student_links'] = links[1:]

            yield scrapy.Request(self.base_url + links[0], meta=response.meta, dont_filter=True, callback=self.parse_students)
        else:
            yield response.meta

    def parse_students(self, response):
        # inspect_response(response, self)
        year = response.request.url.rsplit('=', 1)[1]
        meta = response.meta
        if 'students' not in meta.keys():
            meta['students'] = {}
        meta['students'][year] = self.parse_table(response.css('#ContentPlaceHolderMenuListe_GridViewJahrgansstufen'))
        links = meta['student_links']

        if len(links) > 0:
            meta['student_links'] = links[1:]
            yield scrapy.Request(self.base_url + links[0], meta=response.meta, dont_filter=True, callback=self.parse_students)
        else:
            yield scrapy.Request('https://www.berlin.de/sen/bildung/schule/berliner-schulen/schulverzeichnis/schulpersonal.aspx?view=pers',
                                 meta=meta, callback=self.call_teacher, dont_filter=True)

    def call_teacher(self, response):
        links = response.css('#NaviSchulpersonal ul ul li a::attr(href)').extract()
        meta = response.meta
        meta['cookiejar'] = response.meta['cookiejar']
        if len(links) > 0:
            meta['teacher_links'] = links[1:]
            yield scrapy.Request(self.base_url + links[0], meta=response.meta, dont_filter=True, callback=self.parse_teachers)
        else:
            yield response.meta

    def parse_teachers(self, response):
        year = response.request.url.rsplit('=', 1)[1]
        meta = response.meta
        if 'teachers' not in meta.keys():
            meta['teachers'] = {}
        meta['teachers'][year] = self.parse_table(response.css('#ContentPlaceHolderMenuListe_GridViewPersonal'))
        links = meta['teacher_links']

        if len(links) > 0:
            meta['teacher_links'] = links[1:]
            yield scrapy.Request(self.base_url + links[0], meta=meta, dont_filter=True, callback=self.parse_students)
        else:
            # inspect_response(response, self)
            yield meta

    def parse_table(self, table):
        result = {}
        keys = table.css('th::text').extract()
        for row in table.css('tr'):
            for idx, value in enumerate(row.css('td')):
                result[keys[idx]] = value.css('::text').extract_first()
        return result

    def remove_Spaces(self, string):
        return string.replace(' ','') 