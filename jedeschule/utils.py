def cleanjoin(listlike, join_on=""):
    """ returns string of joined items in list,
        removing whitespace """
    return join_on.join([text.strip() for text in listlike]).strip()


def get_first_or_none(listlike):
    return listlike[0] if listlike else None