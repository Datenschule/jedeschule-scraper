import scrapy
import re

from jedeschule.spiders.school_spider import SchoolSpider
from jedeschule.utils import cleanjoin
from jedeschule.items import School
from scrapy import Item


class SachsenSpider(SchoolSpider):
    name = "sachsen"

    base_url = 'https://schuldatenbank.sachsen.de/'
    start_urls = ['https://schuldatenbank.sachsen.de/index.php?id=2']

    def parse(self, response):
        yield scrapy.FormRequest.from_response(
            response, formcss="#content form", callback=self.parse_schoolist)

    def parse_schoolist(self, response):
        first_ids = response.css('.ssdb_02 form input:nth-child(1) ::attr(value)').extract()
        first_ids_names = response.css('.ssdb_02 form input:nth-child(1) ::attr(name)').extract()
        second_ids = response.css('.ssdb_02 form input:nth-child(2) ::attr(value)').extract()
        second_ids_names = response.css('.ssdb_02 form input:nth-child(2) ::attr(name)').extract()

        for i, first_id in enumerate(first_ids):
            form_url = self.base_url + 'index.php?' + first_ids_names[i] + '=' + str(first_id) + '&' + second_ids_names[i] + '=' + str(second_ids[i])
            yield scrapy.Request(form_url, callback=self.parse_school, meta={'cookiejar': i})

    def parse_school(self, response):
        collection = {'phone_numbers': {}}
        collection['title'] = self.fix_data(response.css("#content h2::text").extract_first().strip())
        collection['data_url'] = response.url
        entries = response.css(".kontaktliste li")
        for entry in entries:
            # Remove the trailing `:` from the key (:-1)
            key = self.fix_data(entry.css("b::text").extract_first(default="kein Eintrag:").strip()[:-1])
            values = [self.fix_data(value) for value in entry.css("::text").extract()[1:]]
            # Some schools list additional phone numbers. The problem is
            # that they do not have the header "Telefon" or something
            # comparable. The header shows, whom the number belongs to
            # So we check if there is a phone icon and if there is we
            # Add this to our list of phone numbers
            type = entry.css("img::attr(src)").extract_first()
            if type == "img/telefon.gif":
                collection['phone_numbers'][key] = ' '.join(values)
            else:
                collection[key] = ' '.join(values).replace('zur Karte', '')

        collection["Leitbild"] = cleanjoin(response.css("#quickbar > div:nth-child(3) ::text").extract(), "\n")
        yield collection

    def fix_data(self, string):
        """ fix wrong tabs, spaces and new lines"""
        if string:
            string = ' '.join(string.split())
            string.replace('\n', '')
        return string

    @staticmethod
    def normalize(item: Item) -> School:
        v = list(item.get('phone_numbers').values())
        phone_numbers = v[0] if len(v) > 0 else None

        address_objects = re.split('\d{5}', item.get('Postanschrift').strip())
        if len(address_objects) == 0:
            address = ''
            zip = ''
            city = ''
        elif len(address_objects) == 1:
            address = ''
            zip = ''
            city = address_objects[0].strip()
        else:
            address = re.split('\d{5}', item.get('Postanschrift'))[0].strip()
            zip = re.findall('\d{5}', item.get('Postanschrift'))[0].strip()
            city = re.split('\d{5}', item.get('Postanschrift'))[1].strip()


        return School(name=item.get('title'),
                      id='SN-{}'.format(item.get('Dienststellenschlüssel')),
                      address=address,
                      zip=zip,
                      city=city,
                      website=item.get('Homepage'),
                      email=item.get('E-Mail'),
                      school_type=item.get('Einrichtungsart'),
                      legal_status=item.get('Rechtsstellung'),
                      provider=item.get('Schulträger'),
                      fax=item.get('Telefax'),
                      phone=phone_numbers,
                      director=item.get('Schulleiter') or item.get('Schulleiter/in'))


