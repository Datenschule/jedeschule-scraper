import scrapy
from scrapy.shell import inspect_response

class SachsenSpider(scrapy.Spider):
    name = "thueringen"
    base_url = "https://www.schulportal-thueringen.de"

    start_urls = ['https://www.schulportal-thueringen.de/tip/schulportraet_suche/search.action?tspi=&tspm=&vsid=none&mode=&extended=0&anwf=schulportraet&freitextsuche=&name=&schulnummer=&strasse=&plz=&ort=&schulartDecode=&schulamtDecode=&schultraegerDecode=&sortierungDecode=Schulname&rowsPerPage=999&schulartCode=&schulamtCode=&schultraegerCode=&sortierungCode=10&uniquePortletId=portlet_schulportraet_suche_WAR_tip_LAYOUT_10301']

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
            if len(tds) == 2:
                collection[tds[0][:-1]] = tds[1]
        print(collection)
        collection['data_url'] = response.url
        yield collection
