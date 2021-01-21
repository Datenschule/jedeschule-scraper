from typing import List, Optional

import scrapy
from scrapy import Item

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


def first_or_none(item: List) -> Optional[str]:
    return next(iter(item or []), None)


class BrandenburgSpider(SchoolSpider):
    name = "brandenburg"
    start_urls = ['https://bildung-brandenburg.de/schulportraets/index.php?id=uebersicht']

    def parse(self, response):
        for link in response.xpath('/html/body/div/div[5]/div[2]/div/div[2]/table/tbody/tr/td/a/@href').getall():
            yield scrapy.Request(response.urljoin(link), callback=self.parse_details)

    def parse_details(self, response):
        table = response.xpath('//*[@id="c"]/div/table')
        data = {
            # extract the school ID from the URL
            'id': response.url.rsplit('=', 1)[1],
            'data_url': response.url
        }
        for tr in table.css('tr:not(:first-child)'):
            key = tr.css('th ::text').get().replace(':', '').strip()
            value = tr.css('td ::text').getall()
            data[key] = [self.fix_data(part) for part in value]
        yield data

    def fix_data(self, string):
        """
        fix wrong tabs, spaces and backslashes
        fix @ in email addresses
        """
        if string is None:
            return None
        string = ' '.join(string.split())
        return string.replace('\\', '').replace('|at|','@').strip()

    @staticmethod
    def normalize(item: Item) -> School:
        *name, street, place = item.get('Adresse')
        zip_code, *city_parts = place.split(" ")
        return School(name=' '.join(name),
                        id='BB-{}'.format(item.get('id')),
                        address=street,
                        zip=zip_code,
                        city=' '.join(city_parts),
                        website=first_or_none(item.get('Internet')),
                        email=first_or_none(item.get('E-Mail')),
                        school_type=first_or_none(item.get('Schulform')),
                        provider=first_or_none(item.get('Schulamt')),
                        fax=first_or_none(item.get('Fax')),
                        phone=first_or_none(item.get('Telefon')),
                        director=first_or_none(item.get('Schulleiter/in')))