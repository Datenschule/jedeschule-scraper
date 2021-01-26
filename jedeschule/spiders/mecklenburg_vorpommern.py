import scrapy
from scrapy import Item
import xlrd

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class MecklenburgVorpommernSpider(SchoolSpider):
    name = "mecklenburg-vorpommern"
    base_url = 'https://www.regierung-mv.de/Landesregierung/bm/Bildung/Schule'
    start_urls = [base_url]

    def parse(self, response):
        # get titles of all a elements first
        titles = response.css('a::attr(title)').extract()

        # our relevant title must contain "Download" and "Schulverzeichnis"
        relevant_title = next(title for title in titles
                              if "Download" in title
                              and "Schulverzeichnis" in title)

        href = response.css(f'a[title="{relevant_title}"]::attr(href)').extract_first()

        url = f"https://www.regierung-mv.de{href}"
        yield scrapy.Request(url, callback=self.parse_xml)

    def parse_xml(self, response: scrapy.http.Response):
        workbook = xlrd.open_workbook(file_contents=response.body)
        # get all sheet names of workbook rather than hardcoding the names
        sheets = workbook.sheet_names()
        sheet_legend = ''
        for sheet in sheets:
            if 'Legende' in sheet:
                sheet_legend = workbook.sheet_by_name(sheet)
                break

        # get values of legend sheet to map values later
        # simple approach as all values in one dict rather than one dict per "schulamt", "landkreis", etc. (there shouldn't be any duplicates)
        legend = {}
        for row_number in range(sheet_legend.nrows):
            legend_key = sheet_legend.cell(row_number, 0).value.strip()
            legend_value = sheet_legend.cell(row_number, 1).value
            if not (legend_key == '' or legend_value == ''):
                entry = {legend_key: legend_value}
                legend.update(entry)

        relevant_sheets = []
        for sheet in sheets:
            # when sheet name contains schulverzeichnis it's relevant to be parsed
            if 'Schulverzeichnis' in sheet:
                relevant_sheets.append(sheet)

        data = []
        # iterate through all sheets of workbook
        for sheet in relevant_sheets:
            worksheet = workbook.sheet_by_name(sheet)

            # identify key row number, column number and values
            for row_number in range(worksheet.nrows):
                for col_number in range(worksheet.ncols):
                    cell_value = worksheet.cell(row_number,col_number).value
                    # key row should include 'Schulname'
                    if cell_value == 'Schulname':
                        # headers of columns differ sometimes (e.g. new line)
                        keys = [v.value.replace("\n", " ") for v in worksheet.row(row_number)]
                        row_of_keys = row_number
                        column_of_schulname = col_number
                        break
                    else:
                        continue

            # identify last relevant row of sheet
            for row_number, cell in enumerate(worksheet.col(column_of_schulname)):
                if row_number <= row_of_keys:
                    continue
                elif cell.value != '':
                    continue
                else:
                    last_row_of_sheet = row_number-1

            for row_number in range(worksheet.nrows):
                # start with row after headlines
                if row_number <= row_of_keys:
                    continue
                # end with last row which has a value in 'schulname'
                elif row_number >= last_row_of_sheet:
                    break
                row_data = {}
                for col_number, cell in enumerate(worksheet.row(row_number)):
                    row_data[keys[col_number]] = cell.value

                # converting values via legend dict
                # exeptions necessary as there are values which are not in legend sheet
                # missing values in legend sheet are set to 'unknown'
                try:
                    row_data['Schul-behörde'] = legend[row_data['Schul-behörde'].replace('\n','')]
                except:
                    row_data['Schul-behörde'] = 'unknown'

                try:
                    row_data['Landkreis/ kreisfr. Stadt'] = legend[row_data['Landkreis/ kreisfr. Stadt'].replace('\n','')]
                except:
                    row_data['Landkreis/ kreisfr. Stadt'] = 'unknown'

                try:
                    if not 'BLS' in sheet:
                        row_data['Schulart/ Org.form'] = legend[row_data['Schulart/ Org.form'].replace('\n','')]
                    else:
                        row_data['Schulart/ Org.form'] = 'Berufliche Schule'
                except:
                    row_data['Schulart/ Org.form'] = 'unknown'

                # of course only rows with a schulname should be added
                if row_data['Schulname'] != '':
                    data.append(row_data)

        for row in data:
            yield row

    @staticmethod
    def normalize(item: Item) -> School:
        dst = str(item.get('Dst-Nr.:')).replace('.0','')
        plz = str(item.get('Plz')).replace('.0','')
        return School(name=item.get('Schulname'),
                      id='MV-{}'.format(dst),
                      address=item.get('Straße, Haus-Nr.'),
                      address2='',
                      zip=plz,
                      city=item.get('Ort'),
                      website=item.get('Homepage'),
                      email=item.get('E-Mail'),
                      school_type=item.get('Schulart/ Org.form'),
                      fax=item.get('Telefax'),
                      phone=item.get('Telefon'),
                      provider=item.get('Schul-behörde'),
                      director=item.get('Schulleitung'))