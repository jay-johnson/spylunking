"""
This class was built for writing JSON log messages to Splunk over a TCP Port.

Available environment variables:

::

    export SPLUNK_TCP_ADDRESS="<splunk port: 1514>"
    export SPLUNK_INDEX="<splunk index>"
    export SPLUNK_SOURCE="<splunk source>"
    export SPLUNK_SOURCETYPE="<splunk sourcetype>"
    export SPLUNK_DEBUG="<1 enable debug|0 off>"
    export SPLUNK_LOG_TOKEN="<splunk log token>"

"""

import os
import socket
import datetime
from logging.handlers import SocketHandler
from spylunking.rnow import rnow
from spylunking.consts import IS_PY2
from spylunking.consts import SPLUNK_TCP_ADDRESS
from spylunking.consts import SPLUNK_INDEX
from spylunking.consts import SPLUNK_SOURCE
from spylunking.consts import SPLUNK_SOURCETYPE
from spylunking.consts import SPLUNK_DEBUG
from spylunking.consts import SPLUNK_LOG_NAME
from spylunking.consts import SPLUNK_DEPLOY_CONFIG
from spylunking.consts import SPLUNK_ENV_NAME


class TCPSplunkPublisher(SocketHandler, object):
    """
    A logging handler to send logs to a Splunk Enterprise instance
    with a Splunk TCP input set up for json with:

    The TCP Splunk Publisher requires having a JSON-ready entry in
    the ``/opt/splunk/etc/system/default/props.conf`` config file.

    Tokens are not required for this to work, but can be included
    for authenticated TCP logging.

    If you want to send include a token in on the tcp log body,
    then you can export:

    ::

        export SPLUNK_LOG_TOKEN=<Optional Log Token>

    Here are the additional lines added to the splunk
    props.conf for validation:

    ::

        [usejson]
        SHOULD_LINEMERGE = false
        KV_MODE = json
        TIME_FORMAT = %Y-%m-%dT%H:%M:%S.%6N%:z

    """

    def __init__(
            self,
            address=None,
            index=None,
            hostname=None,
            source=None,
            sourcetype='json',
            name=None,
            dc=None,
            env=None,
            custom_dict=None,
            debug=False,
            **kwargs):
        """__init__

        Initialize the TCPSplunkPublisher

        :param address: Splunk fqdn:8088 - overrides host and port
        :param index: Splunk index
        :param hostname: Splunk address <host:port>
        :param source: source for log records
        :param sourcetype: json
        :param name: logger name
        :param dc: deployment config
        :param env: environment name
        :param custom_dict: custom json dictionary to merge on
                            self.formatter.format()
        :param debug: enable debug mode
        """

        self.host = None
        self.port = None

        # self.address is used in the SocketHandler base class
        self.tcp_address = address
        if SPLUNK_TCP_ADDRESS:
            self.tcp_address = SPLUNK_TCP_ADDRESS
        self.host = self.tcp_address.split(':')[0]
        self.port = int(self.tcp_address.split(':')[1])

        super(TCPSplunkPublisher, self).__init__(
            self.host,
            self.port)

        self.token = None
        if not self.token:
            self.token = os.getenv(
                'SPLUNK_LOG_TOKEN',
                None)
        self.index = index
        if self.index is None:
            self.index = SPLUNK_INDEX
        self.source = source
        if self.source is None:
            self.source = SPLUNK_SOURCE
        self.sourcetype = sourcetype
        if self.sourcetype is None:
            self.sourcetype = SPLUNK_SOURCETYPE

        self.custom = custom_dict
        self.debug = SPLUNK_DEBUG or debug

        if hostname is None:
            self.hostname = socket.gethostname()
        else:
            self.hostname = hostname

        self.included_vals = {}
        self.included_vals['index'] = self.index
        if self.source:
            self.included_vals['source'] = self.source
        self.included_vals['sourcetype'] = self.sourcetype
        self.included_vals['hostname'] = self.hostname
        if name:
            self.included_vals['name'] = name
        else:
            self.included_vals['name'] = SPLUNK_LOG_NAME
        if dc:
            self.included_vals['dc'] = dc
        else:
            self.included_vals['dc'] = SPLUNK_DEPLOY_CONFIG
        if env:
            self.included_vals['env'] = env
        else:
            self.included_vals['env'] = SPLUNK_ENV_NAME

        self.debug_log(
            'ready {}:{}'.format(
                self.host,
                self.port))
    # end of __init__

    def write_log(
            self,
            log_message):
        """write_log

        Write logs to stdout

        :param log_message: message to log
        """
        print('{} tcpsp {}'.format(
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
            print('{} tcpsp DEBUG {}'.format(
                rnow(),
                log_message))
    # end of debug_log

    def set_fields(
            self,
            custom_dict):
        """set_fields

        Set the formatter's fields as needed even
        after the logger has been created.

        :param custom_dict: new fields to patch in
        """
        self.custom = custom_dict
    # end of set_fields

    def build_into_splunk_tcp_message(
            self,
            body):
        """build_into_splunk_tcp_message

        Format a message for a Splunk JSON sourcetype

        :param body: splunk JSON dictionary msg body
        """
        # is for an authenticated Splunk TCP Port
        log_msg = None
        if self.token:
            if IS_PY2:
                log_msg = ('token={}, body={}').format(
                    self.token,
                    body)
            else:
                log_msg = ('token={}, body={}').format(
                    self.token,
                    body).encode()
        else:
            if IS_PY2:
                log_msg = ('{}').format(
                    body)
            else:
                log_msg = body.encode()
        # end of support for building different
        # Splunk socket-ready messages

        self.debug_log('build={}'.format(
            log_msg))

        return log_msg
    # end of build_into_splunk_tcp_message

    def makePickle(
            self,
            record):
        """makePickle

        Convert a log record into a JSON dictionary
        packaged into a socket-ready message for a Splunk
        TCP Port configured that is set up with a JSON sourcetype

        :param record: log record to format as a socket-ready message
        """

        use_vals = self.custom
        if not use_vals:
            use_vals = {}
        for i in self.included_vals:
            if i not in use_vals:
                use_vals[i] = self.included_vals[i]

        # for now leave as None
        use_vals['asctime'] = None
        use_vals['systime'] = datetime.datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S.%f')

        self.formatter.set_fields(
            new_fields=use_vals)
        self.debug_log('format={}'.format(
            record))
        log_json_str = self.formatter.format(record)
        self.debug_log('build={}'.format(
            log_json_str))
        splunk_msg = self.build_into_splunk_tcp_message(
            body=log_json_str) + b'\n'
        self.debug_log('send={}'.format(
            splunk_msg))
        return splunk_msg
    # end of makePickle

# end of TCPSplunkPublisher
