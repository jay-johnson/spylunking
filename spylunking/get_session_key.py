"""
Get a Splunk User Session Key - for running searches
"""

import requests
import urllib3
from xml.dom.minidom import parseString
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_session_key(
        user,
        password,
        url='https://localhost:8089',
        verify=False,
        ssl_options=None):
    """get_session_key

    This will get a user session key and throw for any errors

    :param user: username
    :param password: password
    :param url: splunk auth url
    :param verify: verify cert
    :param ssl_options: ssl options dictionary

    """
    servercontent = requests.post(
        '{}/services/auth/login'.format(
            url),
        headers={},
        verify=False,
        data={
            'username': user,
            'password': password
        })
    get_session_key = parseString(
        servercontent.text).getElementsByTagName(
            'sessionKey')[0].childNodes[0].nodeValue
    return get_session_key
# end of get_session_key
