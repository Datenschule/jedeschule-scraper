import scrapy
import re

from jedeschule.utils import cleanjoin
from scrapy.shell import inspect_response
from jedeschule.items import School
from scrapy import Item


class SachsenSpider(scrapy.Spider):
    name = "sachsen"

    base_url = 'https://schuldatenbank.sachsen.de/'
    start_urls = ['https://schuldatenbank.sachsen.de/index.php?id=2']

    def parse(self, response):
        yield scrapy.FormRequest.from_response(
            response, formcss="#content form", callback=self.parse_schoolist)


    def parse_schoolist(self, response):
        first_ids = response.css('.ssdb_02 form input:nth-child(1) ::attr(value)').extract()
        first_ids_names = response.css('.ssdb_02 form input:nth-child(1) ::attr(name)').extract()
        second_ids = response.css('.ssdb_02 form input:nth-child(2) ::attr(value)').extract()
        second_ids_names = response.css('.ssdb_02 form input:nth-child(2) ::attr(name)').extract()

        for i, first_id in enumerate(first_ids):
            form_url = self.base_url + 'index.php?' + first_ids_names[i] + '=' + str(first_id) + '&' + second_ids_names[i] + '=' + str(second_ids[i])
            yield scrapy.Request(form_url, callback=self.parse_school, meta={'cookiejar': i})


    def parse_school(self, response):
        collection = {'phone_numbers': {}}
        collection['title'] = self.fix_data(response.css("#content h2::text").extract_first().strip())
        collection['data_url'] = response.url
        entries = response.css(".kontaktliste li")
        for entry in entries:
            # Remove the trailing `:` from the key (:-1)
            key = self.fix_data(entry.css("b::text").extract_first(default="kein Eintrag:").strip()[:-1])
         #   values = self.fix_data(entry.css("::text").extract()[1:])
            values = [self.fix_data(value) for value in entry.css("::text").extract()[1:]]
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
        yield collection

        ### IMPORTANT: As the following functions cause duplicates in the data I stopped them from being used

        # students_url = response.xpath('//*[@id="navi"]/div[2]/ul/li[2]/ul/li[1]/a/@href').get()
        # if not students_url:
        #     yield collection
        # else:    
        #     request = scrapy.Request(self.base_url+students_url,
        #                             meta={'cookiejar': response.meta['cookiejar']},
        #                             callback=self.parse_students,
        #                             dont_filter=True)
        #     request.meta['collection'] = collection

        #     yield request


    def parse_students(self, response):
            collection = response.meta.get('collection', {})
            if response.meta.get('year') != None:
                current_year = response.meta.get('year')
            else:
                current_year = response.xpath('//*[@id="content"]/div[1]/form/select/option[1]/@value').get()
            
            if current_year != None:
                previous_year = str(int(current_year) - 1)
                tables = response.css('table.ssdb_02')
                collected_data = []
                
                if tables and tables.get(0):
                    students_count_table = tables[0]
                    rows = students_count_table.css('tr')
                    headers = [h.strip() for h in rows[0].css('td::text').extract()]
                    for row in rows[1:]:
                        tds = row.css("td")
                        row = {}
                        # only get the rows that contain only raw data, no aggregates/ percentages
                        if len(tds) == len(headers):
                            for index, td in enumerate(tds):
                                value = td.css("::text").extract_first()
                                row[headers[index]] = value if value != None else 0
                            collected_data.append(row)

                    student_information = collection.get('student_information', {})
                    student_information[str(current_year)] = collected_data
                    collection['student_information'] = student_information

                if previous_year in response.xpath('//*[@id="content"]/div[1]/form/select/option/@value').getall():
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

            personal_resources_url = response.xpath('//*[@id="navi"]/div[2]/ul/li[2]/ul/li[2]/a/@href').get()
            request = scrapy.Request(self.base_url+personal_resources_url,
                                    meta={'cookiejar': response.meta['cookiejar']},
                                    callback=self.parse_personal_resources,
                                    dont_filter=True)
            request.meta['collection'] = collection

            yield request


    def parse_personal_resources(self, response):
        collection = response.meta['collection']
        resources = {}
        table = response.xpath('//*[@id="content"]/div[1]/table[1]')
        values = [h.strip() for h in table[0].css('td::text').extract()]
        headers = values[:4]
        entries = values[4:]
        collected_data = []

        while entries:
            row = {}
            row[headers[0]] = entries.pop(0)
            row[headers[1]] = entries.pop(0)
            row[headers[2]] = entries.pop(0)
            row[headers[3]] = entries.pop(0)
            collected_data.append(row)
        collection['personal_resources'] = collected_data

        teach_learn_url = response.xpath('//*[@id="navi"]/div[2]/ul/li[2]/ul/li[4]/a/@href').get()
        request = scrapy.Request(self.base_url+teach_learn_url,
                                 meta={'cookiejar': response.meta['cookiejar']},
                                 callback=self.parse_teach_learn,
                                 dont_filter=True)
        request.meta['collection'] = collection

        yield request


    def parse_teach_learn(self, response):
        collection = response.meta['collection']
        ags = []
        table = response.xpath('//*[@id="content"]/div[2]/table/tr/td/text()').getall()
        if (len(table) > 5):
            collection['ag'] = table[5:]

        school_life_url = response.xpath('//*[@id="navi"]/div[2]/ul/li[2]/ul/li[5]/a/@href').get()
        request = scrapy.Request(self.base_url + school_life_url,
                                 meta={'cookiejar': response.meta['cookiejar']},
                                 callback=self.parse_school_life,
                                 dont_filter=True)
        request.meta['collection'] = collection

        yield request


    def parse_school_life(self, response):
        collection = response.meta['collection']
        headers = response.xpath('//*[@id="content"]/div[1]/h2/text()').getall()
        collected_data = []

        bullet_points = response.xpath('//*[@id="content"]/div[1]/ul/li/text()').getall()
        row = {}
        row[headers[0]] = bullet_points
        collected_data.append(row)

        competitions = response.xpath('//*[@id="content"]/div[1]/table/tbody/tr/text()').getall()
        row = {}
        row[headers[1]] = competitions 
        collected_data.append(row)

        collection['school_life'] = collected_data     
        partners_url = response.xpath('//*[@id="navi"]/div[2]/ul/li[2]/ul/li[9]/a/@href').get()
        request = scrapy.Request(self.base_url + partners_url,
                                 meta={'cookiejar': response.meta['cookiejar']},
                                 callback=self.parse_partners,
                                 dont_filter=True)
        request.meta['collection'] = collection

        yield request


    def parse_partners(self, response):
        collection = response.meta['collection']
        table = response.xpath('//*[@id="content"]/div[1]/table')
        collected_data = {}
        cur_header = self.fix_data(response.xpath('//*[@id="content"]/div[1]/table/tr[1]/td/text()').get())
        partners = []

        for td in table.css('td'):            
            new_header = self.fix_data(td.css('.ssdb_02::text').get())
            if new_header and new_header != cur_header:
                    collected_data[cur_header] = partners
                    cur_header = new_header
                    partners = []
            partner = self.fix_data(td.css('.ssdb_03::text').get())
            if partner:
                partners.append(partner)
        collected_data[cur_header] = partners
        collection['partners'] = collected_data

        yield collection


    # fix wrong tabs, spaces and new lines
    def fix_data(self, string):
        if string:
            string = ' '.join(string.split())
            string.replace('\n', '')
        return string


    @staticmethod
    def normalize(item: Item) -> School:
        v = list(item.get('phone_numbers').values())
        phone_numbers = v[0] if len(v) > 0 else None

        address_objects = re.split('\d{5}', item.get('Postanschrift').strip())
        if len(address_objects) == 0:
            address = ''
            zip = ''
            city = ''
        elif len(address_objects) == 1:
            address = ''
            zip = ''
            city = address_objects[0].strip()
        else:
            address = re.split('\d{5}', item.get('Postanschrift'))[0].strip()
            zip = re.findall('\d{5}', item.get('Postanschrift'))[0].strip()
            city = re.split('\d{5}', item.get('Postanschrift'))[1].strip()


        return School(name=item.get('title'),
                      id='SN-{}'.format(item.get('Dienststellenschlüssel')),
                      address=address,
                      zip=zip,
                      city=city,
                      website=item.get('Homepage'),
                      email=item.get('E-Mail'),
                      school_type=item.get('Einrichtungsart'),
                      legal_status=item.get('Rechtsstellung'),
                      provider=item.get('Schulträger'),
                      fax=item.get('Telefax'),
                      phone=phone_numbers,
                      director=item.get('Schulleiter') or item.get('Schulleiter/in'))


