from scrapy import Item
from scrapy.linkextractors import LinkExtractor

from scrapy.spiders import CrawlSpider, Rule

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class RheinlandPfalzSpider(CrawlSpider, SchoolSpider):
    name = "rheinland-pfalz"
    # Note, one could also use the geo portal:
    # https://www.geoportal.rlp.de/spatial-objects/350/collections/schulstandorte/items?f=html&limit=4000
    start_urls = ["https://schulen.bildung-rp.de"]
    rules = [
        Rule(
            LinkExtractor(allow="https://schulen.bildung-rp.de/einzelanzeige.html?.*"),
            callback="parse_school",
            follow=False,
        )
    ]

    # get the information
    def parse_school(self, response):
        container = response.css("#wfqbeResults")
        item = {"name": container.css("h1::text").get()}
        for row in container.css("tr"):
            key, value = row.css("td")
            value_parts = value.css("*::text").extract()
            item[key.css("::text").extract_first().replace(":", "")] = (
                value_parts[0] if len(value_parts) == 1 else value_parts
            )
        item["id"] = item["Schulnummer"]

        osm_url = container.css('a[href*="openstreetmap"]::attr(href)').extract_first()
        *rest, lat, lon = osm_url.split("/")
        item["lat"] = lat
        item["lon"] = lon
        yield item

    def normalize(self, item: Item) -> School:
        zip, city = item.get("Anschrift")[-1].split("\xa0")
        email_parts = item.get("E-Mail")
        email = email_parts[0].replace("(at)", "@") + email_parts[2]
        return School(
            name=item.get("name"),
            id="RP-{}".format(item.get("id")),
            address=item.get("Anschrift")[1],
            city=city,
            zip=zip,
            latitude=item.get("lat"),
            longitude=item.get("lon"),
            website=item.get("Internet"),
            email=email,
            provider=item.get("Träger"),
            fax=item.get("Telefax"),
            phone=item.get("Telefon"),
        )
