import scrapy
import re

from scrapy import Item

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class HessenSpider(SchoolSpider):
    name = "hessen"

    start_urls = ['https://schul-db.bildung.hessen.de/schul_db.html']

    def parse(self, response):
        school_types = response.xpath('//select[@id="id_school_type"]/option/@value').extract()

        form = {
            'school_name': '',
            'school_town': '',
            'school_zip': '',
            'school_number': '',
            'csrfmiddlewaretoken': response.xpath('//input[@name="csrfmiddlewaretoken"]/@value').extract_first(),
            'submit_hesse': 'Hessische+Schule+suchen+...'
        }

        for school_type in school_types:
            form['school_type'] = school_type

            yield scrapy.FormRequest(self.start_urls[0], formdata=form, callback=self.parse_list)

    def parse_list(self, response):
        schools = response.xpath('//tbody/tr/td/a/@href').extract()

        for school in schools:
            yield scrapy.Request(school, callback=self.parse_details)

    def parse_details(self, response):
        contact_text_nodes = response.xpath('//pre/text()').extract()
        adress = contact_text_nodes[0].split('\n')

        matches = re.search(r"(\d+) (.+)", adress[3])

        school = {
            'name': adress[1],
            'straße': adress[2],
            'ort': matches.group(2),
            'plz': matches.group(1),
        }

        for text_node in contact_text_nodes:
            if "Fax: " in text_node:
                school['fax'] = text_node.split('\n')[1].replace("Fax: ", "").strip()

        contact_links = response.xpath('//pre/a/@href').extract()
        for link in contact_links:
            if "tel:" in link:
                school['telefon'] = link.replace("tel:", "")

            if "http" in link:
                school['homepage'] = link

        school['schultyp'] = response.xpath('//main//div[@class="col-md-9 col-lg-9"]/text()').extract_first().replace("\n", "").strip()
        school['id'] = response.request.url.split("=")[-1]

        yield school

    @staticmethod
    def normalize(item: Item) -> School:
        return School(name=item.get('name'),
                      phone=item.get('telefon'),
                      fax=item.get('fax'),
                      website=item.get('homepage'),
                      address=item.get('straße'),
                      city=item.get('ort'),
                      zip=item.get('plz'),
                      school_type=item.get('schultyp'),
                      id='HE-{}'.format(item.get('id')))
