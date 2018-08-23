# -*- coding: utf-8 -*-
try:
    # python2
    from urlparse import parse_qs
    from urlparse import urlparse

except ImportError:
    # python3
    from urllib.parse import urlparse
    from urllib.parse import parse_qs
import scrapy
from scrapy.shell import inspect_response



class BrandenburgSpider(scrapy.Spider):
    name = "brandenburg"
    # allowed_domains = ["https://www.bildung-brandenburg.de/schulportraets/index.php?id=3"]
    start_urls = ['https://www.bildung-brandenburg.de/schulportraets/index.php?id=3&schuljahr=2016&kreis=&plz=&schulform=&jahrgangsstufe=0&traeger=0&submit=Suchen',
                  'https://www.bildung-brandenburg.de/schulportraets/index.php?id=3&schuljahr=2016&kreis=&plz=&schulform=&jahrgangsstufe=0&traeger=1&submit=Suchen']

    def parse(self, response):
        for link in response.css("table a"):
            url = link.css("::attr(href)").extract_first()
            response.link = link
            parsed_url = urlparse(url)
            parsed = parse_qs(parsed_url.query)
            meta = {}
            meta['nummer'] = parsed['schulnr'][0]
            meta['name'] = link.css('::text').extract_first()
            response.foo = meta
            #inspect_response(response, self)
            yield scrapy.Request(response.urljoin(url), callback=self.parse_detail, meta=meta)

    def parse_detail(self, response):
        trs = response.css("table tr")
        content = {}
        # The first row is an image and a map
        #inspect_response(response, self)
        for tr in trs[1:]:
            key = "\n".join(tr.css('th ::text').extract()).strip()[:-1].replace("**", "")
            value = "\n".join(tr.css("td ::text").extract()).replace("*", "")
            content[key] = value
        content['name'] = response.meta['name']
        content['nummer'] = response.meta['nummer']
        response.content = content
        #inspect_response(response, self)
        yield content
