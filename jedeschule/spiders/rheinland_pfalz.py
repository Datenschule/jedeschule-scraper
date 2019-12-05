import re

import scrapy
from scrapy import Item
from scrapy.shell import inspect_response

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider
from jedeschule.utils import cleanjoin
import logging


class RheinlandPfalzSpider(SchoolSpider):
    name = "rheinland-pfalz"
    root_url = "https://www.statistik.rlp.de/"
    abs_url = 'https://www.statistik.rlp.de/de/service/adress-suche/allgemeinbildende-schulen/'
    start_urls = [
        'https://www.statistik.rlp.de/de/service/adress-suche/allgemeinbildende-schulen/stala/search/General/school/',
        'https://www.statistik.rlp.de/de/service/adress-suche/berufsbildende-schulen/stala/search/General/schoolp/'
    ]

    def start_requests(self):
        data = {
            'tx_stala_general[name]:': '',
        }
        return [scrapy.FormRequest(url=url,
                                   formdata=data,
                                   callback=self.parse_schoolist)
                for url in self.start_urls]

    # go on each schools details side
    def parse_schoolist(self, response):
        table = response.css('table.publications tbody tr')
        # sometimes the typ is only displayed once for multiple school, so we have to chache it
        school_type = ''
        for tr in table:
            cols = tr.css("td a::text").getall()
            if len(cols) > 1:
                school_type = cols[0]
            links = tr.css("td a::attr(href)").getall()
            link = self.root_url + links[-1]
            yield scrapy.Request(
                response.urljoin(link),
                meta={'school_type': school_type},
                callback=self.parse_school_data
            )

    # get the information
    def parse_school_data(self, response):
        info = response.css('div.links')
        details = info.css('.list-address li::text').getall()
        street = details[5] if 5 < len(details) else ''
        city = details[6] if 6 < len(details) else ''
        online = info.css('.list-address li a::text').getall()
        email = online[0] if 0 < len(online) else ''
        internet = online[1] if 1 < len(online) else ''

        # extract the school ID from the URL
        m = re.search(r'/(\d+)/$', response.url)
        school_id = m.group(1) if len(m.groups()) == 1 else None

        data = {
            'id': school_id,
            'name': self.fix_data(info.css('h3::text').get()),
            'Schulform': self.fix_data(response.meta.get('school_type')),
            'Adresse': self.fix_data(street),
            'Ort': self.fix_data(city),
            'Telefon': self.fix_data(details[7] if 7 < len(details) else ''),
            'Fax': self.fix_data(details[8] if 8 < len(details) else ''),
            'E-Mail': self.fix_data(email),
            'Internet': self.fix_data(internet),
            'data_url': response.url
        }

        yield data

    # fix wrong tabs, spaces and backslashes
    def fix_data(self, string):
        string = ' '.join(string.split())
        string.replace('\\', '')
        return string

    def normalize(self, item: Item) -> School:
        return School(name=item.get('name'),
                      id='RP-{}'.format(item.get('id')),
                      address=item.get('Adresse'),
                      city=item.get('Ort'),
                      website=item.get('Internet'),
                      email=item.get('E-Mail'),
                      school_type=item.get('Schulform'),
                      fax=item.get('Fax'),
                      phone=item.get('Telefon'))
