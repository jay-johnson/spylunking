"""
Publish to Splunk using a ``multiprocessing.Process`` worker

Including a handler derived from the original repository:
https://github.com/zach-taylor/splunk_handler

This version was built to fix issues seen
with multiple Celery worker processes.

"""
import os
import sys
import json
import logging
import socket
import time
import traceback
import multiprocessing
import requests
from spylunking.ppj import ppj
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

is_py2 = sys.version[0] == '2'
if is_py2:
    import Queue as queue
else:
    import queue as queue


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
            sleep_interval=None,
            queue_size=0,
            debug=False,
            retry_count=20,
            run_once=False,
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
        :param sleep_interval: Sleep before purging queued
                               logs interval in seconds
        :param queue_size: Queue this number of logs
                           before dropping new logs with
                           0 is an infinite number of messages
        :param debug: debug the publisher
        :param retry_count: number of publish retries per log record
        :param retry_backoff: cooldown timer in seconds
        :param run_once: flag used by tests for publishing once
                         and shutting down
        """

        logging.Handler.__init__(self)

        self.host = host
        self.port = port
        self.token = token
        self.index = index
        self.source = source
        self.sourcetype = sourcetype
        self.verify = verify
        self.timeout = timeout
        self.sleep_interval = sleep_interval
        if self.sleep_interval is None:
            self.sleep_interval = float(os.getenv(
                'SPLUNK_SLEEP_INTERVAL',
                '0.5'))
        self.log_payload = ''

        self.session = requests.Session()
        self.retry_count = retry_count
        self.retry_backoff = retry_backoff
        self.num_sent = 0

        # Multiprocesing entities
        self.run_once = run_once
        self.processes = []
        self.manager = multiprocessing.Manager()
        self.queue = self.manager.Queue()
        self.exit = multiprocessing.Event()

        self.debug = debug
        if os.getenv(
                'SPLUNK_DEBUG',
                '0') == '1':
            self.debug = True

        # 'True' if application requested exit
        self.shutdown_now = False

        self.write_debug_log('starting debug mode')

        if hostname is None:
            self.hostname = socket.gethostname()
        else:
            self.hostname = hostname

        self.write_debug_log('preparing to override loggers')

        # prevent infinite recursion by silencing requests and urllib3 loggers
        logging.getLogger('requests').propagate = False
        logging.getLogger('urllib3').propagate = False

        # and do the same for ourselves
        logging.getLogger(__name__).propagate = False

        # disable all warnings from urllib3 package
        if not self.verify:
            requests.packages.urllib3.disable_warnings()

        # Set up automatic retry with back-off
        self.write_debug_log('preparing to create a Requests session')
        retry = Retry(
            total=self.retry_count,
            backoff_factor=self.retry_backoff,
            method_whitelist=False,  # Retry for any HTTP verb
            status_forcelist=[500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retry))

        self.start_worker_thread()

        self.write_debug_log('class initialize complete')
    # end of __init__

    def emit(
            self,
            record):
        """emit

        Emit handler for queue-ing message for
        the helper thread to send to Splunk on the ``self.sleep_interval``

        :param record: LogRecord to send to Splunk
                       https://docs.python.org/3/library/logging.html
        """
        self.write_debug_log('emit - start')

        try:
            record = self.format_record(
                record)
        except Exception as e:
            self.write_log(
                'exception in Splunk logging handler: %s' % str(e))
            self.write_log(
                traceback.format_exc())
            return

        if not self.is_shutting_down() and self.sleep_interval > 0.1:
            try:
                self.write_debug_log(
                    'writing record to log queue')
                # Put log message into queue; worker thread will pick up
                self.queue.put(
                    record)
            except Exception as e:
                self.write_log(
                    'log queue full; log data will be dropped.')
        else:
            # Flush log immediately; this is a blocking call
            self.publish_to_splunk(
                payload=record)

        self.write_debug_log('emit - done')
    # end of emit

    def close(self):
        """close"""
        self.write_debug_log(
            'close - start shutdown')
        self.shutdown()
        logging.Handler.close(self)
        self.write_debug_log(
            'close - handler join on processes={}'.format(
                len(self.processes)))
        for process in self.processes:
            process.terminate()
            process.join()
        self.write_debug_log(
            'close - done')
    # end of close

    def start_worker_thread(
            self):
        """start_worker_thread

        Start the helper worker thread to publish queued messages
        to Splunk
        """
        # Start a worker thread responsible for sending logs
        if not self.is_shutting_down() and self.sleep_interval > 0.1:
            self.processes = []
            self.write_debug_log(
                'starting multiprocessing.Process')
            p = multiprocessing.Process(
                target=self.perform_work)
            self.processes.append(p)
            p.start()
    # end of start_worker_thread

    def write_log(
            self,
            log_message):
        """write_log

        :param log_message: message to log
        """
        print('splunk-pub {}'.format(log_message))
    # end of write_log

    def write_debug_log(
            self,
            log_message):
        """write_debug_log

        :param log_message: message to log
        """
        if self.debug:
            print('splunk-pub DEBUG {}'.format(log_message))
    # end of write_debug_log

    def format_record(
            self,
            record):
        """format_record

        :param record: message to format
        """
        self.write_debug_log(
            'format_record - start')

        if self.source is None:
            source = record.pathname
        else:
            source = self.source

        current_time = time.time()

        params = {
            'time': current_time,
            'host': self.hostname,
            'index': self.index,
            'source': source,
            'sourcetype': self.sourcetype,
            'event': self.format(record),
        }

        self.write_debug_log(
            'record dictionary created')

        formatted_record = json.dumps(
            params,
            sort_keys=True)

        self.write_debug_log(
            'format_record - done')

        return formatted_record
    # end of format_record

    def perform_work(
            self):
        """perform_work

        Process handler function for processing messages
        found in the ``multiprocessing.Manager.queue``

        Build the ``self.log_payload`` from the queued log messages
        and POST it to the Splunk endpoint

        """

        self.write_debug_log((
            'perform_work - start'))
        try:

            not_done = not self.is_shutting_down()

            while not_done:

                try:
                    self.build_payload_from_queued_messages()
                except Exception as e:
                    if self.is_shutting_down():
                        self.write_debug_log(
                            'perform_work - done - detected shutdown')
                    else:
                        self.write_log((
                            'perform_work - done - Exception in '
                            'shutting down for ex={}').format(
                                e))
                        self.shutdown()
                    return
                # end of try to return if the queue

                self.publish_to_splunk()

                if self.is_shutting_down():
                    self.write_debug_log(
                        'perform_work - done - shutdown detected')
                    return
                else:
                    counter = 0
                    while counter <= self.sleep_interval:
                        if self.is_shutting_down():
                            self.write_debug_log(
                                'publish_to_splunk - shutting down')
                            not_done = False
                            counter = self.sleep_interval
                            break
                        else:
                            self.write_debug_log((
                                ' - msgs={} '
                                'sleep_interval={}/{}s').format(
                                    self.num_sent,
                                    counter,
                                    self.sleep_interval))
                            time.sleep(1.0)
                            counter += 1
                        # if shutting down or just sleeping
                    # end of while resting, periodically check if the shutdown
                    # was sent
                # check if done

                self.num_sent = 0
            # end of while not done

        except Exception as e:
            if self.is_shutting_down():
                self.write_debug_log((
                    'perform_work - shutdown sent={}').format(
                        self.num_sent))
            else:
                self.write_debug_log((
                    'perform_work - ex={}').format(
                        e))
        # end of try/ex

        self.write_debug_log((
            'perform_work - done'))

    # end of perform_work

    def publish_to_splunk(
            self,
            payload=None):
        """publish_to_splunk

        :param payload: optional string log message to send to Splunk
        """

        self.write_debug_log((
            'publish_to_splunk - start'))

        use_payload = payload
        if not use_payload:
            use_payload = self.log_payload

        if use_payload:
            self.write_debug_log(
                'payload available for sending')

            url = 'https://{}:{}/services/collector'.format(
                self.host,
                self.port)
            self.write_debug_log(
                'destination URL is ' + url)

            try:
                if self.debug:
                    try:
                        msg_dict = json.loads(use_payload)
                        event_data = json.loads(msg_dict['event'])
                        msg_dict['event'] = event_data
                        self.write_debug_log((
                            'sending payload: {}').format(
                                ppj(msg_dict)))
                    except Exception:
                        self.write_debug_log((
                            'sending data payload: {}').format(
                                use_payload))

                if self.num_sent > 100000:
                    self.num_sent = 0
                else:
                    self.num_sent += 1
                r = self.session.post(
                    url,
                    data=use_payload,
                    headers={
                        'Authorization': 'Splunk {}'.format(
                            self.token)
                    },
                    verify=self.verify,
                    timeout=self.timeout
                )
                # Throws exception for 4xx/5xx status
                r.raise_for_status()
                self.write_debug_log(
                    'payload sent successfully')

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
        # end of publish handling

        self.write_debug_log((
            'publish_to_splunk - done - '
            'self.is_shutting_down={} self.shutdown_now={}').format(
                self.is_shutting_down(),
                self.shutdown_now))
    # end of publish_to_splunk

    def build_payload_from_queued_messages(
            self):
        """build_payload_from_queued_messages

        Empty the queued messages by building a large ``self.log_payload``
        """
        not_done = True
        while not_done:

            if self.is_shutting_down():
                self.write_debug_log(
                    'build_payload shutting down')
                return True

            self.write_debug_log('reading from queue')
            try:
                msg = self.queue.get(
                    block=False)
                self.log_payload = self.log_payload + msg
                if self.debug:
                    self.write_debug_log('got queued message={}'.format(
                        msg))
                not_done = not self.queue.empty()
            except queue.Empty:
                self.write_debug_log((
                    'done emptying queue'))
                return True
            except Exception as e:
                if self.is_shutting_down():
                    self.write_debug_log(
                        'helper was shut down '
                        'msgs in the queue may not all '
                        'have been sent')
                else:
                    self.write_debug_log((
                        'helper hit an ex={} shutting down '
                        'msgs in the queue may not all '
                        'have been sent').format(
                            e))
                    not_done = True
                    self.shutdown_now = True
                return True
            # end of getting log msgs from the queue

            if self.is_shutting_down():
                self.write_debug_log(
                    'build_payload - already shutting down')
                return True

            # If the payload is getting very long,
            # stop reading and send immediately.
            # Current limit is 50MB
            if self.is_shutting_down() or len(self.log_payload) >= 524288:
                self.write_debug_log(
                    'payload maximum size exceeded, sending immediately')
                return False

        return True
    # end of build_payload_from_queued_messages

    def force_flush(
            self):
        """force_flush

        Flush the queue and publish everything to Splunk
        """
        self.write_debug_log('force flush requested')
        self.publish_to_splunk()
    # end of force_flush

    def is_shutting_down(
            self):
        """is_shutting_down"""
        return self.exit.is_set() or self.shutdown_now or self.run_once
    # end of is_shutting_down

    def shutdown(
            self):
        """shutdown
        """

        # Only initiate shutdown once
        if self.is_shutting_down():
            self.write_debug_log('shutdown - still shutting down')
            return
        else:
            self.write_debug_log('shutdown - start')
            self.exit.set()
        # if/else already shutting down

        self.write_debug_log('shutdown - setting shutdown_now=True')
        self.shutdown_now = True

        self.write_debug_log(
            'shutdown - trying to publish remaining msgs')

        # Send the remaining items that might be sitting in queue.
        self.publish_to_splunk()
        self.write_debug_log('shutdown - done')
    # end of shutdown

# end of SplunkPublisher
