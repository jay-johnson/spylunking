#!/usr/bin/env python

"""
Get a Splunk User Token
"""

import spylunking.get_token
from spylunking.log.setup_logging import simple_logger


log = simple_logger()


def run_main():
    """run_main"""

    token = spylunking.get_token.get_token(
        url="https://localhost:8089")

    log.info(token)
# end of run_main


if __name__ == '__main__':
    run_main()
