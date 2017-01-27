import scrapy
from jedeschule.utils import cleanjoin
from scrapy.shell import inspect_response


class SachsenSpider(scrapy.Spider):
    name = "sachsen"

    start_urls = ['https://schuldatenbank.sachsen.de/index.php?id=2']

    def parse(self, response):
        yield scrapy.FormRequest.from_response(
            response, formcss="#content form", callback=self.parse_schoolist)

    def parse_schoolist(self, response):
        forms = len(response.css('.ssdb_02 form'))
        for formnumber in range(forms):
            yield scrapy.FormRequest.from_response(
                response,
                formnumber=formnumber + 3,
                meta={'cookiejar': formnumber},
                dont_filter=True,
                callback=self.parse_school)

    def parse_school(self, response):
        collection = {'phone_numbers': {}}
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

        collection["Leitbild"] = cleanjoin(response.css("#quickbar > div:nth-child(3) ::text").extract(), "\n")
        request = scrapy.Request('https://schuldatenbank.sachsen.de/index.php?id=440',
                                 meta={'cookiejar': response.meta['cookiejar']},
                                 callback=self.parse_personal_resources,
                                 dont_filter=True)
        request.meta['collection'] = collection
        yield request

    def parse_personal_resources(self, response):
        collection = response.meta['collection']
        resources = {}
        categories = response.css('#content h2')
        for cat in categories:
            catname = cat.css("::text").extract_first().strip()
            trs = cat.xpath("following-sibling::table").css('tr')
            if trs:
                headers = [header.css('::text').extract_first().strip() for header in trs[0].css("td")]
                entries = []
                for tr in trs[1:]:
                    row = {}
                    for index, td in enumerate(tr.css('td')):
                        row[headers[index]] = td.css("::text").extract_first().strip()
                    entries.append(row)
                resources[catname] = entries
        collection['personal_resources'] = resources

        request = scrapy.Request('https://schuldatenbank.sachsen.de/index.php?id=460',
                                 meta={'cookiejar': response.meta['cookiejar']},
                                 callback=self.parse_teach_learn,
                                 dont_filter=True)
        request.meta['collection'] = collection

        yield request

    def parse_teach_learn(self, response):
        collection = response.meta['collection']
        ags = []

        tables = response.css('#content table')#[2].css('tr')[2:]#first 2 rows are heading
        if (len(tables) > 2):
            ag_entries = response.css('#content table')[2].css('tr')[2:]
            for tr in ag_entries:
               ags.append(tr.css('.ssdb_02::text').extract_first())
            collection['ag'] = ags
        request = scrapy.Request('https://schuldatenbank.sachsen.de/index.php?id=430',
                                 meta={'cookiejar': response.meta['cookiejar']},
                                 callback=self.parse_students,
                                 dont_filter=True)
        request.meta['collection'] = collection
        request.meta['year'] = 2016

        yield request

    def parse_students(self, response):
        collection = response.meta.get('collection', {})
        current_year = response.meta.get('year')
        previous_year = current_year - 1 if current_year != 2013 else None

        if current_year != 2016:
            tables = response.css('table.ssdb_02')
            collected_data = []
            students_count_table = tables[0]
            rows = students_count_table.css('tr')
            headers = [h.strip() for h in rows[0].css('td::text').extract()]
            for row in rows[1:]:
                tds = row.css("td")
                row = {}
                # only get the rows that contain only raw data, no aggregates/ percentages
                if len(tds) == len(headers):
                    for index, td in enumerate(tds):
                        row[headers[index]] = td.css("::text").extract_first().strip()
                    collected_data.append(row)

            student_information = collection.get('student_information', {})
            student_information[str(current_year)] = collected_data
            collection['student_information'] = student_information

        if previous_year:
            request = scrapy.FormRequest.from_response(
                response,
                formname='jahr',
                formdata={"jahr": str(previous_year)},
                meta={'cookiejar': response.meta['cookiejar']},
                dont_filter=True,
                callback=self.parse_students)
            request.meta['collection'] = collection
            request.meta['year'] = previous_year
            yield request

        else:
            request = scrapy.Request("https://schuldatenbank.sachsen.de/index.php?id=510",
                                     meta={'cookiejar': response.meta['cookiejar']},
                                     callback=self.parse_partners_overview,
                                     dont_filter=True)
            request.meta['collection'] = collection
            yield request

    def parse_partners_overview(self, response):
        collection = response.meta.get('collection', {})
        forms = len(response.css('#tabform'))
        requests = []
        for formnumber in range(1, forms):
            request = scrapy.FormRequest.from_response(
                response,
                formnumber=formnumber + 1,  # first form is search, skip that
                meta={'cookiejar': response.meta['cookiejar']},
                dont_filter=True,
                callback=self.parse_partners_detail)
            request.meta['collection'] = collection
            requests.append(request)

        collection['partners'] = []
        yield scrapy.FormRequest.from_response(
            response,
            formnumber=1,  # first form is search, skip that
            meta={'cookiejar': response.meta['cookiejar'],
                  'collection': collection,
                  'stash': requests},
            dont_filter=True,
            callback=self.parse_partners_detail)

    def parse_partners_detail(self, response):
        meta = response.meta
        stash = response.meta.get('stash')

        if "5130" in response.url:
            data = []
            table = response.css("table.ssdb_02")
            for row in table.css("tr"):
                row_data = {}
                tds = row.css("td")
                row_key = tds[0].css("::text").extract_first().strip()
                row_data[row_key] = cleanjoin(tds[1:].css("::text").extract())
                data.append(row_data)
            meta['collection']['partners'].append(data)
        else:
            # TODO: This is an Eltern/SV page, parse it differently
            pass

        if len(stash) > 0:
            next_request = meta['stash'].pop()
            next_request.meta['stash'] = meta['stash']
            yield next_request
        else:
            request = scrapy.Request("https://schuldatenbank.sachsen.de/index.php?id=470",
                                     meta={'cookiejar': response.meta['cookiejar']},
                                     callback=self.parse_competitions_overview,
                                     dont_filter=True)
            request.meta['collection'] = meta['collection']
            yield request

    def parse_competitions_overview(self, response):
        collection = response.meta.get('collection', {})
        forms = len(response.css('#tabform'))

        requests = []
        for formnumber in range(1, forms):
            request = scrapy.FormRequest.from_response(
                response,
                formnumber=formnumber + 1,
                meta={'cookiejar': response.meta['cookiejar']},
                dont_filter=True,
                callback=self.parse_competition_detail)
            request.meta['collection'] = collection
            requests.append(request)

        collection['competitions'] = []
        yield scrapy.FormRequest.from_response(
            response,
            formnumber=1,
            meta={'cookiejar': response.meta['cookiejar'],
                  'collection': collection,
                  'stash': requests},
            dont_filter=True,
            callback=self.parse_competition_detail)

    def parse_competition_detail(self, response):
        meta = response.meta
        stash = response.meta.get('stash')

        data = {
            'name': response.css("#content > div:nth-child(3) > b::text").extract_first(),
            'results': []
        }
        table = response.css("table.ssdb_02")
        headers = [text.strip() for text in table.css(" tr:first-child td::text").extract()]
        for tr_index, row in enumerate(table.css("tr")):
            if tr_index == 0:
                # header
                continue
            row_data = {}
            for td_index, td in enumerate(row.css("td")):
                row_data[headers[td_index]] = cleanjoin(td.css("::text").extract())
            data['results'].append(row_data)
        meta['collection']['competitions'].append(data)

        if len(stash) > 0:
            next_request = meta['stash'].pop()
            next_request.meta['stash'] = meta['stash']
            yield next_request
        else:
            yield meta['collection']