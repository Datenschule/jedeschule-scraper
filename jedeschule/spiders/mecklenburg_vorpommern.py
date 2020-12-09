import scrapy
from scrapy import Item
import wget
import xlrd
import json
import os
from jedeschule.items import School


# [2020-12-05, htw-kevkev]
#   Created separate mv scraper to get url of download file dynamically (is hopefully more stable)
#   Added output to regular School pipeline instead of individual json
#   FURTHER TO-DOs:
#      - adjust run.py for mv
#         - get_mv method can be deleted and removed from main
#         - "yield runner.crawl(MecklenburgVorpommernSpider)" can be added to crawl method

class MecklenburgVorpommernSpider(scrapy.Spider):
    name = "mecklenburg-vorpommern"
    base_url = 'https://www.regierung-mv.de/Landesregierung/bm/Bildung/Schule'
    start_urls = [base_url]

    def parse(self, response):
        # get titles of all a elements first
        titles = response.css('a::attr(title)').extract()

        # our relevant title might contain "Download" and "Schulverzeichnis"
        for title in titles:
            if "Download" in title:
                if "Schulverzeichnis" in title:
                    relevant_title = title
                    break

        href = response.css('a[title="' + relevant_title + '"]::attr(href)').extract()[0]

        filename = 'mv.xlsx'
        url_mv = 'https://www.regierung-mv.de' + href
        wget.download(url_mv, filename)

        ### OLD HARDCODED LEGEND: obsolet as legend sheet of xlsx is stored in a dict
        # legend = {
        #     'schulart': {
        #         'Agy': 'Abendgymnasium',
        #         'FöL': 'Schule mit dem Förderschwerpunkt Lernen',
        #         'FöS': 'Schule mit dem Förderschwerpunkt Sehen',
        #         'FöSp': 'Schule mit dem Förderschwerpunkt Sprache',
        #         'FöK': 'Schule mit dem Förderschwerpunkt körperliche und motorische Entwicklung',
        #         'FöK/GS': 'Schule mit dem Förderschwerpunkt körperliche und motorische Entwicklung mit Grundschule',
        #         'FöG': 'Schule mit dem Förderschwerpunkt geistige Entwicklung',
        #         'FöG/FöKr': 'Schule mit dem Förderschwerpunkt geistige Entwicklung und dem Unterricht kranker Schülerinnen und Schüler',
        #         'FöKr': 'Schule mit dem Förderschwerpunkt Unterricht kranker Schülerinnen und Schüler',
        #         'FöL/FöG': 'Schule mit dem Förderschwerpunkt Lernen und  dem Förderschwerpunkt geistige Entwicklung',
        #         'FöL/FöKr':	'Schule mit dem Förderschwerpunkt Lernen und dem Förderschwerpunkt Unterricht kranker Schülerinnen und Schüler',
        #         'FöL/FöV': 'Schule mit dem Förderschwerpunkt emotionale und soziale Entwicklung und dem Förderschwerpunkt Lernen',
        #         'FöV': 'Schule mit dem Förderschwerpunkt emotionale und soziale Entwicklung',
        #         'FöV/FöKr': 'Schule mit dem Förderschwerpunkt emotionale und soziale Entwicklung und dem Förderschwerpunkt Unterricht kranker Schülerinnen und Schüler',
        #         'FöV/FöL': 'Schule mit dem Förderschwerpunkt emotionale und soziale Entwicklung und dem Förderschwerpunkt Lernen)',
        #         'FöL/FöV/FöKr': 'Schule mit den Förderschwerpunkten Lernen, dem Förderschwerpunkt emotionale und soziale Entwicklung sowie dem Förderschwerpunkt Unterricht kranker Schülerinnen und Schüler',
        #         'FöL/FöV/FöSp': 'Schule mit den Förderschwerpunkten Lernen, dem Förderschwerpunkt emotionale und soziale Entwicklung sowie dem Förderschwerpunkt Sprache',
        #         'FöH': 'Schule mit dem Förderschwerpunkt Hören',
        #         'GS': 'Grundschule',
        #         'GS/OS': 'Grundschule mit schulartunabhängiger Orientierungsstufe',
        #         'GS/FöSp': 'Grundschule mit selbstständigen Klassen mit dem Förderschwerpunkt Sprache',
        #         'GS/OS/Gy': 'Grundschule mit schulartunabhängiger Orientierungsstufe und Gymnasium',
        #         'Gy': 'Gymnasium',
        #         'Gy/OS': 'Gymnasium mit schulartunabhängiger Orientierungsstufe (z.B. auch Musikgymnasien und Gymnasien für hochbegabte Schülerinnen und Schüler)',
        #         'Gy/GS/OS': 'Gymnasium mit Grundschule und schulartunabhängiger Orientierungsstufe',
        #         'Gy/RegS': 'Gymnasium mit Regionaler Schule (z.B. auch Sportgymnasien)',
        #         'Gy/RegS/GS': 'Gymnasium mit Regionaler Schule und Grundschule',
        #         'IGS': 'Integrierte Gesamtschule',
        #         'IGS/GS': 'Integrierte Gesamtschule mit Grundschule',
        #         'IGS/GS/FöG': 'Integrierte Gesamtschule mit Grundschule  und Schule mit dem Förderschwerpunkt geistige Entwicklung',
        #         'KGS': 'Kooperative Gesamtschule',
        #         'KGS/GS': 'Kooperative Gesamtschule mit Grundschule',
        #         'KGS/GS/\nFöL': 'Kooperative Gesamtschule mit Grundschule und Schule mit dem Förderschwerpunkt Lernen',
        #         'RegS': 'Regionale Schule',
        #         'RegS/GS': 'Regionale Schule mit Grundschule',
        #         'RegS/Gy': 'Regionale Schule mit Gymnasium',
        #         'WS': 'Waldorfschule',
        #         '': 'unknown'
        #     },
        #     'schulamt': {
        #         'GW': 'Greifswald',
        #         'NB': 'Neubrandenburg',
        #         'RO': 'Rostock',
        #         'SN': 'Schwerin',
        #         'BM': 'Ministerium für Bildung, Wissenschaft und Kultur',
        #         '': 'unknown'
        #     },
        #     'landkreis': {
        #         'HRO': 'Hansestadt Rostock',
        #         'SN': 'Landeshauptstadt Schwerin',
        #         'LRO': 'Landkreis Rostock',
        #         'LUP': 'Landkreis Ludwigslust-Parchim',
        #         'MSE': 'Landkreis Mecklenburgische Seenplatte',
        #         'NWM': 'Landkreis Nordwestmecklenburg',
        #         'VG': 'Landkreis Vorpommern-Greifswald',
        #         'VR': 'Landkreis Vorpommern-Rügen',
        #         '': 'unknown'
        #     }
        # }

        workbook = xlrd.open_workbook(filename)
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

        # with open('data/mecklenburg-vorpommern2.json', 'w') as json_file:
        #     json_file.write(json.dumps(data))
        os.remove(filename)

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