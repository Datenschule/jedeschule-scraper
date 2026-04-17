from abc import ABC

import scrapy
from scrapy import Item

from jedeschule.items import School


class SchoolSpider(scrapy.Spider, ABC):
    #: ISO 3166-2:DE code (no ``DE-`` prefix). Set on each Land spider; persisted as ``schools.state_key``.
    state_key: str = ""

    def make_school_id(self, tail: str) -> str:
        """``{state_key}-{tail}`` — same prefix as stored ``state_key`` / composed ``id``."""
        return f"{self.state_key}-{tail}"

    def normalize(self, item: Item) -> School:
        raise NotImplementedError
