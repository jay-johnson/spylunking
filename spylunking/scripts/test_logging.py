#!/usr/bin/env python

"""
Publish functional testing logs to splunk using the logger
"""

import time
import uuid
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
    Sleep to allow the thread/process to pick up final messages
    before exiting and stopping the Splunk HTTP publisher.

    You can decrease this delay (in seconds) by reducing
    the splunk_sleep_interval or by exporting the env var:
    export SPLUNK_SLEEP_INTERVAL=0.5

    If you set the timer to 0 then it will be a blocking HTTP POST sent
    to Splunk for each log message. This creates a blocking logger in
    your application that will wait until each log's HTTP POST
    was received before continuing.

    Note: Reducing this Splunk sleep timer could result in losing
          messages that were stuck in the queue when the
          parent process exits. The multiprocessing
          Splunk Publisher was built to do this, but will
          not work in certain frameworks like Celery
          as it requires access to spawn daemon processes to
          prevent this 'message loss' case during exiting.
          Applications using this library should ensure
          there's no critical log messages stuck in a queue
          when stopping a long-running process.
    """
    time.sleep(2)

# end of run_main


if __name__ == '__main__':
    run_main()
