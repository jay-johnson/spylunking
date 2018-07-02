import os
import logging
import unittest
import mock
import json
import uuid
from spylunking.mp_splunk_publisher import MPSplunkPublisher
from tests.mock_utils import MockRequest


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


# These are intentionally different than the kwarg defaults
SPLUNK_HOST = os.getenv(
    'SPLUNK_HOST',
    'splunkenterprise')
SPLUNK_PORT = int(os.getenv(
    'SPLUNK_PORT',
    '4321'))
SPLUNK_COLLECTOR_URL = (
    "https://{}:{}/services/collector").format(
        SPLUNK_HOST,
        SPLUNK_PORT)
SPLUNK_TOKEN = 'ABCDEFGH-IJKL-MNOP-QRST-UVWXYZ123456'
SPLUNK_INDEX = 'test_index'
SPLUNK_HOSTNAME = 'test_host'
SPLUNK_SOURCE = 'test_source'
SPLUNK_SOURCETYPE = 'test_sourcetype'
SPLUNK_VERIFY = False
SPLUNK_TIMEOUT = 27
SPLUNK_SLEEP_INTERVAL = 0.0
SPLUNK_QUEUE_SIZE = 1111
SPLUNK_DEBUG = False
SPLUNK_RETRY_COUNT = 1
SPLUNK_RETRY_BACKOFF = 0.1


class TestMPSplunkPublisher(unittest.TestCase):
    """TestMPSplunkPublisher"""

    org_value = None

    def setUp(self):
        """setUp"""
        self.splunk = MPSplunkPublisher(
            host=SPLUNK_HOST,
            port=SPLUNK_PORT,
            token=SPLUNK_TOKEN,
            index=SPLUNK_INDEX,
            hostname=SPLUNK_HOSTNAME,
            source=SPLUNK_SOURCE,
            sourcetype=SPLUNK_SOURCETYPE,
            verify=SPLUNK_VERIFY,
            timeout=SPLUNK_TIMEOUT,
            sleep_interval=SPLUNK_SLEEP_INTERVAL,
            queue_size=SPLUNK_QUEUE_SIZE,
            debug=SPLUNK_DEBUG,
            retry_count=SPLUNK_RETRY_COUNT,
            retry_backoff=SPLUNK_RETRY_BACKOFF
        )
        self.org_value = os.getenv(
            'TEST_MP_POST',
            None)
        os.environ.pop(
            'TEST_MP_POST', None)
    # end of setUp

    def tearDown(self):
        """tearDown"""
        self.splunk = None
        if self.org_value:
            os.environ['TEST_MP_POST'] = self.org_value
    # end of tearDown

    def test_init(self):
        """test_init"""
        self.assertIsNotNone(self.splunk)
        self.assertIsInstance(self.splunk, MPSplunkPublisher)
        self.assertIsInstance(self.splunk, logging.Handler)
        self.assertEqual(self.splunk.host, SPLUNK_HOST)
        self.assertEqual(self.splunk.port, SPLUNK_PORT)
        self.assertEqual(self.splunk.token, SPLUNK_TOKEN)
        self.assertEqual(self.splunk.index, SPLUNK_INDEX)
        self.assertEqual(self.splunk.hostname, SPLUNK_HOSTNAME)
        self.assertEqual(self.splunk.source, SPLUNK_SOURCE)
        self.assertEqual(self.splunk.sourcetype, SPLUNK_SOURCETYPE)
        self.assertEqual(self.splunk.verify, SPLUNK_VERIFY)
        self.assertEqual(self.splunk.timeout, SPLUNK_TIMEOUT)
        self.assertEqual(self.splunk.sleep_interval, SPLUNK_SLEEP_INTERVAL)
        self.assertEqual(self.splunk.retry_count, SPLUNK_RETRY_COUNT)
        self.assertEqual(self.splunk.retry_backoff, SPLUNK_RETRY_BACKOFF)
        self.assertIsNotNone(self.splunk.debug)

        self.assertFalse(logging.getLogger('requests').propagate)
    # end of test_init

    @mock.patch(
        ('spylunking.send_to_splunk.send_to_splunk'),
        new=mock_mp_post_request)
    def test_publish_to_splunk(
            self):
        """test_publish_to_splunk

        :param mock_request: mock request object
        """
        # Silence root logger
        log = logging.getLogger('')
        for h in log.handlers:
            log.removeHandler(h)

        log = logging.getLogger('test')
        log.addHandler(self.splunk)

        log_msg = ('testing message={}').format(
            str(uuid.uuid4()))
        log.warning(log_msg)

        expected_output = {
            'event': log_msg,
            'host': SPLUNK_HOSTNAME,
            'index': SPLUNK_INDEX,
            'source': SPLUNK_SOURCE,
            'sourcetype': SPLUNK_SOURCETYPE
        }
        found_env_vals = os.getenv(
            'TEST_MP_POST',
            None)
        requested_vals = json.loads(
            found_env_vals)
        self.assertIsNotNone(
            requested_vals)
        print(requested_vals)
        found_url = requested_vals['url']
        self.assertEqual(
            found_url,
            SPLUNK_COLLECTOR_URL)
        found_data = json.loads(
            requested_vals['data'])
        self.assertEqual(
            expected_output['event'],
            found_data['event'])
        self.assertEqual(
            expected_output['host'],
            found_data['host'])
        self.assertEqual(
            expected_output['index'],
            found_data['index'])
        self.assertEqual(
            expected_output['source'],
            found_data['source'])
        self.assertEqual(
            expected_output['sourcetype'],
            found_data['sourcetype'])
    # end of publish_to_splunk

# end of TestMPSplunkPublisher
