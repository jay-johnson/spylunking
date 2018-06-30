"""
Testing Logger Methods
"""
from spylunking.log.setup_logging import build_colorized_logger
from tests.base_test import BaseTestCase


class TestLogger(BaseTestCase):
    """TestLogger"""

    def test_build_colorized_logger_with_splunk_user_and_password(
            self):
        """test_build_colorized_logger"""
        log = build_colorized_logger(
            name='build_colorized_logger_with_splunk',
            splunk_user='trex',
            splunk_password='123321')
        self.assertIsNotNone(log)
    # end of test_build_colorized_logger_with_splunk_user_and_password

    def test_build_colorized_logger_without_splunk(
            self):
        """test_build_colorized_logger"""
        log = build_colorized_logger(
            name='build_colorized_logger_without_splunk')
        self.assertIsNotNone(log)
    # end of test_build_colorized_logger_without_splunk

# end of TestLogger
