import os
import logging
import unittest
import mock
import json
import uuid
from tests.mock_utils import MockRequest
from spylunking.splunk_publisher import SplunkPublisher
from spylunking.consts import SPLUNK_HOST
from spylunking.consts import SPLUNK_PORT
from spylunking.consts import SPLUNK_HOSTNAME
from spylunking.consts import SPLUNK_TOKEN
from spylunking.consts import SPLUNK_INDEX
from spylunking.consts import SPLUNK_SOURCE
from spylunking.consts import SPLUNK_SOURCETYPE
from spylunking.consts import SPLUNK_VERIFY
from spylunking.consts import SPLUNK_TIMEOUT
from spylunking.consts import SPLUNK_RETRY_COUNT
from spylunking.consts import SPLUNK_RETRY_BACKOFF
from spylunking.consts import SPLUNK_QUEUE_SIZE
from spylunking.consts import SPLUNK_DEBUG
from spylunking.consts import SPLUNK_COLLECTOR_URL


def mock_post_request(
        self=None,
        session=None,
        url=None,
        data=None,
        headers=None,
        verify=None,
        timeout=None):
    """mock_post_request

    Mock spylunking.send_to_splunk which is using:
    ``requests.Session.post``

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


class TestSplunkPublisher(unittest.TestCase):
    """TestSplunkPublisher"""

    org_value = None
    disable_shutdown_publish_value = None

    def setUp(self):
        """setUp"""
        self.splunk = SplunkPublisher(
            host=SPLUNK_HOST,
            port=SPLUNK_PORT,
            token=SPLUNK_TOKEN,
            index=SPLUNK_INDEX,
            hostname=SPLUNK_HOSTNAME,
            source=SPLUNK_SOURCE,
            sourcetype=SPLUNK_SOURCETYPE,
            verify=SPLUNK_VERIFY,
            timeout=SPLUNK_TIMEOUT,
            sleep_interval=0,
            queue_size=SPLUNK_QUEUE_SIZE,
            debug=SPLUNK_DEBUG,
            retry_count=SPLUNK_RETRY_COUNT,
            retry_backoff=SPLUNK_RETRY_BACKOFF
        )
        self.org_value = os.getenv(
            'TEST_POST',
            None)
        self.disable_shutdown_publish_value = os.getenv(
            'SPLUNK_DISABLE_SHUTDOWN_PUBLISH',
            None)
        os.environ.pop(
            'TEST_POST', None)
        os.environ.pop(
            'SPLUNK_DISABLE_SHUTDOWN_PUBLISH', None)
    # end of setUp

    def tearDown(self):
        """tearDown"""
        self.splunk = None
        if self.org_value:
            os.environ['TEST_POST'] = self.org_value
        if self.disable_shutdown_publish_value:
            os.environ['SPLUNK_DISABLE_SHUTDOWN_PUBLISH'] = \
                self.disable_shutdown_publish_value
    # end of tearDown

    def test_init(self):
        """test_init"""
        self.assertIsNotNone(self.splunk)
        self.assertIsInstance(self.splunk, SplunkPublisher)
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
        self.assertEqual(self.splunk.sleep_interval, 0)
        self.assertEqual(self.splunk.retry_count, SPLUNK_RETRY_COUNT)
        self.assertEqual(self.splunk.retry_backoff, SPLUNK_RETRY_BACKOFF)
        self.assertIsNotNone(self.splunk.debug)

        self.assertFalse(logging.getLogger('requests').propagate)
    # end of test_init

    @mock.patch(
        ('spylunking.send_to_splunk.send_to_splunk'),
        new=mock_post_request)
    def test_publish_to_splunk(
            self):
        """test_publish_to_splunk
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
            'TEST_POST',
            None)
        requested_vals = json.loads(
            found_env_vals)
        self.assertIsNotNone(
            requested_vals)
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
    # end of test_publish_to_splunk

# end of TestSplunkPublisher
