def cleanjoin(listlike, join_on=""):
    """ returns string of joined items in list,
        removing whitespace """
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
