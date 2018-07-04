"""
Constants file

"""

import os
import sys


SUCCESS = 0
FAILED = 1
ERR = 2
EX = 3
NOT_RUN = 4
INVALID = 5
NOT_DONE = 6

# version of python
IS_PY2 = sys.version[0] == '2'

LOG_HANDLER_NAME = os.getenv(
    'LOG_HANDLER_NAME',
    'console').strip()
SPLUNK_USER = os.getenv(
    'SPLUNK_USER',
    None)
if SPLUNK_USER:
    SPLUNK_USER = SPLUNK_USER.strip()
SPLUNK_PASSWORD = os.getenv(
    'SPLUNK_PASSWORD',
    None)
if SPLUNK_PASSWORD:
    SPLUNK_PASSWORD = SPLUNK_PASSWORD.strip()
SPLUNK_HOST = os.getenv(
    'SPLUNK_HOST',
    'splunkenterprise').strip()
SPLUNK_PORT = int(os.getenv(
    'SPLUNK_PORT',
    '8088').strip())
SPLUNK_API_PORT = int(os.getenv(
    'SPLUNK_API_PORT',
    '8089').strip())
SPLUNK_TCP_PORT = int(os.getenv(
    'SPLUNK_TCP_PORT',
    '1514').strip())
SPLUNK_ADDRESS = os.getenv(
    'SPLUNK_ADDRESS',
    '{}:{}'.format(
        SPLUNK_HOST,
        SPLUNK_PORT)).strip()
SPLUNK_API_ADDRESS = os.getenv(
    'SPLUNK_API_ADDRESS',
    '{}:{}'.format(
        SPLUNK_HOST,
        SPLUNK_API_PORT)).strip()
SPLUNK_TCP_ADDRESS = os.getenv(
    'SPLUNK_TCP_ADDRESS',
    '{}:{}'.format(
        SPLUNK_HOST,
        SPLUNK_TCP_PORT)).strip()
SPLUNK_HOSTNAME = os.getenv(
    'SPLUNK_HOSTNAME',
    '')
SPLUNK_TOKEN = os.getenv(
    'SPLUNK_TOKEN',
    None)
if SPLUNK_TOKEN:
    SPLUNK_TOKEN = SPLUNK_TOKEN.strip()
SPLUNK_INDEX = os.getenv(
    'SPLUNK_INDEX',
    None)
if SPLUNK_INDEX:
    SPLUNK_INDEX = SPLUNK_INDEX.strip()
SPLUNK_SOURCE = os.getenv(
    'SPLUNK_SOURCE',
    '').strip()
SPLUNK_SOURCETYPE = os.getenv(
    'SPLUNK_SOURCETYPE',
    'json').strip()
SPLUNK_VERIFY = bool(os.getenv(
    'SPLUNK_VERIFY',
    '0').strip() == '1')
SPLUNK_VERBOSE = bool(os.getenv(
    'SPLUNK_VERBOSE',
    '0').strip() == '1')
SPLUNK_TIMEOUT = float(os.getenv(
    'SPLUNK_TIMEOUT',
    '10.0').strip())
SPLUNK_SLEEP_INTERVAL = float(os.getenv(
    'SPLUNK_SLEEP_INTERVAL',
    '1.0').strip())
SPLUNK_RETRY_COUNT = int(os.getenv(
    'SPLUNK_RETRY_COUNT',
    '10').strip())
SPLUNK_RETRY_BACKOFF = float(os.getenv(
    'SPLUNK_RETRY_BACKOFF',
    '2.0').strip())
SPLUNK_QUEUE_SIZE = int(os.getenv(
    'SPLUNK_QUEUE_SIZE',
    '0').strip())  # infinite queue size = 0
SPLUNK_DEBUG = bool(os.getenv(
    'SPLUNK_DEBUG',
    '0').strip() == '1')
SPLUNK_COLLECTOR_URL = (
    'https://{}:{}/services/collector').format(
        SPLUNK_HOST,
        SPLUNK_PORT)
SPLUNK_HANDLER_NAME = os.getenv(
    'SPLUNK_HANDLER_NAME',
    'splunk').strip()
SPLUNK_LOG_NAME = os.getenv(
    'LOG_NAME',
    '').strip()
SPLUNK_DEPLOY_CONFIG = os.getenv(
    'DEPLOY_CONFIG',
    '').strip()
SPLUNK_ENV_NAME = os.getenv(
    'ENV_NAME',
    '').strip()


def get_status(
        status):
    """get_status

    Return the string label for an integer status code
    which should be one of the ones above.

    :param status: integer status code

    """
    if status == SUCCESS:
        return 'SUCCESS'
    elif status == FAILED:
        return 'FAILED'
    elif status == ERR:
        return 'ERR'
    elif status == EX:
        return 'EX'
    elif status == NOT_RUN:
        return 'NOT_RUN'
    elif status == INVALID:
        return 'INVALID'
    elif status == NOT_DONE:
        return 'NOT_DONE'
    else:
        return 'unsupported status={}'.format(
            status)
# end of get_status
