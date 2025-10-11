"""
Utility functions for jedeschule scrapers
"""
import re


def cleanjoin(listlike, join_on=""):
    """returns string of joined items in list,
    removing whitespace"""
    return join_on.join([text.strip() for text in listlike]).strip()


def get_first_or_none(listlike):
    return listlike[0] if listlike else None


# See https://www.python.org/dev/peps/pep-0318/#examples
def singleton(cls):
    instances = {}

    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]

    return getinstance


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
