import csv

import requests


# See https://www.python.org/dev/peps/pep-0318/#examples
def singleton(cls):
    instances = {}
    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getinstance


@singleton
class NordRheinWestfalenHelper:
    sources = {
        "rechtsform": "https://www.schulministerium.nrw.de/BiPo/OpenData/Schuldaten/key_rechtsform.csv",
        "schulform": "https://www.schulministerium.nrw.de/BiPo/OpenData/Schuldaten/key_schulformschluessel.csv"
    }

    def __init__(self):
        self.mappings = self.load_data()

    def load_data(self):
        return {
            key: self.get_map(url)
            for key, url in self.sources.items()
        }

    def get_map(self, url):
        response = requests.get(url)
        response.encoding = 'utf-8'
        # skip the first line which contains information about
        # the separator
        # and the second line which contains the headers
        reader = csv.reader(response.text.splitlines()[2:], delimiter=';')
        return {line[0]: line[1] for line in reader}

    def resolve(self, data_type, key):
        return self.mappings.get(data_type).get(key)