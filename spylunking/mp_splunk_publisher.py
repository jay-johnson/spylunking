"""
Publish to Splunk using a ``multiprocessing.Process`` worker

Including a handler derived from the original repository:
https://github.com/zach-taylor/splunk_handler

Please note this will not work with Celery. Please use
the ``spylunking.splunk_publisher.SplunkPublisher`` if you want
to see logs inside a Celery task.

Supported environment variables:

::

    export SPLUNK_HOST="<splunk host>"
    export SPLUNK_PORT="<splunk port: 8088>"
    export SPLUNK_API_PORT="<splunk port: 8089>"
    export SPLUNK_ADDRESS="<splunk address host:port>"
    export SPLUNK_API_ADDRESS="<splunk api address host:port>"
    export SPLUNK_TOKEN="<splunk token>"
    export SPLUNK_INDEX="<splunk index>"
    export SPLUNK_SOURCE="<splunk source>"
    export SPLUNK_SOURCETYPE="<splunk sourcetype>"
    export SPLUNK_VERIFY="<verify certs on HTTP POST>"
    export SPLUNK_TIMEOUT="<timeout in seconds>"
    export SPLUNK_QUEUE_SIZE="<num msgs allowed in queue - 0=infinite>"
    export SPLUNK_SLEEP_INTERVAL="<sleep in seconds per batch>"
    export SPLUNK_RETRY_COUNT="<attempts per log to retry publishing>"
    export SPLUNK_RETRY_BACKOFF="<cooldown in seconds per failed POST>"
    export SPLUNK_DEBUG="<1 enable debug|0 off>"

"""

import json
import logging
import time
import traceback
import requests
import signal
import multiprocessing
import spylunking.send_to_splunk as send_to_splunk
from spylunking.rnow import rnow
from spylunking.ppj import ppj
from spylunking.consts import SPLUNK_HOST
from spylunking.consts import SPLUNK_PORT
from spylunking.consts import SPLUNK_TOKEN
from spylunking.consts import SPLUNK_INDEX
from spylunking.consts import SPLUNK_SOURCE
from spylunking.consts import SPLUNK_SOURCETYPE
from spylunking.consts import SPLUNK_VERIFY
from spylunking.consts import SPLUNK_TIMEOUT
from spylunking.consts import SPLUNK_SLEEP_INTERVAL
from spylunking.consts import SPLUNK_RETRY_COUNT
from spylunking.consts import SPLUNK_RETRY_BACKOFF
from spylunking.consts import SPLUNK_QUEUE_SIZE
from spylunking.consts import SPLUNK_DEBUG
from spylunking.consts import SPLUNK_HOSTNAME
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


