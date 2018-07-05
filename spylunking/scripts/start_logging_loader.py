#!/usr/bin/env python

"""

Splunk client load tester for determining how many messages can
this client send over splunk. By default, this tester
sends a batch of messages and then sleeps to
let the client catch up.

"""

import datetime
import uuid
from spylunking.log.setup_logging import build_colorized_logger


name = 'load-test-{}'.format(
    datetime.datetime.utcnow().strftime(
        '%Y_%m_%d_%H_%M_%S'))

log = build_colorized_logger(
    name=name,
    splunk_user='trex',
    splunk_password='123321',
    # handler_name='simple',
    # handler_name='not-real',
    # splunk_address='localhost:8088',
    # splunk_token='55df5127-cb0e-4182-932e-c71c454699b8',
    splunk_debug=False)


def run_main():
    """run_main"""

    # max_messages_to_send = 200
    max_messages_to_send = 1000000
    end_time = None
    num_logs_per_batch = 0.0
    num_logs = 0.0
    running_time = 0.0

    start_time = datetime.datetime.utcnow()
    checkpoint = datetime.datetime.utcnow()
    last_checkpoint = datetime.datetime.utcnow()

    try:
        while True:

            log.debug('DEBUG message_id={}'.format(
                str(uuid.uuid4())))
            log.info('INFO message_id={}'.format(
                str(uuid.uuid4())))
            log.error('ERROR message_id={}'.format(
                str(uuid.uuid4())))
            log.critical('CRITICAL message_id={}'.format(
                str(uuid.uuid4())))
            log.warning('WARNING message_id={}'.format(
                str(uuid.uuid4())))
            num_logs += 5.0
            num_logs_per_batch += 5.0

            if num_logs >= max_messages_to_send:
                print('done')
                break

            if num_logs % 10000 == 0:
                checkpoint = datetime.datetime.utcnow()
                running_time = float(
                    (checkpoint - last_checkpoint).total_seconds())
                total_exec_time = float(
                    (checkpoint - start_time).total_seconds())
                print((
                    'sent total_logs={} logs_in_batch={} '
                    'batch_time={}s rate={} '
                    'msg/batch time={}s').format(
                        num_logs,
                        num_logs_per_batch,
                        running_time,
                        float(num_logs_per_batch / running_time),
                        total_exec_time))
                last_checkpoint = checkpoint
                num_logs_per_batch = 0.0
    # end of while
    except Exception as e:
        print('stopping')
    # end of try/ex

    end_time = datetime.datetime.utcnow()
    running_time = float((end_time - start_time).total_seconds())
    print('\n')
    print('start_time={}'.format(start_time))
    print('end_time={}'.format(end_time))
    print('---------------------------')
    print('total_time: {} seconds'.format(running_time))
    print('total_logs: {}'.format(num_logs))
    print('log rate: {}'.format(float(num_logs / running_time)))
    print('')
    search_query = (
        'search index=\"antinex\" AND logger_name=\"{}\" '
        '| stats count').format(
            name)

    print((
        'Find this load test in splunk using the search query: '
        '\n'
        '{}'
        '\n\n'
        'Or with the Spylunking search tool:\n'
        'sp -q \'{}\' ').format(
            search_query,
            search_query))

    print('')
    print('sleeping before pulling load test: {} results'.format(
        name))
    print('pulling load test: {} results'.format(
        name))
# end of run_main


if __name__ == '__main__':
    run_main()
