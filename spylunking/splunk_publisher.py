"""
Including a handler derived from the original repository:
https://github.com/zach-taylor/splunk_handler

This version was built to fix issues seen
with multiple Celery worker processes.

Available environment variables:

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

import sys
import atexit
import traceback
import multiprocessing
import threading
import json
import logging
import socket
import time
import requests
import spylunking.send_to_splunk as send_to_splunk
from threading import Timer
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
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


is_py2 = sys.version[0] == '2'
if is_py2:
    from Queue import Queue  # noqa
else:
    from queue import Queue  # noqa

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
    if SPLUNK_DEBUG:
        print('{} -------------------------------'.format(
            rnow()))
        print('{} splunkpub: atexit.register - start'.format(
            rnow()))
    worked = True
    for instance in instances:
        try:
            if SPLUNK_DEBUG:
                print('{} - shutting down instance={} - start'.format(
                    rnow(),
                    instance))
            instance.shutdown()
            if SPLUNK_DEBUG:
                print('{} - shutting down instance={} - done'.format(
                    rnow(),
                    instance))
        except Exception as e:
            worked = False
            if SPLUNK_DEBUG:
                print(
                    '{} - shutting down instance={} '
                    '- hit ex={} during shutdown'.format(
                        rnow(),
                        instance,
                        e))
        # end of try/ex
    if not worked:
        if SPLUNK_DEBUG:
            print('{} Failed exiting'.format(
                rnow()))
    if SPLUNK_DEBUG:
        print('{} splunkpub: atexit.register - done'.format(
            rnow()))
        print('{} -------------------------------'.format(
            rnow()))
# end of perform_exit


def force_flush():
    """force_flush"""
    if SPLUNK_DEBUG:
        print('{} -------------------------------'.format(
            rnow()))
        print('{} splunkpub: force_flush - start'.format(
            rnow()))
    worked = True
    for instance in instances:
        try:
            instance.force_flush()
        except Exception as e:
            worked = False
            if SPLUNK_DEBUG:
                print(
                    '{} - force_flush instance={} '
                    '- hit ex={}'.format(
                        rnow(),
                        instance,
                        e))
        # end of try/ex
    if not worked:
        if SPLUNK_DEBUG:
            print('{} Failed flushing queues'.format(
                rnow()))
    if SPLUNK_DEBUG:
        print('{} splunkpub: force_flush - done'.format(
            rnow()))
        print('{} -------------------------------'.format(
            rnow()))
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
            sleep_interval=2.0,
            queue_size=0,
            debug=False,
            retry_count=20,
            retry_backoff=2.0,
            run_once=False):
        """__init__

        Initialize the SplunkPublisher

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
        :param sleep_interval: Flush the queue of logs interval in seconds
        :param queue_size: Queue this number of logs before dropping
                           new logs with 0 is an infinite number of messages
        :param debug: debug the publisher
        :param retry_count: number of publish retries per log record
        :param retry_backoff: cooldown timer in seconds
        :param run_once: test flag for running this just one time
        """

        global instances
        instances.append(self)
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

        self.timer = None
        self.tid = None
        self.manager = multiprocessing.Manager()
        self.queue = self.manager.Queue(maxsize=self.queue_size)
        self.session = requests.Session()
        self.shutdown_event = multiprocessing.Event()
        self.shutdown_ack = multiprocessing.Event()
        self.already_done = multiprocessing.Event()
        self.testing = False
        self.shutdown_now = False
        self.run_once = run_once

        self.debug_count = 0
        self.debug = debug
        if SPLUNK_DEBUG:
            self.debug = True

        self.debug_log('starting debug mode')

        if hostname is None:
            self.hostname = socket.gethostname()
        else:
            self.hostname = hostname

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

        self.start_worker_thread(
            sleep_interval=self.sleep_interval)

        self.debug_log((
            'READY init - sleep_interval={}').format(
                self.sleep_interval))
    # end of __init__

    def emit(
            self,
            record):
        """emit

        Emit handler for queue-ing message for
        the helper thread to send to Splunk on the ``sleep_interval``

        :param record: LogRecord to send to Splunk
                       https://docs.python.org/3/library/logging.html
        """

        self.debug_log('emit')

        try:
            record = self.format_record(
                record)
        except Exception as e:
            self.write_log(
                'Exception in Splunk logging handler={}'.format(e))
            self.write_log(
                traceback.format_exc())
            return

        if self.sleep_interval > 0:
            try:
                self.debug_log('put in queue')
                # Put log message into queue; worker thread will pick up
                self.queue.put_nowait(
                    record)
            except Exception as e:
                self.write_log(
                    'log queue full - log data will be dropped.')
        else:
            # Flush log immediately; is blocking call
            self.publish_to_splunk(
                payload=record)
    # end of emit

    def start_worker_thread(
            self,
            sleep_interval=1.0):
        """start_worker_thread

        Start the helper worker thread to publish queued messages
        to Splunk

        :param sleep_interval: sleep in seconds before reading from
                               the queue again
        """
        # Start a worker thread responsible for sending logs
        if self.sleep_interval > 0:
            self.debug_log(
                'starting worker thread')
            self.timer = Timer(
                sleep_interval,
                self.perform_work)
            self.timer.daemon = True  # Auto-kill thread if main process exits
            self.timer.start()
    # end of start_worker_thread

    def write_log(
            self,
            log_message):
        """write_log

        Write logs to stdout

        :param log_message: message to log
        """
        print('{} splunkpub {}'.format(
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
            print('{} splunkpub DEBUG {}'.format(
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
        self.debug_log('format_record - start')

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

        self.debug_log('record dictionary created')

        formatted_record = json.dumps(params, sort_keys=True)

        self.debug_log('format_record - done')

        return formatted_record
    # end of format_record

    def build_payload_from_queued_messages(
            self,
            use_queue,
            shutdown_event,
            triggered_by_shutdown=False):
        """build_payload_from_queued_messages

        Empty the queued messages by building a large ``self.log_payload``

        :param use_queue: queue holding the messages
        :param shutdown_event: shutdown event
        :param triggered_by_shutdown: called during shutdown
        """
        self.debug_log('build_payload - start')

        not_done = True
        while not_done:

            if not triggered_by_shutdown and self.is_shutting_down(
                    shutdown_event=shutdown_event):
                self.debug_log(
                    'build_payload shutting down')
                return True

            self.debug_count += 1
            if self.debug_count > 60:
                self.debug_count = 0
                self.debug_log('build_payload tid={} queue={}'.format(
                    self.tid,
                    str(use_queue)))
            try:
                msg = use_queue.get(
                    block=True,
                    timeout=self.sleep_interval)
                self.log_payload = self.log_payload + msg
                if self.debug:
                    self.debug_log('{} got={}'.format(
                        self,
                        ppj(msg)))
                not_done = not self.queue_empty(
                    use_queue=use_queue)
            except Exception as e:
                if self.is_shutting_down(
                        shutdown_event=shutdown_event):
                    self.debug_log(
                        'helper was shut down '
                        'msgs in the queue may not all '
                        'have been sent')
                if ('No such file or directory' in str(e)
                        or 'Broken pipe' in str(e)):
                    raise e
                elif ("object, typeid 'Queue' at" in str(e)
                        and "'__str__()' failed" in str(e)):
                    raise e
                not_done = True
            # end of getting log msgs from the queue

            if not triggered_by_shutdown and self.is_shutting_down(
                    shutdown_event=shutdown_event):
                self.debug_log(
                    'build_payload - already shutting down')
                return True

            # If the payload is getting very long,
            # stop reading and send immediately.
            # Current limit is 50MB
            if (not triggered_by_shutdown and self.is_shutting_down(
                    shutdown_event=shutdown_event)
                    or len(self.log_payload) >= 524288):
                self.debug_log(
                    'payload maximum size exceeded, sending immediately')
                return False

        self.debug_log('build_payload - done')

        return True
    # end of build_payload_from_queued_messages

    def perform_work(
            self):
        """perform_work

        Process handler function for processing messages
        found in the ``multiprocessing.Manager.queue``

        Build the ``self.log_payload`` from the queued log messages
        and POST it to the Splunk endpoint

        """

        self.debug_log((
            'perform_work - start'))

        self.tid = threading.current_thread().ident

        if self.sleep_interval > 0:
            # Stop the timer. Happens automatically if this is called
            # via the timer, does not if invoked by force_flush()
            if self.timer:
                self.timer.cancel()
            else:
                self.debug_log((
                    'perform_work - done - timer was destroyed'))
                return

        self.debug_log((
            'perform_work - ready tid={}').format(
                self.tid))

        try:

            not_done = not self.is_shutting_down(
                shutdown_event=self.shutdown_event)

            while not_done:

                try:
                    self.build_payload_from_queued_messages(
                        use_queue=self.queue,
                        shutdown_event=self.shutdown_event)
                except Exception as e:
                    if self.is_shutting_down(
                            shutdown_event=self.shutdown_event):
                        self.debug_log(
                            'perform_work - done - detected shutdown')
                    else:
                        self.debug_log((
                            'perform_work - done - '
                            'Exception shutting down with ex={}').format(
                                e))
                        self.shutdown()
                    self.already_done.set()
                    return
                # end of try to return if the queue

                self.publish_to_splunk()
                timer_interval = self.sleep_interval

                if not_done:
                    if self.is_shutting_down(
                            shutdown_event=self.shutdown_event):
                        self.debug_log(
                            'perform_work - done - shutdown detected')
                        self.already_done.set()
                        return
                    # check if done
                    else:
                        if self.num_sent > 0:
                            # run again if queue was not cleared
                            timer_interval = 0.5
                            self.debug_log(
                                'queue not empty - run again')
                        else:
                            self.debug_log(
                                'sleep={}s'.format(
                                    timer_interval))
                        time.sleep(timer_interval)
                # end of checking if this should run again or is shutting down

            # end of while not done

        except Exception as e:
            if self.is_shutting_down(
                    shutdown_event=self.shutdown_event):
                self.debug_log((
                    'perform_work - shutdown sent={}').format(
                        self.num_sent))
            else:
                self.debug_log((
                    'perform_work - ex={}').format(
                        e))
        # end of try/ex

        self.already_done.set()

        self.debug_log((
            'EXIT - perform_work - done - tid={}').format(
                self.tid))
    # end of perform_work

    def publish_to_splunk(
            self,
            payload=None):
        """publish_to_splunk

        Build the ``self.log_payload`` from the queued log messages
        and POST it to the Splunk endpoint

        :param payload: string message to send to Splunk
        """
        self.debug_log('publish_to_splunk - start')

        use_payload = payload
        if not use_payload:
            use_payload = self.log_payload

        self.num_sent = 0

        if use_payload:
            url = 'https://{}:{}/services/collector'.format(
                self.host,
                self.port)
            self.debug_log('splunk url={}'.format(
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
                    self.num_sent = 1
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
                self.debug_log('payload sent success')
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
        else:
            self.debug_log(
                'no logs to send')

        self.debug_log((
            'publish_to_splunk - done - '
            'self.is_shutting_down={} self.shutdown_now={}').format(
                self.is_shutting_down(shutdown_event=self.shutdown_event),
                self.shutdown_now))
    # end of publish_to_splunk

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
        self.debug_log('force flush - start')
        self.publish_to_splunk()
        self.debug_log('force flush - done')
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

    def close(
            self):
        """close"""
        self.debug_log('close - start')
        self.shutdown()
        logging.Handler.close(self)
        self.debug_log('close - done')
    # end of close

    def shutdown(
            self):
        """shutdown"""
        self.debug_log('shutdown - start')

        # Only initiate shutdown once
        if not self.shutdown_now:
            self.debug_log('shutdown - still shutting down')
            # Cancels the scheduled Timer, allows exit immediately
            if self.timer:
                self.timer.cancel()
                self.timer = None
            return
        else:
            self.debug_log('shutdown - start - setting instance shutdown')
            self.shutdown_now = True
            self.shutdown_event.set()
        # if/else already shutting down

        # Cancels the scheduled Timer, allows exit immediately
        self.timer.cancel()
        self.timer = None

        self.debug_log(
            'shutdown - publishing remaining logs')

        if self.sleep_interval > 0:
            try:
                self.build_payload_from_queued_messages(
                    use_queue=self.queue,
                    shutdown_event=self.shutdown_event,
                    triggered_by_shutdown=True)
            except Exception as e:
                self.write_log((
                    'shutdown - failed to build a payload for remaining '
                    'messages in queue Exception shutting down '
                    'with ex={}').format(
                    e))

            self.debug_log(
                'publishing remaining logs')

            # Send the remaining items in the queue
            self.publish_to_splunk()
        # end of try to publish remaining messages in the queue
        # during shutdown

        self.debug_log('shutdown - done')
    # end of shutdown

# end of SplunkPublisher
