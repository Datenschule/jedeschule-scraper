import scrapy
from scrapy.shell import inspect_response

class SachsenSpider(scrapy.Spider):
    name = "sachsen"

    start_urls = ['https://schuldatenbank.sachsen.de/index.php?id=2']

    def parse(self, response):
        # inspect_response(response, self)
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
        collection = {'phone_numbers':{}}
        collection['title'] = response.css("#content h2::text").extract_first().strip()
        entries = response.css(".kontaktliste li")
        for entry in entries:
            # Remove the trailing `:` from the key (:-1)
            key = entry.css("b::text").extract_first(default="kein Eintrag:").strip()[:-1]
            values = entry.css("::text").extract()[1:]

            # Some schools list additional phone numbers. The problem is
            # that they do not have the header "Telefon" or something
            # comparable. The header shows, whom the number belongs to
            # So we check if there is a phone icon and if there is we
            # Add this to our list of phone numbers
            type = entry.css("img::attr(src)").extract_first()
            if type == "img/telefon.gif":
                collection['phone_numbers'][key] = ' '.join(values)
            else:
                collection[key] = ' '.join(values).replace('zur Karte', '')

        collection["Leitbild"] = response.css("#quickbar > div:nth-child(3) ::text")
        response = scrapy.Request('https://schuldatenbank.sachsen.de/index.php?id=440',
                                  meta={'cookiejar': response.meta['cookiejar']},
                                  callback=self.parse_personal_resources,
                                  dont_filter=True)
        response.meta['collection'] = collection
        yield response

    def parse_personal_resources(self, response):
        collection = response.meta['collection']
        resources = {}
        categories = response.css('#content h2')
        for cat in categories:
            catname = cat.css("::text").extract_first().strip()
            trs = cat.xpath("following-sibling::table").css('tr')
            headers = [header.css('::text').extract_first().strip() for header in trs[0].css("td")]
            entries = []
            for tr in trs[1:]:
                row = {}
                for index, td in enumerate(tr.css('td')):
                    row[headers[index]] = td.css("::text").extract_first().strip()
                entries.append(row)
            resources[catname] = entries
        collection['personal_resources'] = resources
        yield collection
