"""
Get a Splunk User Token
"""

import os
import requests
import urllib3
from xml.dom.minidom import parseString
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_token(
        user=None,
        password=None,
        url='https://localhost:8089',
        verify=False,
        ssl_options=None,
        version="7.0.3",
        debug=False):
    """get_token

    This will get a user token and throw for any errors

    :param user: username - defaults to env var:
                 SPLUNK_ADMIN_USER
    :param password: password - defaults to env var:
                     SPLUNK_ADMIN_PASSWORD
    :param url: splunk auth url
    :param verify: verify cert
    :param ssl_options: ssl options dictionary
    :param version: splunk version string
    :param debug: debug xml response from splunk (for versioning)

    """
    use_user = os.getenv(
        "SPLUNK_ADMIN_USER",
        user)
    use_password = os.getenv(
        "SPLUNK_ADMIN_PASSWORD",
        password)
    if not use_user:
        use_user = "admin"
    if not use_password:
        use_password = "changeme"

    full_url = (
        '{}/servicesNS/admin/splunk_httpinput/data/inputs/http').format(
            url)
    if debug:
        print(full_url)
    response = requests.get(
        url=full_url,
        verify=False,
        auth=(use_user, use_password),
        data={
            'username': use_user,
            'password': use_password
        })
    if debug:
        print(response.text)

    # this works on 7.0.3
    if version == "7.0.3":
        all_keys = parseString(
            response.text).getElementsByTagName(
                'entry')[0].getElementsByTagName(
                    'content')[0].childNodes[1].getElementsByTagName(
                        's:key')
        for k in all_keys:
            name_value = k.attributes.get(
                "name",
                None)
            if name_value:
                if name_value.value == "token":
                    if debug:
                        print(name_value.value)
                        print(k.childNodes[0].nodeValue)
                    return k.childNodes[0].nodeValue
                    break
    else:
        print((
            "Unsupported version={}").format(
                version))
    # end of version handling on xml responses

    return None
# end of get_token
