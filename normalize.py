import json
import csv
import os
from collections import namedtuple

test = """
id
name
address
address2
zip
city
school_type
phone
fax
email
website
pupils_no
pupils_ts
"""

BASE_PATH = '.'

School = namedtuple('School',
                    ['id', 'name', 'address', 'address2', 'zip', 'city', 'school_type', 'phone', 'fax', 'email',
                     'website'])


def normalize(state):
    with open(os.path.join(BASE_PATH, 'data/{}.json'.format(state))) as f:
        data = json.load(f)
    with open(os.path.join(BASE_PATH, 'data/{}.csv'.format(state)), 'w') as f:
        output = csv.writer(f)
        output.writerow(School._fields)

        for row in data:
            s = School(
                id=row['info']['id'],
                name=row['info']['name'],
                address=row['info']['address'],
                address2='',
                zip=row['info'].get('zip'),
                city=row['info'].get('city'),
                school_type=row['info']['school_type'],
                phone=row['info']['phone'],
                fax=row['info']['fax'],
                email=row['info']['email'],
                website=row['info']['website']
            )

            output.writerow(s)


def normalize_mv():
    state = 'mecklenburg-vorpommern'
    with open(os.path.join(BASE_PATH, 'data/{}.json'.format(state))) as f:
        data = json.load(f)
    with open(os.path.join(BASE_PATH, 'data/{}.csv'.format(state)), 'w') as f:
        output = csv.writer(f)
        output.writerow(School._fields)

        for row in data:

            if isinstance(row['Dst-Nr.:'], float):
                school_id = int(row['Dst-Nr.:'])
            else:
                school_id = row['Dst-Nr.:']

            try:
                schulart = row['Schulart/ Org.form']
            except:
                schulart = row['Schulart/\nOrg.form']

            s = School(
                id='MV-{}'.format(school_id),
                name=row['Schulname'],
                address=row['Straße, Haus-Nr.'],
                address2='',
                zip=row['PLZ'],
                city=row['Ort'],
                school_type=schulart,
                phone=row['Telefon'],
                fax=row['Telefax'],
                email=row['E-Mail'],
                website=row['Homepage']
            )

            output.writerow(s)


if __name__ == '__main__':
    normalize('brandenburg')
    normalize('niedersachsen')
    normalize('thueringen')
    normalize('saarland')
    normalize('schleswig-holstein')
    normalize_mv()
