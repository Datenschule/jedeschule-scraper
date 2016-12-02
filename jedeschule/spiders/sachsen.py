import scrapy
from scrapy.shell import inspect_response

class SachsenSpider(scrapy.Spider):
    name = "sachsen"

    start_urls = ['https://schuldatenbank.sachsen.de/index.php?id=2']
    #custom_settings = {
    #    "CONCURRENT_REQUESTS": 1,
    #    "DOWNLOAD_DELAY":5,
    #    "DEPTH_PRIORITY" : -1
    #}

    def parse(self, response):
        #inspect_response(response, self)
        yield scrapy.FormRequest.from_response(
            response, formcss="#content form", callback=self.parse_schoolist)

    def parse_schoolist(self, response):
        forms = len(response.css('.ssdb_02 form'))
        for formnumber in range(forms):
            yield scrapy.FormRequest.from_response(
                response,
                formnumber=formnumber + 3,
                meta={'cookiejar': formnumber},
                callback=self.parse_school)

    def parse_school(self, response):
        collection = {}
        #inspect_response(response, self)
        collection['title'] = response.css("#content h2::text").extract_first().strip()
        entries = response.css(".kontaktliste li")
        for entry in entries:
            key = entry.css("b::text").extract_first(default="kein Eintrag").strip()
            values = entry.css("::text").extract()[1:]
            #inspect_response(response, self)
            collection[key] = ' '.join(values).replace('zur Karte', '')
        response = scrapy.Request('https://schuldatenbank.sachsen.de/index.php?id=440',
                                  meta={'cookiejar': response.meta['cookiejar']},
                                  callback=self.parse_personal_ressources,
                                  dont_filter=True)
        response.meta['collection'] = collection
        yield response
        #yield collection

    def parse_personal_ressources(self, response):
        #inspect_response(response,self)
        collection = response.meta['collection']
        ressources = {}
        categories = response.css('#content h2')
        for cat in categories:
            catname = cat.css("::text").extract_first().strip()
            trs = cat.xpath("following-sibling::table").css('tr')
            headers = [header.css('::text').extract_first().strip() for header in trs[0].css("td")]
            entries = []
            for tr in trs[1:]:
                row = {}
                for index,td in enumerate(tr.css('td')):
                    row[headers[index]] = td.css("::text").extract_first().strip()
                entries.append(row)
            ressources[catname] = entries
        collection['personal Ressources'] = ressources
        yield collection
