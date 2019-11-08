import scrapy
import re

class BrandenburgSpider(scrapy.Spider):
    name = "brandenburg"
    start_urls = ['https://bildung-brandenburg.de/schulportraets/index.php?id=uebersicht']

    def parse(self, response):
        for link in response.xpath('/html/body/div/div[5]/div[2]/div/div[2]/table/tbody/tr/td/a/@href').getall():
            yield scrapy.Request(response.urljoin(link), callback=self.parse_details)

    def parse_details(self, response):
        table = response.xpath('//*[@id="c"]/div/table')
        # extract the school ID from the URL
        school_id = response.url.rsplit('=', 1)[1]
        name_adresse = table.xpath('//tr[2]/td/text()').getall()
        schulleiter = table.xpath('//tr[3]/td/text()').get() 
        telefon = table.xpath('//tr[4]/td/text()').get()
        fax = table.xpath('//tr[5]/td/text()').get()
        email = table.xpath('//tr[6]/td/a/text()').get()
        internet = table.xpath('//tr[7]/td/a/text()').get()
        landkreis = table.xpath('//tr[8]/td/text()').get()
        schulamt = table.xpath('//tr[9]/td/text()').get()
        schulform = table.xpath('//tr[10]/td/text()').get()
        schultraeger = table.xpath('//tr[11]/td/text()').get()

        data = {
            'id'           : school_id,
            'name'         : self.fix_data(name_adresse[0]), 
            'Adresse'      : self.fix_data(name_adresse[1]+name_adresse[2]),         
            'Schulleiter'  : self.fix_data(schulleiter),
            'Telefon'      : self.fix_data(telefon),
            'Fax'          : self.fix_data(fax),
            'E-Mail'       : self.fix_email(email),
            'Internet'     : internet,
            'Landkreis'    : self.fix_data(landkreis),
            'Schulamt'     : self.fix_data(schulamt),
            'Schulform'    : self.fix_data(schulform),
            'Schultraeger' : self.fix_data(schultraeger)
        }
        yield data

    # fix wrong tabs, spaces and backslashes
    def fix_data(self, string):
        if string != None:
            string = ' '.join(string.split())
            string.replace('\\', '')
            return string
        else:
            return ''

    # fix @ in email adresse
    def fix_email(self, email):
        if email != None:
            return email.replace('|at|','@')
        else:
            return ''