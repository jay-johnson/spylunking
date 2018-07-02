import os
import json
import uuid


def mock_get_token(
        user=None,
        password=None,
        url='https://testhost:8088',
        verify=False,
        ssl_options=None,
        version='7.0.3',
        debug=False):
    """mock_get_token

    Mock get Splunk token and store the requested
    data in the environment variable:
    ``TEST_GET_TOKEN``

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

    data = {
        'user': user,
        'password': password,
        'url': url,
        'verify': verify,
        'ssl_options': ssl_options,
        'version': version,
        'token': 'testtoken_{}'.format(
            str(uuid.uuid4())),
        'debug': debug
    }
    os.environ['TEST_GET_TOKEN'] = json.dumps(
        data)
    return data['token']
# end of mock_get_token


class MockRequest:
    """MockRequest"""

    def __init__(
            self):
        """__init__"""
        self.vals = None
        self.called_raise = False
    # end of __init

    def raise_for_status(
            self):
        """mock_raise"""
        self.called_raise = True
        return
    # end of raise_for_status

# end of MockRequest


def mock_post_request(
        self=None,
        session=None,
        url=None,
        data=None,
        headers=None,
        verify=None,
        timeout=None):
    """mock_post_request

    Mock ``requests.Session.post``

    :param self: class obj
    :param session: requests.Session
    :param data: data dictionary
    :param headers: auth headers
    :param verify: verifiy
    :param timeout: timeout
    """
    req = MockRequest()
    req.vals = {
        'url': url,
        'data': data,
        'headers': headers,
        'verify': verify,
        'timeout': timeout
    }
    os.environ['TEST_POST'] = json.dumps(
        req.vals)
    return req
# end of mock_post_request


def mock_mp_post_request(
        self=None,
        session=None,
        url=None,
        data=None,
        headers=None,
        verify=None,
        timeout=None):
    """mock_mp_post_request

    Mock ``requests.Session.post``

    :param self: class obj
    :param session: requests.Session
    :param data: data dictionary
    :param headers: auth headers
    :param verify: verifiy
    :param timeout: timeout
    """
    req = MockRequest()
    req.vals = {
        'url': url,
        'data': data,
        'headers': headers,
        'verify': verify,
        'timeout': timeout
    }
    os.environ['TEST_MP_POST'] = json.dumps(
        req.vals)
    return req
# end of mock_mp_post_request


def mock_test_time():
    """mock_test_time"""
    return None
# end of mock_test_time
