import scrapy
from scrapy.shell import inspect_response

class SachsenSpider(scrapy.Spider):
    name = "nrw"
    base_url = "https://www.schulministerium.nrw.de/BiPo/SchuleSuchen/"

    start_urls = ['https://www.schulministerium.nrw.de/BiPo/SchuleSuchen/online']

    def parse(self, response):
        url = response.css(".bp_tab tr")[4].css("td")[1].css('a::attr(href)').extract_first().strip()
        return scrapy.Request(self.base_url + url, callback=self.parse_search)

    def parse_search(self, response):
        return scrapy.FormRequest.from_response(response, callback=self.parse_schoollist)

    def parse_schoollist(self, response):
        for tr in response.css('table tr'):
            collection = {}
            collection['Schulform'] = tr.css('td::text').extract()[1].strip()
            url = tr.css('td')[3].css('a::attr(href)').extract_first().strip()
            request = scrapy.Request(self.base_url + url, callback=self.parse_overview)
            request.meta['collection'] = collection
            yield request

    def parse_overview(self, response):
        collection = response.meta['collection']
        tables = response.css("table")
        # Table 1 is "Schuldaten"
        for tr in tables[0].css("tr"):
            tds = tr.css("td ::text").extract()
            # sometimes there is no value for the key
            if len(tds[0].strip()) > 0 and len(tds) >= 2:
                collection[tds[0].strip()] = " ".join([td.strip() for td in tds[1:]])
        yield collection
