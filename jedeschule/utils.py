def cleanjoin(listlike, join_on=""):
    """ returns string of joined items in list,
        removing whitespace """
    return join_on.join([text.strip() for text in listlike])