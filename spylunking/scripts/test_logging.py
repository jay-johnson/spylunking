#!/usr/bin/env python

"""
Publish functional testing logs to splunk using the logger
"""

import uuid
import spylunking.wait_for_exit as wait_for_exit
from spylunking.log.setup_logging import build_colorized_logger


def run_main():
    """run_main"""

    log = build_colorized_logger(
        name='helloworld',
        splunk_user='trex',
        splunk_password='123321',
        # handler_name='simple',
        # handler_name='not-real',
        # splunk_address='localhost:8088',
        # splunk_token='55df5127-cb0e-4182-932e-c71c454699b8',
        splunk_debug=False)

    max_recs = 1
    msg_sent = 0
    not_done = True
    while not_done:

        log.debug('testing DEBUG message_id={}'.format(
            str(uuid.uuid4())))
        log.info('testing INFO message_id={}'.format(
            str(uuid.uuid4())))
        log.error('testing ERROR message_id={}'.format(
            str(uuid.uuid4())))
        log.critical('testing CRITICAL message_id={}'.format(
            str(uuid.uuid4())))
        log.warning('testing WARNING message_id={}'.format(
            str(uuid.uuid4())))

        try:
            raise Exception('Throw for testing exceptions')
        except Exception as e:
            log.error((
                'Testing EXCEPTION with ex={} message_id={}').format(
                    e,
                    str(uuid.uuid4())))
        # end of try/ex

        msg_sent += 6
        if msg_sent >= max_recs:
            not_done = False
    # end of while

    """
    The threaded and multiprocessing Splunk Publishers
    require an exit sleep to prevent message loss when
    the parent process exits. The other handler(s) do not.
    """
    wait_for_exit.wait_for_exit(log)

# end of run_main


if __name__ == '__main__':
    run_main()
