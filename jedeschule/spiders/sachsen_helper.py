import requests

from jedeschule.utils import singleton


@singleton
class SachsenHelper:
    def __init__(self):
        self.school_types = self.load_school_types()

    def resolve_school_type(self, key):
        return self.school_types.get(key)

    def load_school_types(self):
        response = requests.get("https://schuldatenbank.sachsen.de/api/v1/key_tables/school_types?format=json")
        data = response.json()
        return {int(entry['key']): entry['label'] for entry in data}