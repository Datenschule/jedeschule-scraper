from scrapy import Item
from scrapy.linkextractors import LinkExtractor
import re

from scrapy.spiders import CrawlSpider, Rule

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class RheinlandPfalzSpider(CrawlSpider, SchoolSpider):
    name = "rheinland-pfalz"
    # Note, one could also use the geo portal:
    # https://www.geoportal.rlp.de/spatial-objects/350/collections/schulstandorte/items?f=html&limit=4000
    start_urls = ["https://bildung.rlp.de/schulen"]
    rules = [
        Rule(
            LinkExtractor(allow="https://bildung.rlp.de/schulen/einzelanzeige.*"),
            callback="parse_school",
            follow=False,
        )
    ]

    # get the information
    def parse_school(self, response):
        container = response.css(".rlp-schooldatabase-detail")
        item = {"name": container.css("h1::text").get()}
        for row in container.css("tr"):
            key, value = row.css("td")
            value_parts = value.css("*::text").extract()
            cleaned = [part.strip() for part in value_parts]
            item[key.css("::text").extract_first().replace(":", "")] = (
                cleaned[0] if len(cleaned) == 1 else cleaned
            )
        item["id"] = item["Schulnummer"]

        osm_url = container.css('a[href*="openstreetmap"]::attr(href)').extract_first()
        *rest, lat, lon = osm_url.split("/")
        item["lat"] = lat
        item["lon"] = lon
        yield item

    def normalize(self, item: Item) -> School:
        zip, city = item.get("Anschrift")[-1].rsplit(" ")
        email = item.get("E-Mail", "").replace("(at)", "@")
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
