import json

import requests
from requests import HTTPError


def load_data():
    with open("/tmp/jedeschule-changes.json") as infile:
        return json.load(infile)


def fetch_data(school_id):
    response = requests.get(f"https://jedeschule.codefor.de/schools/{school_id}")
    response.raise_for_status()
    return response.json()


def get_clean_item(data):
    return {
            key: value
            for key, value in data.items()
            if value is not None and key != "update_timestamp"
        }


def dict_diff(dict1, dict2):
    all_keys = set(dict1.keys()) | set(dict2.keys())

    differences = {}
    for key in all_keys:
        val1 = dict1.get(key, None)
        val2 = dict2.get(key, None)

        if val1 != val2:
            differences[key] = (val1, val2)

    return differences


def compare_schools(new_school, old_school):
    new_values = get_clean_item(new_school)
    old_values = get_clean_item(old_school)

    differences = dict_diff(new_values, old_values)
    if len(differences) == 0:
        print(" no changes \n")
        return

    print(f"Difference found:")
    print(json.dumps(differences, indent=2))


def main():
    data = load_data()
    for school in data[:10]:
        school_id = school.get("info").get("id")

        print()
        print("#" * 10, f"Comparing {school_id}")

        upstream_data = {}
        try:
            upstream_data = fetch_data(school_id)
        except HTTPError as e:
            print(f"WARN: Could not fetch old data for school-id {school_id}: {e}")
            print()

        compare_schools(school.get("info"), upstream_data)


if __name__ == "__main__":
    main()
