"""
Testing Logger Methods
"""
import os
import mock
from spylunking.log.setup_logging import build_colorized_logger
from tests.base_test import BaseTestCase
from tests.mock_utils import mock_get_token
from tests.mock_utils import mock_post_request


class TestLogger(BaseTestCase):
    """TestLogger"""

    org_value = None

    def setUp(
            self):
        """setUp"""
        self.org_value = os.getenv(
            'TEST_POST',
            None)
    # end of setUp

    def tearDown(self):
        """tearDown"""
        if self.org_value:
            os.environ['TEST_GET_TOKEN'] = self.org_value
    # end of tearDown

    @mock.patch(
        ('spylunking.send_to_splunk.send_to_splunk'),
        new=mock_post_request)
    @mock.patch(
        ('spylunking.get_token.get_token'),
        new=mock_get_token)
    def test_build_colorized_logger_with_splunk_user_and_password(
            self):
        """test_build_colorized_logger"""
        log = build_colorized_logger(
            name='build_colorized_logger_with_splunk',
            splunk_user='trex',
            splunk_password='123321',
            splunk_sleep_interval=0)
        self.assertIsNotNone(log)
    # end of test_build_colorized_logger_with_splunk_user_and_password

    @mock.patch(
        ('spylunking.send_to_splunk.send_to_splunk'),
        new=mock_post_request)
    @mock.patch(
        ('spylunking.get_token.get_token'),
        new=mock_get_token)
    def test_build_colorized_logger_without_splunk(
            self):
        """test_build_colorized_logger"""
        log = build_colorized_logger(
            name='build_colorized_logger_without_splunk',
            splunk_sleep_interval=0)
        self.assertIsNotNone(log)
    # end of test_build_colorized_logger_without_splunk

# end of TestLogger
