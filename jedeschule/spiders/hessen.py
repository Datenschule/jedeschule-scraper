import scrapy
import re
from urllib.parse import urlparse, parse_qs

from scrapy import Item

from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


class HessenSpider(SchoolSpider):
    """Spider for scraping school data from Hessen's school database

    Extracts school information by:
    1. Submitting search forms for each school type
    2. Parsing result lists for school detail page links
    3. Extracting contact info and coordinates from detail pages
    """
    name = "hessen"

    start_urls = ["https://schul-db.bildung.hessen.de/schul_db.html"]

    def parse(self, response):
        # Extract all available school types from the dropdown
        school_types = response.xpath(
            '//select[@id="id_school_type"]/option/@value'
        ).extract()

        # Build search form with empty filters to get all schools per type
        form = {
            "school_name": "",
            "school_town": "",
            "school_zip": "",
            "school_number": "",
            "csrfmiddlewaretoken": response.xpath(
                '//input[@name="csrfmiddlewaretoken"]/@value'
            ).extract_first(),
            "submit_hesse": "Hessische+Schule+suchen+...",
        }

        # Submit one search per school type to retrieve all schools
        for school_type in school_types:
            form["school_type"] = school_type

            yield scrapy.FormRequest(
                self.start_urls[0], formdata=form, callback=self.parse_list
            )

    def parse_list(self, response):
        # Extract links to individual school detail pages
        schools = response.xpath("//tbody/tr/td/a/@href").extract()

        for school in schools:
            yield scrapy.Request(school, callback=self.parse_details)

    def _extract_coords_from_osm_url(self, url):
        """Extract coordinates from OpenStreetMap URL query parameters"""
        if not url or "openstreetmap.org" not in url:
            return None, None

        qs = parse_qs(urlparse(url).query)

        # Try marker parameter first (most precise)
        if "marker" in qs and qs["marker"]:
            try:
                lat_str, lon_str = qs["marker"][0].split(",", 1)
                return float(lat_str), float(lon_str)
            except Exception:
                pass

        # Try mlat/mlon parameters
        if "mlat" in qs and "mlon" in qs:
            try:
                return float(qs["mlat"][0]), float(qs["mlon"][0])
            except Exception:
                pass

        # Fallback: bbox center
        if "bbox" in qs and qs["bbox"]:
            try:
                west, south, east, north = map(float, qs["bbox"][0].split(",", 3))
                return (south + north) / 2.0, (west + east) / 2.0
            except Exception:
                pass

        return None, None

    def parse_details(self, response):
        # Extract basic school info from <pre> text blocks
        contact_text_nodes = response.xpath("//pre/text()").extract()
        adress = contact_text_nodes[0].split("\n")

        # Parse ZIP and city from line 4 (format: "12345 City Name")
        matches = re.search(r"(\d+) (.+)", adress[3])

        # Build school dict with required fields
        school = {
            "name": adress[1],
            "straße": adress[2],
            "ort": matches.group(2),
            "plz": matches.group(1),
        }

        # Extract optional fax number if present
        for text_node in contact_text_nodes:
            if "Fax: " in text_node:
                school["fax"] = text_node.split("\n")[1].replace("Fax: ", "").strip()

        # Extract phone and website from links
        contact_links = response.xpath("//pre/a/@href").extract()
        for link in contact_links:
            if "tel:" in link:
                school["telefon"] = link.replace("tel:", "")

            if "http" in link:
                school["homepage"] = link

        # Extract school type from main content area
        school["schultyp"] = (
            response.xpath('//main//div[@class="col-md-9 col-lg-9"]/text()')
            .extract_first()
            .replace("\n", "")
            .strip()
        )
        # Extract school ID from URL query parameter
        school["id"] = response.request.url.split("=")[-1]

        # Extract coordinates from OpenStreetMap iframe or link
        latitude, longitude = None, None

        # Try iframe first
        iframe_src = response.xpath('//iframe[contains(@src, "openstreetmap.org")]/@src').get()
        if iframe_src:
            latitude, longitude = self._extract_coords_from_osm_url(iframe_src)

        # Fallback: try "Größere Karte" link
        if latitude is None:
            osm_link = response.xpath('//a[contains(@href, "openstreetmap.org")]/@href').get()
            if osm_link:
                latitude, longitude = self._extract_coords_from_osm_url(osm_link)

        # Filter out placeholder coordinates (-1.0, -1.0) used by Hessen DB for missing data
        if latitude == -1.0 and longitude == -1.0:
            latitude = None
            longitude = None

        school["latitude"] = latitude
        school["longitude"] = longitude

        yield school

    @staticmethod
    def normalize(item: Item) -> School:
        """Transform raw scraped data into standardized School model"""
        return School(
            name=item.get("name") or None,
            phone=item.get("telefon") or None,
            fax=item.get("fax") or None,
            website=item.get("homepage") or None,
            address=item.get("straße") or None,
            city=item.get("ort") or None,
            zip=item.get("plz") or None,
            school_type=item.get("schultyp") or None,
            id="HE-{}".format(item.get("id")),  # Prefix with state code
            latitude=item.get("latitude") or None,
            longitude=item.get("longitude") or None,
        )
