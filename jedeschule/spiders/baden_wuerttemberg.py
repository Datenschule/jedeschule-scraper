import re
import scrapy
from scrapy import Item

from jedeschule.fallback_school_id import baden_wuerttemberg_school_id
from jedeschule.items import School
from jedeschule.spiders.school_spider import SchoolSpider


# Pattern to extract DISCH (8-digit school ID) from Baden-Württemberg email addresses
DISCH_RE = re.compile(r'@(\d{8})\.schule\.bwl\.de', re.IGNORECASE)


def extract_disch(email: str | None) -> str | None:
    """
    Extract 8-digit DISCH (Dienststellenschlüssel) from BW school email address.

    Args:
        email: Email address, typically in format poststelle@{DISCH}.schule.bwl.de

    Returns:
        8-digit DISCH string if found, None otherwise

    Example:
        >>> extract_disch("poststelle@04144952.schule.bwl.de")
        '04144952'
        >>> extract_disch("info@school.de")
        None
    """
    if not email:
        return None

    match = DISCH_RE.search(email.strip())
    return match.group(1) if match else None


class BadenWuerttembergSpider(SchoolSpider):
    name = "baden-wuerttemberg"

    start_urls = [
        "https://gis.kultus-bw.de/geoserver/us-govserv/ows?"
        "service=WFS&request=GetFeature&"
        "typeNames=us-govserv%3AGovernmentalService&"
        "outputFormat=application%2Fjson"
    ]

    def parse(self, response):
        """Parse WFS GeoJSON response"""
        data = response.json()
        features = data.get("features") or []

        # GeoServer includes WFS 2.0 counters; use them to detect truncation or paging gaps.
        def _as_int(v):
            if v is None:
                return None
            try:
                return int(v)
            except (TypeError, ValueError):
                return None

        nm = _as_int(data.get("numberMatched"))
        nr = _as_int(data.get("numberReturned"))
        tf = _as_int(data.get("totalFeatures"))
        if nm is not None and nm != len(features):
            self.logger.error(
                "BW WFS: numberMatched (%s) != len(features) (%s) — response may be truncated",
                nm,
                len(features),
            )
        if (
            nm is not None
            and nr is not None
            and nr != nm
            and nr != 0
        ):
            self.logger.error(
                "BW WFS: numberReturned (%s) != numberMatched (%s) — implement paging (STARTINDEX) or raise",
                nr,
                nm,
            )
        if tf is not None and nm is not None and tf != nm:
            self.logger.warning(
                "BW WFS: totalFeatures (%s) != numberMatched (%s)",
                tf,
                nm,
            )

        for feature in features:
            uuid = feature.get("id")
            props = feature["properties"]

            # Extract coordinates
            service_loc = props.get("serviceLocation", {})
            geom = service_loc.get("serviceLocationByGeometry", {})
            coords = geom.get("coordinates")

            # Note: BW WFS returns [latitude, longitude] (non-standard!)
            lat = coords[0] if coords and len(coords) >= 2 else None
            lon = coords[1] if coords and len(coords) >= 2 else None

            # Extract contact and address info
            contact = props.get("pointOfContact", {}).get("Contact", {})
            addr_repr = contact.get("address", {}).get("AddressRepresentation", {})

            # School name
            locator_name = addr_repr.get("locatorName", {})
            name_spelling = locator_name.get("spelling", {})
            name = (
                name_spelling.get("text", "") if isinstance(name_spelling, dict) else ""
            )

            # Street
            thoroughfare = addr_repr.get("thoroughfare", {})
            if isinstance(thoroughfare, dict):
                street_obj = thoroughfare.get("GeographicalName", {}).get(
                    "spelling", {}
                )
                street = (
                    street_obj.get("text", "").strip()
                    if isinstance(street_obj, dict)
                    else ""
                )
            else:
                street = ""

            # House number
            locator = addr_repr.get("locatorDesignator", "").strip()

            # Full address
            address = f"{street} {locator}".strip() if street else None

            # ZIP code
            zip_code = addr_repr.get("postCode", "").strip()

            # City
            post_name = addr_repr.get("postName", {})
            city_obj = post_name.get("GeographicalName", {})
            city_spelling = city_obj.get("spelling", {})
            city = (
                city_spelling.get("text", "").strip()
                if isinstance(city_spelling, dict)
                else ""
            )

            # Contact info
            email = contact.get("electronicMailAddress", "")
            phone = contact.get("telephoneVoice", "")
            fax = contact.get("telephoneFacsimile", "")
            website = contact.get("website", "")

            # Extract DISCH from email (if available)
            disch = extract_disch(email)

            # Service type (school type)
            service_type = props.get("serviceType", {}).get("@href", "")

            item = {
                "uuid": uuid,
                "disch": disch,  # Store in raw for reference
                "name": name,
                "address": address,
                "zip": zip_code,
                "city": city,
                "email": email,
                "phone": phone,
                "fax": fax,
                "website": website if website else None,
                "school_type": service_type,
                "lat": lat,
                "lon": lon,
            }

            yield item

    @staticmethod
    def normalize(item: Item) -> School:
        disch = item.get("disch")
        uuid = item.get("uuid")
        school_id = baden_wuerttemberg_school_id(
            disch,
            item.get("lat"),
            item.get("lon"),
            item.get("name"),
            item.get("school_type"),
            str(uuid) if uuid is not None else None,
        )

        return School(
            id=school_id,
            name=item.get("name"),
            address=item.get("address"),
            zip=item.get("zip"),
            city=item.get("city"),
            email=item.get("email"),
            phone=item.get("phone"),
            fax=item.get("fax"),
            website=item.get("website"),
            school_type=item.get("school_type"),
            latitude=item.get("lat"),
            longitude=item.get("lon"),
        )
