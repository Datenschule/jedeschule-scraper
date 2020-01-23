import pandas as pd
import wget
import os
import xlrd
import sys
from collections import namedtuple
import csv
import json


def download_allgemeine_Schulen():
    allgemeine_Schulen     = 'allgemeine_Schulen.xlsx'
    url_allgemeine_Schulen = 'https://statistik.hessen.de/sites/statistik.hessen.de/files/Verz-6_19.xlsx'
    wget.download(url_allgemeine_Schulen, allgemeine_Schulen)
    workbook               = xlrd.open_workbook(allgemeine_Schulen)
    worksheet              = workbook.sheet_by_name('Schulverzeichnis')
    keys = ['Schul-nummer', 'Rechtsform\n1 = öffentlich\n2 = privat', 'Name der Schule', 'PLZ', 'Schulort', 'Straße, Hausnummer', 'Telefon-vorwahl', 'Telefon-nummer', 'Fax', 'Email Adresse']
    school_type_keys = ['Grundschulen', 'Hauptschule', 'Mittelstufen-schule', 'Realschule', 'Gymnasien', 'Förderschulen']
    data = []

    print('allgemeine Schulen')

    for row_number in range(worksheet.nrows):
        if row_number == 0 or row_number == 1:
            continue
        row_data = {}
        schooltype_string = ""
        for col_number, cell in enumerate(worksheet.row(row_number)):
            column = worksheet.row(0)[col_number].value
            if column in keys:
                if column == 'Rechtsform\n1 = öffentlich\n2 = privat':
                    if cell.value == '1':
                        row_data['Schulträger'] = 'öffentlich'
                    else:
                        row_data['Schulträger'] = 'privat'
                else:
                    row_data[column] = cell.value
            elif column in school_type_keys and cell.value != '':
                if column == 'Grundschulen':
                    schooltype_string += ' Grundschule'
                elif column == 'Mittelstufen-schule':
                    schooltype_string += ' Mittelstufenschule'
                elif column == 'Gymnasien':
                    schooltype_string += ' Gymnasium'
                elif column == 'Förderschulen':
                    schooltype_string += ' Förderschule'
                else:
                    schooltype_string += (' ' + column)

        row_data['Internetseite'] = ''
        row_data['Schultyp'] = schooltype_string[1:]
        data.append(row_data)

    os.remove(allgemeine_Schulen)
    return data


def download_freie_allgemeine_Schulen():
    freie_allgemeine_Schulen     = 'freie_allgemeine_Schulen.xlsx'
    url_freie_allgemeine_Schulen = 'https://statistik.hessen.de/sites/statistik.hessen.de/files/Verz-9_16.xlsx'
    wget.download(url_freie_allgemeine_Schulen, freie_allgemeine_Schulen)
    workbook                     = xlrd.open_workbook(freie_allgemeine_Schulen)
    worksheet                    = workbook.sheet_by_name('Adressen 2016')
    keys = ['Schul Nr.', 'Rechts-\nform', 'Schulname', 'PLZ', 'Ort', 'Straße', 'TelVW', 'TelNr', 'FaxNr', 'Email Adresse']
    school_type_keys = ['Vorklassen', 'Grundschulen', 'Hauptschulen', 'Schulen für Erwachsene', 'Realschulen', 'Gymnasien', 'Förderschulen']
    data = []

    print('freie allgemeine Schulen')
    
    for row_number in range(worksheet.nrows):
        if row_number == 0 or row_number == 1:
            continue
        row_data = {}
        schooltype_string = ""
        for col_number, cell in enumerate(worksheet.row(row_number)):
            column = worksheet.row(1)[col_number].value
            if column in keys:
                if column == 'Rechts-\nform':
                    if cell.value == '1':
                        row_data['Schulträger'] = 'öffentlich'
                    else:
                        row_data['Schulträger'] = 'privat'
                elif column == 'Schul Nr.':
                    row_data['Schul-nummer'] = cell.value
                elif column == 'Schulname':
                    row_data['Name der Schule'] = cell.value
                elif column == 'Ort':
                    row_data['Schulort'] = cell.value
                elif column == 'Straße':
                    row_data['Straße, Hausnummer'] = cell.value
                elif column == 'TelVW':
                    row_data['Telefon-vorwahl'] = cell.value
                elif column == 'TelNr':
                    row_data['Telefon-nummer'] = cell.value
                elif column == 'FaxNr':
                    row_data['Fax'] = cell.value
                else:
                    row_data[column] = cell.value
            elif column in school_type_keys and cell.value != '':
                if column == 'Vorklassen':
                    schooltype_string += ' Vorklasse'
                elif column == 'Grundschulen':
                    schooltype_string += ' Grundschule'
                elif column == 'Gymnasien':
                    schooltype_string += ' Gymnasium'
                elif column == 'Hauptschulen':
                    schooltype_string += ' Hauptschule'
                elif column == 'Schulen für Erwachsene':
                    schooltype_string += ' Schule für Erwachsene'
                elif column == 'Realschulen':
                    schooltype_string += ' Realschule'
                elif column == 'Förderschulen':
                    schooltype_string += ' Förderschule'
        
        row_data['Internetseite'] = ''
        row_data['Schultyp'] = schooltype_string[1:]
        data.append(row_data)
    
    os.remove(freie_allgemeine_Schulen)
    return data


