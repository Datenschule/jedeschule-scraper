import re

import scrapy
from scrapy import Item

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class ThueringenSpider(SchoolSpider):
    name = "thueringen"
    base_url = "https://www.schulportal-thueringen.de"

    start_urls = [
        'https://www.schulportal-thueringen.de/tip/schulportraet_suche/search.action?tspi=&tspm=&vsid=none&mode=&extended=0&anwf=schulportraet&freitextsuche=&name=&schulnummer=&strasse=&plz=&ort=&schulartDecode=&schulamtDecode=&kzFreierTraeger_cb=1&kzFreierTraeger=2&schultraegerDecode=&sortierungDecode=Schulname&rowsPerPage=999&schulartCode=&schulamtCode=&schultraegerCode=&sortierungCode=10&uniquePortletId=portlet_schulportraet_suche_WAR_tip1109990a_e473_4c62_872b_4ef69bdb6c5d&ajaxId=schulportraet_suche_results']

    # TODO: parse last_modified
    def parse(self, response):
        headers = [header.css('::text').extract_first().strip() for header in response.css("th")]
        for tr in response.css(".tispo_row_odd,.tispo_row_normal"):
            collection = {}
            tds = tr.css("td")
            for index, td in enumerate(tds):
                key = headers[index]
                value = td.css('::text').extract_first()
                # The school name is hidden in a link so we check if there
                # is a link and if yes extract the value from that
                link_text = td.css("a ::text").extract_first()
                if link_text:
                    value = link_text
                collection[key] = value.strip()
            # inspect_response(response, self)
            url = tds[1].css('::attr(href)').extract_first().strip()
            request = scrapy.Request(self.base_url + url, callback=self.parse_overview)
            request.meta['collection'] = collection
            yield request

    def parse_overview(self, response):
        #inspect_response(response, self)
        collection = response.meta['collection']
        for tr in response.css(".tispo_labelValueView tr"):
            tds = tr.css("td ::text").extract()
            # sometimes there is no value for the key
            if len(tds) >= 2:
                collection[tds[0][:-1].strip()] = "".join([td.strip() for td in tds[1:]])
        collection['data_url'] = response.url
        collection['Leitbild'] = " ".join(response.css(".tispo_htmlUserContent ::text").extract())
        yield collection

    @staticmethod
    def normalize(item: Item) -> School:
        city_parts = item.get('Ort').split()
        zip, city = city_parts[0], ' '.join(city_parts[1:])
        return School(name=item.get('Schulname'),
                      id='TH-{}'.format(item.get('Schulnummer')),
                      address=item.get('Straße'),
                      zip=zip,
                      city=city,
                      website=item.get('Internet'),
                      email=ThueringenSpider._deobfuscate_email(item.get('E-Mail')),
                      school_type=item.get('Schulart'),
                      provider=item.get('Schulträger'),
                      fax=item.get('Telefax'),
                      phone=item.get('Telefon'))

    @staticmethod
    def _deobfuscate_email(orig):
        """
        Reverse-engineered version of the deobfuscation code on the website.

        :param orig: the obfuscated string or the whole function call (`$(function() {...})`),
            as long as it contains the prefix `#3b` and the suffix `3e#`.
        :return: the deofuscated string
        """

        result = ''
        if orig and re.search(r'#3b[a-z0-9 ]+3e#', orig):
            orig = re.search(r'#3b[a-z0-9 ]+3e#', orig).group(0)
            s = orig.replace(' ', '').replace('#3b', '').replace('3e#', '').replace('o', '')

            last_value = 0
            current_value = 0
            for i, c in enumerate(s):
                if c.isnumeric():
                    current_value = int(c)
                else:
                    current_value = ord(c) - 97 + 10

                if i % 2 == 1:
                    t = int(last_value * 23 + current_value) // 2
                    result += chr(t)
                last_value = current_value

        return result