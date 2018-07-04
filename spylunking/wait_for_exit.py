import os
import time
from spylunking.consts import SPLUNK_DEBUG


def wait_for_exit(
        log,
        debug=False):
    """wait_for_exit

    Sleep to allow the thread to pick up final messages
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

    :param log: created logger
    :param debug: bool to debug with prints
    """

    debug = SPLUNK_DEBUG
    for i in log.root.handlers:
        handler_class_name = i.__class__.__name__.lower()
        if debug:
            print((
                ' - wait_for_exit handler={}').format(
                    handler_class_name))
        if ('splunkpublisher' == handler_class_name
                or 'mpsplunkpublisher' == handler_class_name):
            if hasattr(i, 'sleep_interval'):
                total_sleep = i.sleep_interval + 2.0
                if os.getenv(
                        'PUBLISHER_EXIT_DELAY',
                        False):
                    total_sleep = float(os.getenv(
                        'PUBLISHER_EXIT_DELAY',
                        total_sleep))
                if debug:
                    print((
                        ' - wait_for_exit '
                        'handler={} wait={}s').format(
                            handler_class_name,
                            total_sleep))
                time.sleep(total_sleep)
                if debug:
                    print((
                        'done waiting for exit'))
                return
            else:
                print((
                    ' - wait_for_exit handler={} has no'
                    'sleep_interval').format(
                        handler_class_name))
            # if has a sleep_interval member variable
        # if one of the loggers requiring an exit sleep
    # end of finding logger handlers
# end of wait_for_exit
