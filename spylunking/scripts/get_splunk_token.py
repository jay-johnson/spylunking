#!/usr/bin/env python

"""
Get a Splunk User Token
"""

import spylunking.get_token
from spylunking.log.setup_logging import simple_logger
from spylunking.consts import SPLUNK_API_ADDRESS


log = simple_logger()


def run_main():
    """run_main"""

    token = spylunking.get_token.get_token(
        url='https://{}'.format(
            SPLUNK_API_ADDRESS))

    log.info(token)
# end of run_main


if __name__ == '__main__':
    run_main()
