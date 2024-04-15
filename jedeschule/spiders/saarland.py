from scrapy.spiders import Rule, CrawlSpider
from scrapy.linkextractors import LinkExtractor
from scrapy import Item, FormRequest, Request

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider

# School types: Berufliche Schule, Erweitere Realschule, Förderschule, Freie Waldorfschule,
# Gemeinschatsschule, Grundschule, Gymnasium, Lyzeum, Realschule, Studienseminare

class SaarlandSpider(CrawlSpider, SchoolSpider):
    name = "saarland"
    start_urls = ['https://www.saarland.de/mbk/DE/portale/bildungsserver/schulen-und-bildungswege/schuldatenbank']

    rules = (Rule(LinkExtractor(allow=(), restrict_xpaths=('//a[@class="forward button"]',)), callback="parse_start_url", follow= True),)


    def parse_start_url(self, response):
        yield FormRequest.from_response(response,
                                        formname="searchSchool",
                                        callback=self.parse_page)

    def parse_page(self, response):
        for school in self.parse_schools(response):
            yield school
        next_button = response.xpath('//a[@class="forward button"]/@href').extract_first()
        if next_button:
            yield Request(next_button, callback=self.parse_page)

    def parse_schools(self, response):
        cards = response.xpath('//div[@class="c-teaser-card"]')

        for card in cards:
            school = {}
            school["name"] = card.xpath('.//h3/text()').extract_first().strip()

            badges = card.css('.c-badge')
            school["schultyp"] = badges[0].css("::text").extract_first()
            school["ort"] = badges[1].css("::text").extract_first()

            address = card.xpath('.//p/text()').extract_first().split(", ")

            school["straße"] = address[0]
            school["plz"] = address[1].strip(" " + school['ort'])

            keys = card.xpath('.//dt/text()').extract()
            info = card.xpath('.//dd/text()').extract()

            for index in range(0, len(keys)):
                key = keys[index].strip(":").lower()

                if key == "homepage" :
                    school["homepage"] = card.xpath('.//a[@target="_blank"]/text()').extract_first()

                if key == "e-mail" :
                    school["e-mail"] = card.xpath('.//a[contains(@title, "E-Mail senden an:")]/@href').extract_first().strip("mailto:")

                if key != "homepage" and key != "e-mail" :
                    school[key] = info[index]

            yield school

    @staticmethod
    def get_id(item: Item) -> str:
        # There are no IDs on the page that we could use.
        # We will fall back to phone number, e-mail or name
        # and fall back to e-mail in the worst case
        if tel := item.get('telefon'):
            return tel.replace(" ", "-")
        if email := item.get('e-mail'):
            return email.replace("@", "AT")
        return item.get('name')

    @staticmethod
    def normalize(item: Item) -> School:
        return School(name=item.get('name'),
                      phone=item.get('telefon'),
                      fax=item.get('telefax'),
                      website=item.get('homepage'),
                      email=item.get("e-mail"),
                      address=item.get('straße'),
                      city=item.get('ort'),
                      zip=item.get('plz'),
                      school_type=item.get('schultyp'),
                      director=item.get('schulleitung'),
                      id='SL-{}'.format(SaarlandSpider.get_id(item)))