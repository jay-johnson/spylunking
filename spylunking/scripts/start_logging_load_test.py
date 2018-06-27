#!/usr/bin/env python

"""

Splunk client load tester for determining how many messages can
this client send over splunk. By default, this tester
sends a batch of 1000 messages and then sleeps to
let the client catch up.

"""

import datetime
import uuid
import time
from spylunking.log.setup_logging import build_colorized_logger


log = build_colorized_logger(
    name="load-test",
    splunk_user="trex",
    splunk_password="123321",
    # handler_name="simple",
    # handler_name="not-real",
    # splunk_address="localhost:8088",
    # splunk_token="55df5127-cb0e-4182-932e-c71c454699b8",
    splunk_debug=False)


def run_main():
    """run_main"""

    start_time = datetime.datetime.now()
    checkpoint = datetime.datetime.now()
    last_checkpoint = datetime.datetime.now()
    end_time = None
    num_logs = 0.0
    running_time = 0.0

    try:
        while True:

            log.debug("testing DEBUG message_id={}".format(
                str(uuid.uuid4())))
            log.info("testing INFO message_id={}".format(
                str(uuid.uuid4())))
            log.error("testing ERROR message_id={}".format(
                str(uuid.uuid4())))
            log.critical("testing CRITICAL message_id={}".format(
                str(uuid.uuid4())))
            log.warn("testing WARN message_id={}".format(
                str(uuid.uuid4())))
            num_logs += 5.0

            if num_logs > 1000000 == 0:
                print("done")
                break

            if num_logs % 1000 == 0:
                checkpoint = datetime.datetime.now()
                running_time = float(
                    (checkpoint - last_checkpoint).total_seconds())
                total_exec_time = float(
                    (checkpoint - start_time).total_seconds())
                print(' - log={} cycle={}s rate: {} time={}s'.format(
                    num_logs,
                    running_time,
                    float(num_logs / running_time),
                    total_exec_time))
                last_checkpoint = datetime.datetime.now()
                time.sleep(1)
    # end of while
    except Exception as e:
        end_time = datetime.datetime.now()
        running_time = float((end_time - start_time).total_seconds())
        print('\n')
        print('start_time={}'.format(start_time))
        print('end_time={}'.format(end_time))
        print('---------------------------')
        print('total_time: {} seconds'.format(running_time))
        print('total_logs: {}'.format(num_logs))
        print('log rate: {}'.format(float(num_logs / running_time)))
    # end of while
# end of run_main


if __name__ == '__main__':
    run_main()
