"""
Utility - pretty print a dictionary
"""

import json


def ppj(json_data):
    """ppj

    Pretty print a json dictionary and return it as a string

    :param json_data: dictionary to print
    """
    return str(
        json.dumps(
            json_data,
            sort_keys=True,
            indent=4,
            separators=(',', ': ')))
# end of ppj
