import scrapy


class BrandenburgSpider(scrapy.Spider):
    name = "brandenburg"
    start_urls = ['https://bildung-brandenburg.de/schulportraets/index.php?id=uebersicht']

    def parse(self, response):
        for link in response.xpath('/html/body/div/div[5]/div[2]/div/div[2]/table/tbody/tr/td/a/@href').getall():
            yield scrapy.Request(response.urljoin(link), callback=self.parse_details)

    def parse_details(self, response):
        table = response.xpath('//*[@id="c"]/div/table')
        data = {
            # extract the school ID from the URL
            'id': response.url.rsplit('=', 1)[1]
        }
        for tr in table.css('tr:not(:first-child)'):
            key = tr.css('th ::text').get().replace(':', '').strip()
            value = tr.css('td ::text').getall()
            data[key] = [self.fix_data(part) for part in value]
        yield data

    def fix_data(self, string):
        """
        fix wrong tabs, spaces and backslashes
        fix @ in email addresses
        """
        if string is None:
            return None
        string = ' '.join(string.split())
        return string.replace('\\', '').replace('|at|','@').strip()
