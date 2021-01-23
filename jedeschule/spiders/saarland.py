from scrapy.spiders import Rule, CrawlSpider
from scrapy.linkextractors import LinkExtractor
from scrapy import Item

from jedeschule.items import School

# School types: Berufliche Schule, Erweitere Realschule, Förderschule, Freie Waldorfschule,
# Gemeinschatsschule, Grundschule, Gymnasium, Lyzeum, Realschule, Studienseminare


class SaarlandSpider(CrawlSpider):
    name = "saarland"
    start_urls = ['https://www.saarland.de/mbk/DE/portale/bildungsserver/themen/schulen-und-bildungswege/schuldatenbank/_functions/Schulsuche_Formular.html']

    rules = (Rule(LinkExtractor(allow=(), restrict_xpaths=('//a[@class="forward button"]',)), callback="parse_start_url", follow= True),)

    def parse_start_url(self, response):
        cards = response.xpath('//div[@class="c-teaser-card"]')

        for card in cards:
            school = {}
            school["name"] = card.xpath('.//h3/text()').extract_first().strip()

            c_badge = card.xpath('.//span[@class="c-badge"]/text()').extract()
            school["schultyp"] = c_badge[0]
            school["ort"] = c_badge[1]

            adress = card.xpath('.//p/text()').extract_first().split(", ")

            school["straße"] = adress[0]
            school["plz"] = adress[1].strip(" " + school['ort'])

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
    def normalize(item: Item) -> School:
        if item.get('homepage'):
            hp = item.get('homepage')
        else:
            hp = 'N.N.'

        if item.get('e-mail'):
            mail = item.get('e-mail')
        else:
            mail = 'N.N.'

        if item.get('telefon'):
            tel = item.get('telefon')
        else:
            tel = 'N.N.'

        if item.get('telefax'):
            fax = item.get('telefax')
        else:
            fax = 'N.N.'

        if item.get('schulleitung'):
            leitung = item.get('schulleitung')
        else:
            leitung = 'N.N.'

        return School(name=item.get('name'),
                      phone=tel,
                      fax=fax,
                      website=hp,
                      email=mail,
                      address=item.get('straße'),
                      city=item.get('ort'),
                      zip=item.get('plz'),
                      school_type=item.get('schultyp'),
                      director=leitung,
                      id='SL-{}'.format(tel.replace(" ", "-")))