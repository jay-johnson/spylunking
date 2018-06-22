import os
import json


def ev(k, v):
    """ev

    :param k: environment variable key
    :param v: environment variable value
    """
    return os.getenv(k, v).strip().lstrip()
# end of ev


def ppj(json_data):
    """ppj

    :param json_data: dictionary to print
    """
    return str(json.dumps(
                json_data,
                sort_keys=True,
                indent=4,
                separators=(',', ': ')))
# end of ppj
