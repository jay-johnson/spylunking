"""
Including a handler derived from the original repository:
https://github.com/zach-taylor/splunk_handler

This version was built to fix issues seen
with multiple Celery worker processes.
"""
import os
import atexit
import json
import logging
import socket
import time
import traceback
import multiprocessing
import requests
from threading import Timer
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


# For keeping track of running class instances
instances = []


# Called when application exit imminent (main thread ended / got kill signal)
@atexit.register
def perform_exit():
    """perform_exit

    Handling at-the-exit events
    ---------------------------

    This will cleanup each worker process which
    could be in the middle of a request/sleep/block
    action. This has been tested on python 3 with
    Celery and single processes.

    """
    worked = True
    for instance in instances:
        try:
            instance.shutdown()
        except Exception:
            worked = False
    if not worked:
        if os.getenv(
                'SPLUNK_DEBUG',
                '0') == '1':
            print('Failed exiting')
# end of perform_exit


def force_flush():
    """force_flush"""
    worked = True
    for instance in instances:
        try:
            instance.force_flush()
        except Exception:
            worked = False
    if not worked:
        if os.getenv(
                'SPLUNK_DEBUG',
                '0') == '1':
            print('Failed flushing queues')
# end of force_flush


class SplunkPublisher(logging.Handler):
    """
    A logging handler to send logs to a Splunk Enterprise instance
    running the Splunk HTTP Event Collector.
    Originally inspired from the repository:
    https://github.com/zach-taylor/splunk_handler
    This class allows multiple processes like Celery workers
    to reliably publish logs to Splunk from inside of a Celery task
    """

    def __init__(
            self,
            host,
            port,
            token,
            index,
            hostname=None,
            source=None,
            sourcetype='text',
            verify=True,
            timeout=60,
            flush_interval=2.0,
            queue_size=0,
            debug=False,
            retry_count=20,
            retry_backoff=2.0):
        """__init__
        Initialize the SplunkPublisher
        :param host: Splunk fqdn
        :param port: Splunk HEC Port 8088
        :param token: Pre-existing Splunk token
        :param index: Splunk index
        :param hostname: Splunk address <host:port>
        :param source: source for log records
        :param sourcetype: json
        :param verify: verify using certs
        :param timeout: HTTP request timeout in seconds
        :param flush_interval: Flush the queue of logs interval in seconds
        :param queue_size: Queue this number of logs before dropping
                           new logs with 0 is an infinite number of messages
        :param debug: debug the publisher
        :param retry_count: number of publish retries per log record
        :param retry_backoff: cooldown timer in seconds
        """

        global instances
        instances.append(self)
        logging.Handler.__init__(self)

        self.host = host
        self.port = port
        self.token = token
        self.index = index
        self.source = source
        self.sourcetype = sourcetype
        self.verify = verify
        self.timeout = timeout
        self.flush_interval = flush_interval
        self.log_payload = ''
        self.timer = None
        self.manager = multiprocessing.Manager()
        self.queue = self.manager.Queue()
        self.session = requests.Session()
        self.retry_count = retry_count
        self.retry_backoff = retry_backoff
        self.testing = False

        self.debug = debug
        if os.getenv(
                'SPLUNK_DEBUG',
                '0') == '1':
            self.debug = True

        # 'True' if application requested exit
        self.SIGTERM = False

        self.write_debug_log('Starting debug mode')

        if hostname is None:
            self.hostname = socket.gethostname()
        else:
            self.hostname = hostname

        self.write_debug_log('Preparing to override loggers')

        # prevent infinite recursion by silencing requests and urllib3 loggers
        logging.getLogger('requests').propagate = False
        logging.getLogger('urllib3').propagate = False

        # and do the same for ourselves
        logging.getLogger(__name__).propagate = False

        # disable all warnings from urllib3 package
        if not self.verify:
            requests.packages.urllib3.disable_warnings()

        # Set up automatic retry with back-off
        self.write_debug_log('Preparing to create a Requests session')
        retry = Retry(total=self.retry_count,
                      backoff_factor=self.retry_backoff,
                      method_whitelist=False,  # Retry for any HTTP verb
                      status_forcelist=[500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retry))

        self.start_worker_thread()

        self.write_debug_log('Class initialize complete')
    # end of __init__

    def emit(
            self,
            record):
        """emit
        Emit handler for queue-ing message for
        the helper thread to send to Splunk on the ``flush_interval``
        :param record: LogRecord to send to Splunk
                       https://docs.python.org/3/library/logging.html
        """
        self.write_debug_log('emit() called')

        try:
            record = self.format_record(
                record)
        except Exception as e:
            self.write_log(
                'Exception in Splunk logging handler: %s' % str(e))
            self.write_log(
                traceback.format_exc())
            return

        if self.flush_interval > 0:
            try:
                self.write_debug_log('Writing record to log queue')
                # Put log message into queue; worker thread will pick up
                self.queue.put_nowait(
                    record)
            except Exception as e:
                self.write_log(
                    'Log queue full; log data will be dropped.')
        else:
            # Flush log immediately; is blocking call
            self.publish_to_splunk(
                payload=record)
    # end of emit

    def close(self):
        """close"""
        self.shutdown()
        logging.Handler.close(self)
    # end of close

    def start_worker_thread(
            self):
        """start_worker_thread
        Start the helper worker thread to publish queued messages
        to Splunk
        """
        # Start a worker thread responsible for sending logs
        if self.flush_interval > 0:
            self.write_debug_log(
                'Preparing to spin off first worker thread Timer')
            self.timer = Timer(
                self.flush_interval,
                self.publish_to_splunk)
            self.timer.daemon = True  # Auto-kill thread if main process exits
            self.timer.start()
    # end of start_worker_thread

    def write_log(
            self,
            log_message):
        """write_log
        :param log_message: message to log
        """
        print('[SplunkPub] {}'.format(log_message))
    # end of write_log

    def write_debug_log(
            self,
            log_message):
        """write_debug_log
        :param log_message: message to log
        """
        if self.debug:
            print('[SplunkPub] DEBUG {}'.format(log_message))
    # end of write_debug_log

    def format_record(
            self,
            record):
        """format_record
        :param record: message to format
        """
        self.write_debug_log('format_record() called')

        if self.source is None:
            source = record.pathname
        else:
            source = self.source

        current_time = time.time()
        if self.testing:
            current_time = None

        params = {
            'time': current_time,
            'host': self.hostname,
            'index': self.index,
            'source': source,
            'sourcetype': self.sourcetype,
            'event': self.format(record),
        }

        self.write_debug_log('Record dictionary created')

        formatted_record = json.dumps(params, sort_keys=True)
        self.write_debug_log('Record formatting complete')

        return formatted_record
    # end of format_record

    def publish_to_splunk(self, payload=None):
        """publish_to_splunk
        Build the ``self.log_payload`` from the queued log messages
        and POST it to the Splunk endpoint
        :param payload: string message to send to Splunk
        """
        self.write_debug_log('publish_to_splunk() called')

        if self.flush_interval > 0:
            # Stop the timer. Happens automatically if this is called
            # via the timer, does not if invoked by force_flush()
            self.timer.cancel()

            queue_is_empty = self.empty_queue()

        if not payload:
            payload = self.log_payload

        if payload:
            self.write_debug_log('Payload available for sending')
            url = 'https://%s:%s/services/collector' % (self.host, self.port)
            self.write_debug_log('Destination URL is ' + url)

            try:
                self.write_debug_log(
                    'Sending payload: ' + payload)
                r = self.session.post(
                    url,
                    data=payload,
                    headers={'Authorization': 'Splunk %s' % self.token},
                    verify=self.verify,
                    timeout=self.timeout,
                )
                r.raise_for_status()  # Throws exception for 4xx/5xx status
                self.write_debug_log('Payload sent successfully')

            except Exception as e:
                try:
                    self.write_log(
                        'Exception in Splunk logging handler: {}'.format(
                            e))
                    self.write_log(traceback.format_exc())
                except Exception:
                    self.write_debug_log(
                        'Exception encountered,'
                        'but traceback could not be formatted')

            self.log_payload = ''
        else:
            self.write_debug_log(
                'Timer thread executed but no payload was available to send')

        # Restart the timer
        if self.flush_interval > 0:
            timer_interval = self.flush_interval
            if self.SIGTERM:
                self.write_debug_log(
                    'Timer reset aborted due to SIGTERM received')
            else:
                if not queue_is_empty:
                    self.write_debug_log(
                        'Queue not empty, scheduling timer to run immediately')
                    # Start up again right away if queue was not cleared
                    timer_interval = 1.0

                self.write_debug_log('Resetting timer thread')
                self.timer = Timer(timer_interval, self.publish_to_splunk)
                # Auto-kill thread if main process exits
                self.timer.daemon = True
                self.timer.start()
                self.write_debug_log('Timer thread scheduled')
    # end of publish_to_splunk

    def empty_queue(
            self):
        """empty_queue
        Empty the queued messages by building a large ``self.log_payload``
        """
        while not self.queue.empty():
            self.write_debug_log('Recursing through queue')
            try:
                item = self.queue.get(block=False)
                self.log_payload = self.log_payload + item
                self.queue.task_done()
                self.write_debug_log('Queue task completed')
            except Exception as e:
                self.write_debug_log((
                    'Error - Queue get hit ex={} '
                    'empty').format(
                        e))

            # If the payload is getting very long,
            # stop reading and send immediately.
            # Current limit is 50MB
            if not self.SIGTERM and len(self.log_payload) >= 524288:
                self.write_debug_log(
                    'Payload maximum size exceeded, sending immediately')
                return False

        return True
    # end of empty_queue

    def force_flush(
            self):
        """force_flush
        Flush the queue and publish everything to Splunk
        """
        self.write_debug_log('Force flush requested')
        self.publish_to_splunk()
    # end of force_flush

    def shutdown(
            self):
        """shutdown"""
        self.write_debug_log('Immediate shutdown requested')

        # Only initiate shutdown once
        if self.SIGTERM:
            return

        self.write_debug_log('Setting instance SIGTERM=True')
        self.SIGTERM = True

        if self.flush_interval > 0:
            # Cancels the scheduled Timer, allows exit immediately
            self.timer.cancel()

        self.write_debug_log(
            'Starting up the final run of the worker thread before shutdown')
        # Send the remaining items that might be sitting in queue.
        self.publish_to_splunk()
    # end of shutdown

# end of SplunkPublisher
