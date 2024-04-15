import csv

import requests

from jedeschule.utils import singleton




@singleton
class NordRheinWestfalenHelper:
    sources = {
        "rechtsform": "https://www.schulministerium.nrw.de/BiPo/OpenData/Schuldaten/key_rechtsform.csv",
        "schulform": "https://www.schulministerium.nrw.de/BiPo/OpenData/Schuldaten/key_schulformschluessel.csv",
    }

    def __init__(self):
        self.mappings = self.load_data()

    def get_provider(self):
        """ Provider is a bit special because the csv table contains more than
        two columns"""
        url = "https://www.schulministerium.nrw.de/BiPo/OpenData/Schuldaten/key_traeger.csv"
        response = requests.get(url)
        response.encoding = 'utf-8'
        # skip the first line which contains information about
        # the separator
        # and the second line which contains the headers
        reader = csv.reader(response.text.splitlines()[2:], delimiter=';')
        return {line[0]: " ".join(line[n] for n in range(1,4)).strip() for line in reader}

    def load_data(self):
        base_data = {
            key: self.get_map(url)
            for key, url in self.sources.items()
        }
        base_data['provider'] = self.get_provider()
        return base_data

    def get_map(self, url):
        # TODO: This could/should be consolidated with the `get_provider` method
        # to be more generic.
        response = requests.get(url)
        response.encoding = 'utf-8'
        # skip the first line which contains information about
        # the separator
        # and the second line which contains the headers
        reader = csv.reader(response.text.splitlines()[2:], delimiter=';')
        return {line[0]: line[1] for line in reader}

    def resolve(self, data_type, key):
        return self.mappings.get(data_type).get(key)