import scrapy
from scrapy import Item
import xlrd

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


def as_string(value: str):
    try:
        return str(int(value))
    except ValueError:
        return value


class MecklenburgVorpommernSpider(SchoolSpider):
    name = "mecklenburg-vorpommern"
    # The state provides the data as an Excel file. The current year's
    # data is for sale, all older version are free to download.
    # We use the free data from 2022/2023
    # An overview of all available files can be found here:
    #   https://www.statistischebibliothek.de/mir/receive/MVSerie_mods_00000396
    # Official documentation on all available data here:
    #   https://www.laiv-mv.de/Statistik/Veröffentlichungen/Verzeichnisse/
    base_url = "https://www.statistischebibliothek.de/mir/servlets/MCRFileNodeServlet/MVHeft_derivate_00007470/V044%202023%2000.xlsx"
    start_urls = [base_url]

    def parse(self, response):
        workbook = xlrd.open_workbook(file_contents=response.body)
        data_sheet = workbook.sheet_by_name("Verzeichnis allg bild Schulen")
        headers = [data_sheet.cell(0, c).value for c in range(data_sheet.ncols)]
        for row_number in range(1, data_sheet.nrows):
            yield {
                headers[c]: data_sheet.cell(row_number, c).value
                for c in range(data_sheet.ncols)
            }

    @staticmethod
    def normalize(item: Item) -> School:
        return School(
            name=item.get("NAME1"),
            id="MV-{}".format(as_string(item.get("DIENSTSTELLEN-NUMMER"))),
            address=item.get("STRASSE"),
            address2="",
            zip=as_string(item.get("PLZ")).zfill(5),
            city=item.get("ORT"),
            website=item.get("INTERNET"),
            email=item.get("E-MAIL-ADRESSE"),
            phone=item.get("TELEFON"),
            director=item.get("SCHULLEITER/-IN"),
        )