class MPSplunkPublisher(logging.Handler):
    """
    A logging handler to send logs to a Splunk Enterprise instance
    running the Splunk HTTP Event Collector.

    Originally inspired from the repository but written for
    python's multiprocessing framework:
    https://github.com/zach-taylor/splunk_handler

    This class allows multiple processes like Celery workers
    to reliably publish logs to Splunk from inside of a Celery task

    """

    def __init__(
            self,
            host=None,
            port=None,
            address=None,
            token=None,
            index=None,
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

        Initialize the MPSplunkPublisher with support for
        multiprocessing

        :param host: Splunk fqdn
        :param port: Splunk HEC Port 8088
        :param address: Splunk fqdn:8088 - overrides host and port
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
        if self.host is None:
            self.host = SPLUNK_HOST
        self.port = port
        if self.port is None:
            self.port = SPLUNK_PORT
        if address:
            address_split = address.split(':')
            self.host = address_split[0]
            self.port = int(address_split[1])
        self.token = token
        if self.token is None:
            self.token = SPLUNK_TOKEN
        self.index = index
        if self.index is None:
            self.index = SPLUNK_INDEX
        self.source = source
        if self.source is None:
            self.source = SPLUNK_SOURCE
        self.sourcetype = sourcetype
        if self.sourcetype is None:
            self.sourcetype = SPLUNK_SOURCETYPE
        self.verify = verify
        if self.verify is None:
            self.verify = SPLUNK_VERIFY
        self.timeout = timeout
        if self.timeout is None:
            self.timeout = SPLUNK_TIMEOUT
        self.sleep_interval = sleep_interval
        if self.sleep_interval is None:
            self.sleep_interval = SPLUNK_SLEEP_INTERVAL
        self.retry_count = retry_count
        if self.retry_count is None:
            self.retry_count = SPLUNK_RETRY_COUNT
        self.retry_backoff = retry_backoff
        if self.retry_backoff is None:
            self.retry_backoff = SPLUNK_RETRY_BACKOFF
        self.queue_size = queue_size
        if self.queue_size is None:
            self.queue_size = SPLUNK_QUEUE_SIZE

        self.log_payload = ''

        self.session = requests.Session()
        self.num_sent = 0

        # Multiprocesing entities
        self.run_once = run_once
        self.processes = []
        self.manager = multiprocessing.Manager()
        self.queue = self.manager.Queue(maxsize=self.queue_size)
        self.shutdown_event = multiprocessing.Event()
        self.shutdown_ack = multiprocessing.Event()
        self.already_done = multiprocessing.Event()

        self.debug = debug
        if SPLUNK_DEBUG:
            self.debug = True

        # True if application requested exit
        self.shutdown_now = False

        self.debug_log('starting debug mode')

        self.hostname = hostname
        if hostname is None:
            self.hostname = SPLUNK_HOSTNAME

        self.debug_log('preparing to override loggers')

        # prevent infinite recursion by silencing requests and urllib3 loggers
        logging.getLogger('requests').propagate = False
        logging.getLogger('urllib3').propagate = False

        # and do the same for ourselves
        logging.getLogger(__name__).propagate = False

        # disable all warnings from urllib3 package
        if not self.verify:
            requests.packages.urllib3.disable_warnings()

        # Set up automatic retry with back-off
        self.debug_log('preparing to create a Requests session')
        retry = Retry(
            total=self.retry_count,
            backoff_factor=self.retry_backoff,
            method_whitelist=False,  # Retry for any HTTP verb
            status_forcelist=[500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retry))

        self.start_worker()

        self.debug_log('class initialize complete')
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
        self.debug_log('emit - start')

        try:
            record = self.format_record(
                record)
        except Exception as e:
            self.write_log(
                'exception in Splunk logging handler: %s' % str(e))
            self.write_log(
                traceback.format_exc())
            return

        if not self.is_shutting_down(shutdown_event=self.shutdown_event) \
                and self.sleep_interval > 0.1:
            try:
                self.debug_log(
                    'writing to queue={}'.format(
                        self.queue))
                # Put log message into queue; worker thread will pick up
                self.queue.put(
                    record)
            except Exception as e:
                self.write_log(
                    'log queue full; log data will be dropped.')
        else:
            # Publish immediately because there is no worker
            self.publish_to_splunk(
                payload=record)

        self.debug_log('emit - done')
    # end of emit

    def start_worker(
            self):
        """start_worker

        Start the helper worker process to package queued messages
        and send them to Splunk
        """
        # Start a worker thread responsible for sending logs
        if not self.is_shutting_down(shutdown_event=self.shutdown_event) \
                and self.sleep_interval > 0.1:
            self.processes = []
            self.debug_log(
                'start_worker - start multiprocessing.Process')
            p = multiprocessing.Process(
                target=self.perform_work,
                args=(
                    self.queue,
                    self.shutdown_event,
                    self.shutdown_ack,
                    self.already_done))
            p.daemon = True
            p.start()
            self.processes.append({
                'process': p,
                'shutdown_event': self.shutdown_event,
                'shutdown_ack_event': self.shutdown_ack,
                'already_done_event': self.already_done
            })
            self.debug_log(
                'start_worker - done')
    # end of start_worker

    def write_log(
            self,
            log_message):
        """write_log

        :param log_message: message to log
        """
        print('{} mpsplunkpub {}'.format(
            rnow(),
            log_message))
    # end of write_log

    def debug_log(
            self,
            log_message):
        """debug_log

        Write logs that only show up in debug mode.
        To turn on debugging with environment variables
        please set this environment variable:

        ::

            export SPLUNK_DEBUG="1"

        :param log_message: message to log
        """
        if self.debug:
            print('{} mpsplunkpub DEBUG {}'.format(
                rnow(),
                log_message))
    # end of debug_log

    def format_record(
            self,
            record):
        """format_record

        Convert a log record into a Splunk-ready format

        :param record: message to format
        """
        self.debug_log(
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

        self.debug_log(
            'record dictionary created')

        formatted_record = json.dumps(
            params,
            sort_keys=True)

        self.debug_log(
            'format_record - done')

        return formatted_record
    # end of format_record

    def perform_work(
            self,
            use_queue,
            shutdown_event,
            shutdown_ack_event,
            already_done_event):
        """perform_work

        Process handler function for processing messages
        found in the ``multiprocessing.Manager.queue``

        Build the ``self.log_payload`` from the queued log messages
        and POST it to the Splunk endpoint

        :param use_queue: multiprocessing.Queue - queue holding the messages
        :param shutdown_event: multiprocessing.Event - shutdown event
        :param shutdown_ack_event: multiprocessing.Event -
                                   acknowledge shutdown is in progress
        :param already_done_event: multiprocessing.Event -
                                   already shutting down
        """

        self.debug_log((
            'perform_work - start'))

        # Handle CTRL + C
        signal.signal(
            signal.SIGINT,
            signal.SIG_IGN)

        self.debug_log((
            'perform_work - ready'))

        try:

            not_done = not self.is_shutting_down(
                shutdown_event=shutdown_event)

            while not_done:

                try:
                    self.build_payload_from_queued_messages(
                        use_queue=use_queue,
                        shutdown_event=shutdown_event)
                except Exception as e:
                    if self.is_shutting_down(
                            shutdown_event=shutdown_event):
                        self.debug_log(
                            'perform_work - done - detected shutdown')
                    else:
                        self.debug_log((
                            'perform_work - done - '
                            'Exception shutting down with ex={}').format(
                                e))
                        self.shutdown()
                    already_done_event.set()
                    return
                # end of try to return if the queue

                self.publish_to_splunk()

                if self.is_shutting_down(
                        shutdown_event=shutdown_event):
                    self.debug_log(
                        'perform_work - done - shutdown detected')
                    already_done_event.set()
                    return
                # check if done

                self.num_sent = 0
            # end of while not done

        except Exception as e:
            if self.is_shutting_down(
                    shutdown_event=shutdown_event):
                self.debug_log((
                    'perform_work - shutdown sent={}').format(
                        self.num_sent))
            else:
                self.debug_log((
                    'perform_work - ex={}').format(
                        e))
        # end of try/ex

        already_done_event.set()

        self.debug_log((
            'perform_work - done'))

    # end of perform_work

    def publish_to_splunk(
            self,
            payload=None,
            shutdown_event=None,
            shutdown_ack_event=None,
            already_done_event=None):
        """publish_to_splunk

        Publish the queued messages to Splunk

        :param payload: optional string log message to send to Splunk
        :param shutdown_event: multiprocessing.Event - shutdown event
        :param shutdown_ack_event: multiprocessing.Event -
                                   acknowledge shutdown is in progress
        :param already_done_event: multiprocessing.Event -
                                   already shutting down
        """

        self.debug_log((
            'publish_to_splunk - start'))

        use_payload = payload
        if not use_payload:
            use_payload = self.log_payload

        if use_payload:
            self.debug_log(
                'payload available for sending')

            url = 'https://{}:{}/services/collector'.format(
                self.host,
                self.port)
            self.debug_log(
                'destination URL={}'.format(
                    url))

            try:
                if self.debug:
                    try:
                        msg_dict = json.loads(use_payload)
                        event_data = json.loads(msg_dict['event'])
                        msg_dict['event'] = event_data
                        self.debug_log((
                            'sending payload: {}').format(
                                ppj(msg_dict)))
                    except Exception:
                        self.debug_log((
                            'sending data payload: {}').format(
                                use_payload))

                if self.num_sent > 100000:
                    self.num_sent = 0
                else:
                    self.num_sent += 1
                send_to_splunk.send_to_splunk(
                    session=self.session,
                    url=url,
                    data=use_payload,
                    headers={'Authorization': 'Splunk {}'.format(
                        self.token)},
                    verify=self.verify,
                    timeout=self.timeout)
                self.debug_log(
                    'payload sent successfully')

            except Exception as e:
                try:
                    self.write_log(
                        'Exception in Splunk logging handler: {}'.format(
                            e))
                    self.write_log(traceback.format_exc())
                except Exception:
                    self.debug_log(
                        'Exception encountered,'
                        'but traceback could not be formatted')

            self.log_payload = ''
        # end of publish handling

        self.debug_log((
            'publish_to_splunk - done - '
            'self.is_shutting_down={} self.shutdown_now={}').format(
                self.is_shutting_down(shutdown_event=self.shutdown_event),
                self.shutdown_now))
    # end of publish_to_splunk

    def build_payload_from_queued_messages(
            self,
            use_queue,
            shutdown_event):
        """build_payload_from_queued_messages

        Empty the queued messages by building a large ``self.log_payload``

        :param use_queue: queue holding the messages
        :param shutdown_event: shutdown event
        """
        not_done = True
        while not_done:

            if self.is_shutting_down(
                    shutdown_event=shutdown_event):
                self.debug_log(
                    'build_payload shutting down')
                return True

            self.debug_log('reading from queue={}'.format(
                str(use_queue)))
            try:
                msg = use_queue.get(
                    block=True,
                    timeout=self.sleep_interval)
                self.log_payload = self.log_payload + msg
                if self.debug:
                    self.debug_log('got queued message={}'.format(
                        msg))
                not_done = not self.queue_empty(
                    use_queue=use_queue)
            except Exception as e:
                if self.is_shutting_down(
                        shutdown_event=shutdown_event):
                    self.debug_log(
                        'helper was shut down '
                        'msgs in the queue may not all '
                        'have been sent')
                else:
                    self.debug_log((
                        'helper hit an ex={} shutting down '
                        'msgs in the queue may not all '
                        'have been sent').format(
                            e))
                    not_done = True
                    self.shutdown_now = True
                return True
            # end of getting log msgs from the queue
            self.debug_log('done reading from queue')

            if self.is_shutting_down(
                    shutdown_event=shutdown_event):
                self.debug_log(
                    'build_payload - already shutting down')
                return True

            # If the payload is getting very long,
            # stop reading and send immediately.
            # Current limit is 50MB
            if self.is_shutting_down(shutdown_event=shutdown_event) \
                    or len(self.log_payload) >= 524288:
                self.debug_log(
                    'payload maximum size exceeded, sending immediately')
                return False

        self.debug_log('build_payload - done')

        return True
    # end of build_payload_from_queued_messages

    def queue_empty(
            self,
            use_queue):
        """queue_empty

        :param use_queue: queue to test
        """
        if hasattr(use_queue, 'empty'):
            return use_queue.empty()
        else:
            return use_queue.qsize() == 0
    # end of queue_empty

    def force_flush(
            self):
        """force_flush

        Flush the queue and publish everything to Splunk
        """
        self.debug_log('force flush requested')
        self.perform_work(
            self.queue,
            self.shutdown_event,
            self.shutdown_ack,
            self.already_done)
    # end of force_flush

    def is_shutting_down(
            self,
            shutdown_event):
        """is_shutting_down

        Determine if the parent is shutting down or this was
        triggered to shutdown

        :param shutdown_event: shutdown event
        """

        return bool(
            shutdown_event.is_set()
            or self.shutdown_now
            or self.run_once)
    # end of is_shutting_down

    def close(self):
        """close"""
        self.debug_log(
            'close - start shutdown')
        self.shutdown()
        logging.Handler.close(self)
        self.debug_log(
            'close - handler join on processes={}'.format(
                len(self.processes)))
        self.debug_log(
            'close - done')
    # end of close

    def shutdown(
            self):
        """shutdown
        """

        # Only initiate shutdown once
        if self.is_shutting_down(
                shutdown_event=self.shutdown_event):
            self.debug_log('shutdown - still shutting down')
            return
        else:
            self.debug_log('shutdown - start - setting instance shutdown')
            self.shutdown_now = True
            self.shutdown_event.set()
        # if/else already shutting down

        self.debug_log(
            'shutdown - trying to publish remaining msgs')

        # Send the remaining items that might be sitting in queue.
        self.perform_work(
            self.queue,
            self.shutdown_event,
            self.shutdown_ack,
            self.already_done)

        self.debug_log('shutdown - joining')

        for p in self.processes:
            p['shutdown_event'].set()

        self.debug_log('shutdown - done')
    # end of shutdown

# end of MPSplunkPublisher
