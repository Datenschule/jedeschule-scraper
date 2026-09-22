import re
from urllib.parse import parse_qs, urlparse

import scrapy
from scrapy import Item

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class BayernSpider(SchoolSpider):
    name = "bayern"
    allowed_domains = ["km.bayern.de"]
    school_base_url = "https://www.km.bayern.de/schule/"
    handle_httpstatus_list = [404, 410]

    def __init__(
        self,
        school_numbers=None,
        start_number=1,
        end_number=9999,
        school_number_width=4,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        if school_numbers:
            self.school_numbers = [
                school_number.strip()
                for school_number in school_numbers.split(",")
                if school_number.strip()
            ]
        else:
            number_width = int(school_number_width)
            self.school_numbers = [
                str(school_number).zfill(number_width)
                for school_number in range(int(start_number), int(end_number) + 1)
            ]

    def _iter_school_requests(self):
        for school_number in self.school_numbers:
            yield scrapy.Request(
                f"{self.school_base_url}{school_number}",
                callback=self.parse_school,
                cb_kwargs={"requested_school_number": school_number},
            )

    async def start(self):
        for request in self._iter_school_requests():
            yield request

    def start_requests(self):
        yield from self._iter_school_requests()

    def parse_school(self, response, requested_school_number=None):
        if response.status != 200:
            return

        container = response.css(".schoolSearchResult")
        sections = self._extract_sections(container)
        school_number = self._section_value(
            sections, "Verwaltungsangaben", "Schulnummer"
        )

        if not school_number:
            self.logger.warning(
                "Skipping Bayern KM page without school number: %s",
                response.url,
            )
            return

        latitude, longitude = self._extract_coords(response)
        school_year, teacher_count, student_count = self._extract_school_year_stats(
            sections
        )
        address, zip_code, city = self._extract_address(sections)

        yield {
            "source": "by-km",
            "requested_schulnummer": requested_school_number,
            "id": school_number,
            "schulnummer": school_number,
            "name": self._clean_text(response.css("h1::text").get()),
            "strasse": address,
            "postleitzahl": zip_code,
            "ort": city,
            "telefon": self._section_value(sections, "Kontakt", "Telefon"),
            "fax": self._section_value(sections, "Kontakt", "Fax"),
            "website": self._extract_website(response, sections),
            "schulart": self._section_value(sections, "Verwaltungsangaben", "Schulart"),
            "rechtlicher_status": self._section_value(
                sections, "Verwaltungsangaben", "Rechtlicher Status"
            ),
            "lat": latitude,
            "lon": longitude,
            "schuljahr": school_year,
            "lehrkraefte": teacher_count,
            "schueler": student_count,
            "betreuungsangebote": sections.get("Besondere Betreuungsangebote", []),
            "ausbildungsrichtungen": sections.get("Ausbildungsrichtungen", []),
        }

    @classmethod
    def _extract_sections(cls, container):
        sections = {}
        current_heading = None

        for element in container.xpath(".//*[self::h2 or self::p]"):
            tag_name = element.root.tag.lower()
            texts = []
            for text in element.xpath(".//text()").getall():
                cleaned_text = cls._clean_text(text)
                if cleaned_text:
                    texts.append(cleaned_text)

            if tag_name == "h2":
                current_heading = " ".join(texts)
                sections.setdefault(current_heading, [])
            elif current_heading:
                sections[current_heading].extend(texts)

        return sections

    @staticmethod
    def _clean_text(value):
        if value is None:
            return None
        return re.sub(r"\s+", " ", value).strip()

    @classmethod
    def _section_value(cls, sections, section, label):
        prefix = f"{label}:"
        values = sections.get(section, [])
        for index, value in enumerate(values):
            if value.startswith(prefix):
                text = cls._clean_text(value[len(prefix):])
                if text:
                    return text
                if index + 1 < len(values):
                    return values[index + 1]
        return None

    @classmethod
    def _extract_address(cls, sections):
        contact_lines = sections.get("Kontakt", [])
        address_lines = [
            line
            for line in contact_lines
            if ":" not in line
            and not line.startswith("www.")
            and "Standort anzeigen" not in line
        ]

        address = address_lines[0] if address_lines else None
        zip_code = None
        city = None
        if len(address_lines) > 1:
            match = re.match(r"(\d{5})\s+(.+)", address_lines[1])
            if match:
                zip_code, city = match.groups()

        return address, zip_code, city

    @staticmethod
    def _extract_coords(response):
        atlas_url = response.css('a[href*="geoportal.bayern.de/bayernatlas"]::attr(href)').get()
        if not atlas_url:
            return None, None

        query = parse_qs(urlparse(atlas_url).query)
        try:
            longitude = float(query["E"][0])
            latitude = float(query["N"][0])
            return latitude, longitude
        except (KeyError, IndexError, ValueError):
            return None, None

    @classmethod
    def _extract_school_year_stats(cls, sections):
        school_year = None
        stats = []
        for heading, values in sections.items():
            match = re.match(r"Eckdaten im Schuljahr (.+)", heading)
            if match:
                school_year = match.group(1)
                stats = values
                break

        teacher_count = cls._parse_int(
            cls._section_value({"stats": stats}, "stats", "Vollzeit- und überhälftig teilzeitbeschäftigte Lehrkräfte")
        )
        student_count = cls._parse_int(
            cls._section_value({"stats": stats}, "stats", "Schüler")
        )
        return school_year, teacher_count, student_count

    @staticmethod
    def _parse_int(value):
        if value is None:
            return None
        digits = re.sub(r"\D", "", value)
        return int(digits) if digits else None

    @classmethod
    def _extract_website(cls, response, sections):
        website = response.css("a.website::attr(href)").get()
        if website:
            return website
        return cls._section_value(sections, "Kontakt", "Web")

    @staticmethod
    def normalize(item: Item) -> School:
        return School(
            name=item.get("name") or item.get("schulname"),
            address=item.get("strasse"),
            city=item.get("ort"),
            school_type=item.get("schulart"),
            zip=item.get("postleitzahl"),
            id="BY-{}".format(item.get("id")),
            latitude=item.get("lat"),
            longitude=item.get("lon"),
            phone=item.get("telefon"),
            fax=item.get("fax"),
            website=item.get("website"),
            legal_status=item.get("rechtlicher_status"),
        )
