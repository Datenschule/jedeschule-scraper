import json

import requests
from requests import HTTPError


def load_data():
    with open('/tmp/jedeschule-changes.json') as infile:
        return json.load(infile)


def fetch_data(school_id):
    response = requests.get(f"https://jedeschule.codefor.de/schools/{school_id}")
    response.raise_for_status()
    return response.json()


def sort_dict(data):
    return {key: value for key, value in sorted(data.items(), key=lambda k: k[0])}


def get_clean_item(data):
    return set({key: value for key, value in data.items() if value is not None})


def compare_schools(new_school, old_school):
    new_school = sort_dict(new_school)
    old_school = sort_dict(old_school)

    new_values = get_clean_item(new_school)
    old_values = get_clean_item(old_school)

    differences = new_values ^ old_values
    if not differences:
        print(' no changes \n')
        return

    print(f"Difference: {differences}")
    print(f"Old: {old_school}")
    print(f"New: {new_school}")


def main():
    data = load_data()
    for school in data[:10]:
        school_id = school.get('info').get('id')

        print()
        print('#'*10, f'Comparing {school_id}')

        upstream_data = {}
        try:
            upstream_data = fetch_data(school_id)
            upstream_data.pop('raw')
        except HTTPError as e:
            print(f"WARN: Could not fetch old data for school-id {school_id}: {e}")
            print()

        compare_schools(school.get('info'), upstream_data)


if __name__ == "__main__":
    main()