def download_berufliche_Schulen():
    berufliche_Schulen     = 'berufliche_Schulen.xlsx'
    url_berufliche_Schulen = 'https://statistik.hessen.de/sites/statistik.hessen.de/files/Verz-7_19.xlsx'
    wget.download(url_berufliche_Schulen, berufliche_Schulen)
    workbook               = xlrd.open_workbook(berufliche_Schulen)
    worksheet              = workbook.sheet_by_name('Schulverzeichnis')
    keys = ['Schul-nummer', 'Rechtsform\n1 = öffentlich\n2 = privat', 'Name der Schule', 'PLZ', 'Schulort', 'Straße, Hausnummer', 'Telefon-vorwahl', 'Telefon\nnummer', 'Fax', 'Email Adresse', 'Internetseite']
    school_type_keys = ['Berufliche Gymnasien', 'Berufsfach-schulen', 'Berufs-schulen', 'Fachober-schulen', 'Fachschulen']
    data = []

    print('berufliche Schulen')

    for row_number in range(worksheet.nrows):
        if row_number == 0 or row_number == 1:
            continue
        row_data = {}
        schooltype_string = ""
        for col_number, cell in enumerate(worksheet.row(row_number)):
            column = worksheet.row(0)[col_number].value
            if column in keys:
                if column == 'Rechtsform\n1 = öffentlich\n2 = privat':
                    if cell.value == '1':
                        row_data['Schulträger'] = 'öffentlich'
                    else:
                        row_data['Schulträger'] = 'privat'
                elif column == 'Telefon\nnummer':    
                    row_data['Telefon-nummer'] = cell.value
                else:
                    row_data[column] = cell.value
            elif column in school_type_keys and cell.value != '':
                if column == 'Berufliche Gymnasien':
                    schooltype_string += ' Berufliches Gymnasium'
                elif column == 'Berufsfach-schulen':
                    schooltype_string += ' Berufsfachschule'
                elif column == 'Berufs-schulen':
                    schooltype_string += ' Berufsschule'
                elif column == 'Fachober-schulen':
                    schooltype_string += ' Fachoberschule'
                else:
                    schooltype_string += ' Fachschule'

        row_data['Schultyp'] = schooltype_string[1:]
        data.append(row_data)

    os.remove(berufliche_Schulen)
    return data


def normalize(data):
    BASE_PATH = '../../'
    School = namedtuple('School',
                    ['id', 'name', 'address', 'address2', 'zip', 'city', 'school_type', 'phone', 'fax', 'email',
                     'website'])

    with open(os.path.join(BASE_PATH, 'data/{}.csv'.format('hessen')), 'w', newline='', encoding='utf-8') as f:
        output = csv.writer(f)
        output.writerow(School._fields)
        for row in data:
            
            s = School(
                id          = 'HE-{}'.format(str(int(row['Schul-nummer']))),
                name        = row['Name der Schule'],
                address     = row['Straße, Hausnummer'],
                address2    = '',
                zip         = int(row['PLZ']),
                city        = row['Schulort'],
                school_type = row['Schultyp'],
                phone       = fix_phone_number(row['Telefon-vorwahl']) + fix_phone_number(row['Telefon-nummer']),
                fax         = fix_phone_number(row['Fax']),
                email       = row['Email Adresse'],
                website     = row['Internetseite']
            )

            output.writerow(s)


def fix_phone_number(number):
    result = ""
    if isinstance(number, float) or isinstance(number, int):
        result = str(int(number))
    else:
        result = number.replace(' ', '')
    return result
    

if __name__ == '__main__':
    data = []
    data += download_allgemeine_Schulen()
    data += download_freie_allgemeine_Schulen()
    data += download_berufliche_Schulen()
    normalize(data)

