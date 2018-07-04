import os
import logging
import unittest
import mock
import json
import uuid
from spylunking.tcp_splunk_publisher import TCPSplunkPublisher
from spylunking.log.setup_logging import SplunkFormatter
from spylunking.consts import SPLUNK_TCP_ADDRESS
from spylunking.consts import SPLUNK_TOKEN
from spylunking.consts import SPLUNK_INDEX
from spylunking.consts import SPLUNK_SOURCE
from spylunking.consts import SPLUNK_SOURCETYPE
from spylunking.consts import SPLUNK_HOSTNAME
from spylunking.consts import SPLUNK_DEBUG
from spylunking.consts import IS_PY2


def mock_socket_send(
        self=None,
        s=None):
    """mock_socket_send

    Mock spylunking.send_to_splunk which is using:
    ``logging.handlers.SocketHandler.send``

    :param self: class obj
    :param s: log message
    """
    if IS_PY2:
        os.environ['TEST_TCP_MSG'] = s
    else:
        os.environ['TEST_TCP_MSG'] = s.decode()
    return
# end of mock_post_request


class TestTCPSplunkPublisher(unittest.TestCase):
    """TestSplunkPublisher"""

    org_value = None
    disable_shutdown_publish_value = None

    def setUp(self):
        """setUp"""
        self.splunk = TCPSplunkPublisher(
            address=SPLUNK_TCP_ADDRESS,
            index=SPLUNK_INDEX,
            hostname=SPLUNK_HOSTNAME,
            source=SPLUNK_SOURCE,
            sourcetype=SPLUNK_SOURCETYPE,
            debug=SPLUNK_DEBUG
        )
        self.splunk.formatter = SplunkFormatter()
        self.org_value = os.getenv(
            'TEST_TCP_MSG',
            None)
        os.environ.pop(
            'TEST_TCP_MSG', None)
    # end of setUp

    def tearDown(self):
        """tearDown"""
        self.splunk = None
        if self.org_value:
            os.environ['TEST_TCP_MSG'] = self.org_value
    # end of tearDown

    def test_init(self):
        """test_init"""
        self.assertIsNotNone(self.splunk)
        self.assertIsInstance(self.splunk, TCPSplunkPublisher)
        self.assertIsInstance(self.splunk, logging.Handler)
        self.assertEqual(self.splunk.tcp_address, SPLUNK_TCP_ADDRESS)
        self.assertEqual(self.splunk.token, SPLUNK_TOKEN)
        self.assertEqual(self.splunk.index, SPLUNK_INDEX)
        self.assertEqual(self.splunk.hostname, SPLUNK_HOSTNAME)
        self.assertEqual(self.splunk.source, SPLUNK_SOURCE)
        self.assertEqual(self.splunk.sourcetype, SPLUNK_SOURCETYPE)
        self.assertIsNotNone(self.splunk.debug)
    # end of test_init

    @mock.patch(
        ('logging.handlers.SocketHandler.send'),
        new=mock_socket_send)
    def test_tcp_publish_to_splunk(
            self):
        """test_tcp_publish_to_splunk
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
            'message': log_msg,
            'hostname': SPLUNK_HOSTNAME,
            'index': SPLUNK_INDEX,
            'source': SPLUNK_SOURCE,
            'sourcetype': SPLUNK_SOURCETYPE
        }
        found_env_vals = os.getenv(
            'TEST_TCP_MSG',
            None)
        requested_vals = json.loads(
            found_env_vals)
        self.assertIsNotNone(
            requested_vals)
        found_data = requested_vals
        self.assertEqual(
            expected_output['message'],
            found_data['message'])
        self.assertEqual(
            expected_output['hostname'],
            found_data['hostname'])
        self.assertEqual(
            expected_output['index'],
            found_data['index'])
        self.assertEqual(
            expected_output['sourcetype'],
            found_data['sourcetype'])
    # end test_tcp_publish_to_splunk

# end of TestSplunkPublisher
