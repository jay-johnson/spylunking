import os
import json
import datetime


def ev(k, v):
    """ev

    :param k: environment variable key
    :param v: environment variable value
    """
    return os.getenv(k, v).strip().lstrip()
# end of ev


def rnow(f="%Y-%m-%d %H:%M:%S"):
    """rnow

    :param f: format for the string
    """
    return datetime.datetime.now().strftime(f)
# end of rnow


def convert_to_date(
        value=None,
        format="%Y-%m-%d %H:%M:%S"):
    """convert_to_date

    param: value - datetime object
    param: format - string format
    """

    if value:
        return value.strftime(format)

    return ""
# end of convert_to_date


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
