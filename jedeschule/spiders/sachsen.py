import json

from scrapy import Item

from jedeschule.spiders.sachsen_helper import SachsenHelper
from jedeschule.spiders.school_spider import SchoolSpider
from jedeschule.items import School


class SachsenSpider(SchoolSpider):
    name = "sachsen"

    # URL was created via https://schuldatenbank.sachsen.de/index.php?id=30
    start_urls = ['https://schuldatenbank.sachsen.de/api/v1/schools?owner_extended=yes&school_type_key%5B%5D=11&school_type_key%5B%5D=12&school_type_key%5B%5D=15&school_type_key%5B%5D=13&school_type_key%5B%5D=14&school_type_key%5B%5D=16&school_type_key%5B%5D=31&school_type_key%5B%5D=32&school_type_key%5B%5D=33&school_type_key%5B%5D=34&school_type_key%5B%5D=35&school_type_key%5B%5D=36&school_type_key%5B%5D=37&school_type_key%5B%5D=39&school_type_key%5B%5D=21&school_type_key%5B%5D=22&school_type_key%5B%5D=23&school_type_key%5B%5D=24&school_type_key%5B%5D=25&school_type_key%5B%5D=28&school_type_key%5B%5D=42&school_type_key%5B%5D=43&school_type_key%5B%5D=44&building_type_key=01&fields%5B%5D=id&fields%5B%5D=name&fields%5B%5D=school_category_key&fields%5B%5D=school_type_keys&fields%5B%5D=street&fields%5B%5D=postcode&fields%5B%5D=community&fields%5B%5D=community_key&fields%5B%5D=community_part&fields%5B%5D=community_part_key&fields%5B%5D=relocated&fields%5B%5D=phone_identifier_1&fields%5B%5D=phone_code_1&fields%5B%5D=phone_number_1&fields%5B%5D=phone_identifier_2&fields%5B%5D=phone_code_2&fields%5B%5D=phone_number_2&fields%5B%5D=phone_identifier_3&fields%5B%5D=phone_code_3&fields%5B%5D=phone_number_3&fields%5B%5D=fax_code&fields%5B%5D=fax_number&fields%5B%5D=mail&fields%5B%5D=homepage&fields%5B%5D=longitude&fields%5B%5D=latitude&order%5B%5D=name&format=json']

    def parse(self, response, **kwargs):
        for school in json.loads(response.text):
            yield school

    @staticmethod
    def normalize(item: Item) -> School:
        helper = SachsenHelper()
        building = item.get('buildings', [None])[0]
        school = School(name=item.get('name'),
                        id='SN-{}'.format(item.get('id')))
        if building is None:
            return school
        school['address'] = building.get("street")
        school['zip'] = building.get("postcode")
        school['city'] = building.get("community")
        school['email'] = building.get("mail")
        school['website'] = building.get("homepage")
        school['fax'] = "".join([building.get("fax_code") or "", building.get("fax_number") or ""])
        school['phone'] = "".join([building.get("phone_code_1") or "" , building.get("phone_number_1") or  ""])
        school['latitude'] = building.get("latitude")
        school['longitude'] = building.get("longitude")
        school['school_type'] = helper.resolve_school_type(building.get('school_type_keys', [None])[0])

        return school