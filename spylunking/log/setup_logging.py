"""
Spylunking
----------

Splunk-ready python logging functions, classes and tools

Please use these environment variables to publish logs and run searches
with a local or remote splunk server:

::

    export SPLUNK_ADDRESS="splunkenterprise:8088"
    export SPLUNK_API_ADDRESS="splunkenterprise:8089"
    export SPLUNK_PASSWORD="123321"
    export SPLUNK_USER="trex"
    export SPLUNK_TOKEN="<Optional pre-existing Splunk token>"

Splunk drill down fields with environment variables:

::

    export LOG_NAME="<application log name>"
    export DEPLOY_CONFIG="<application deployed config like k8 filename>"
    export ENV_NAME="<environment name for this application>"

Splunk optional tuning environment variables:

::

    export SPLUNK_INDEX="<splunk index>"
    export SPLUNK_SOURCE="<splunk source>"
    export SPLUNK_SOURCETYPE="<splunk sourcetype>"
    export SPLUNK_VERIFY="<verify certs on HTTP POST>"
    export SPLUNK_TIMEOUT="<timeout in seconds>"
    export SPLUNK_QUEUE_SIZE="<num msgs allowed in queue - 0=infinite>"
    export SPLUNK_SLEEP_INTERVAL="<sleep in seconds per batch>"
    export SPLUNK_RETRY_COUNT="<attempts per log to retry publishing>"
    export SPLUNK_RETRY_BACKOFF="<cooldown in seconds per failed POST>"
    export SPLUNK_DEBUG="<debug the publisher - 1 enable debug|0 off>"
    export SPLUNK_VERBOSE="<debug the sp command line tool - 1 enable|0 off>"

Change the absolute path to the logging config JSON file:

::

    export SHARED_LOG_CFG=<absolute path to logging config JSON file>

"""

import os
import datetime
import json
import logging.config
import spylunking.get_token as get_token
from pythonjsonlogger import jsonlogger
from spylunking.ppj import ppj
from spylunking.consts import SPLUNK_USER
from spylunking.consts import SPLUNK_PASSWORD
from spylunking.consts import SPLUNK_HOST
from spylunking.consts import SPLUNK_PORT
from spylunking.consts import SPLUNK_TOKEN
from spylunking.consts import SPLUNK_INDEX
from spylunking.consts import SPLUNK_SOURCETYPE
from spylunking.consts import SPLUNK_VERIFY
from spylunking.consts import SPLUNK_ADDRESS
from spylunking.consts import SPLUNK_API_ADDRESS
from spylunking.consts import SPLUNK_TIMEOUT
from spylunking.consts import SPLUNK_SLEEP_INTERVAL
from spylunking.consts import SPLUNK_RETRY_COUNT
from spylunking.consts import SPLUNK_QUEUE_SIZE
from spylunking.consts import SPLUNK_DEBUG
from spylunking.consts import SPLUNK_HANDLER_NAME
from spylunking.consts import SPLUNK_LOG_NAME
from spylunking.consts import SPLUNK_DEPLOY_CONFIG
from spylunking.consts import SPLUNK_ENV_NAME
from spylunking.consts import LOG_HANDLER_NAME


class SplunkFormatter(jsonlogger.JsonFormatter):
    """SplunkFormatter"""

    fields_to_add = {}
    org_fields = {}

    def set_fields(
            self,
            new_fields):
        """set_fields

        Change the fields that will be added in on
        a log

        :param new_fields: new fields to patch in
        """
        self.org_fields = {}
        self.fields_to_add = {}
        for k in new_fields:
            self.org_fields[k] = new_fields[k]
            self.fields_to_add[k] = new_fields[k]
    # end of set_fields

    def get_current_fields(
            self):
        """get_current_fields"""
        return self.fields_to_add
    # end of get_current_fields

    def updated_current_fields(
            self,
            update_fields):
        """updated_current_fields

        :param update_fields: dict with values for
                              updating fields_to_add
        """
        self.fields_to_add = {}
        for k in self.org_fields:
            self.fields_to_add[k] = self.org_fields[k]
        self.fields_to_add.update(update_fields)
    # end of updated_current_fields

    def add_fields(
            self,
            log_record,
            record,
            message_dict):
        """add_fields

        :param log_record: log record
        :param record: log message
        :param message_dict: message dict
        """
        super(
            SplunkFormatter,
            self).add_fields(
                log_record,
                record,
                message_dict)
        if not log_record.get('timestamp'):
            now = datetime.datetime.utcnow().strftime(
                '%Y-%m-%dT%H:%M:%S.%fZ')
            log_record['timestamp'] = now
    # end of add_fields

    def format(
            self,
            record,
            datefmt='%Y:%m:%d %H:%M:%S.%f'):
        """format

        :param record: message object to format
        """

        now = datetime.datetime.now()
        utc_now = datetime.datetime.utcnow()
        asctime = None
        if self.datefmt:
            asctime = now.strftime(
                self.datefmt)
        else:
            asctime = now.strftime(
                datefmt)

        message = {
            'time': record.created,
            'timestamp': utc_now.strftime(
                '%Y-%m-%dT%H:%M:%S.%fZ'),
            'asctime': asctime,
            'path': record.pathname,
            'message': record.getMessage(),
            'exc': None,
            'logger_name': record.name
        }

        if record.exc_info and not message.get('exc'):
            message['exc'] = self.formatException(
                record.exc_info)
        if not message.get(
                'exc') and record.exc_text:
            message['exc'] = record.exc_text

        log_record = {}
        try:
            log_record = OrderedDict()
        except NameError:
            log_record = {}
        # end of try/ex

        message.update(
            self.fields_to_add)
        self.add_fields(
            log_record,
            record,
            message)
        use_log_record = self.process_log_record(
            log_record)
        return '{}{}'.format(
            self.prefix,
            self.jsonify_log_record(
                use_log_record))
    # end of format

# end of SplunkFormatter


def setup_logging(
        default_level=logging.INFO,
        default_path=None,
        env_key='LOG_CFG',
        handler_name='console',
        handlers_dict=None,
        log_dict=None,
        config_name=None,
        splunk_host=None,
        splunk_port=None,
        splunk_index=None,
        splunk_token=None,
        splunk_verify=False,
        splunk_handler_name='splunk',
        splunk_sleep_interval=-1,
        splunk_debug=False):
    """setup_logging

    Setup logging configuration

    :param default_level: level to log
    :param default_path: path to config (optional)
    :param env_key: path to config in this env var
    :param handler_name: handler name in the config
    :param handlers_dict: handlers dict
    :param log_dict: full log dictionary config
    :param config_name: filename for config
    :param splunk_host: optional splunk host
    :param splunk_port: optional splunk port
    :param splunk_index: optional splunk index
    :param splunk_token: optional splunk token
    :param splunk_verify: optional splunk verify - default to False
    :param splunk_handler_name: optional splunk handler name
    :param splunk_sleep_interval: optional splunk sleep interval
    :param splunk_debug: optional splunk debug - default to False

    """

    if SPLUNK_DEBUG:
        splunk_debug = True

    if not splunk_token:
        if SPLUNK_TOKEN:
            splunk_token = splunk_token

    config = None
    if os.getenv(
            'LOG_DICT',
            False):
        try:
            config = json.loads(os.getenv(
                'LOG_DICT',
                None).strip())
        except Exception as e:
            print(
                'Please confirm the env key LOG_DICT has a valid '
                'JSON dictionary. Failed json.loads() parsing with '
                '- using default config for '
                'ex={}').format(
                    e)
        # try to parse the dict and log it that there was a failure

    elif log_dict:
        config = config
    # end of if passed in set in an environment variable

    if not config:
        path = default_path
        file_name = default_path.split('/')[-1]
        if config_name:
            file_name = config_name
        path = '{}/{}'.format(
                    '/'.join(default_path.split('/')[:-1]),
                    file_name)
        value = os.getenv(env_key, None)
        if value:
            path = value
        if os.path.exists(path):
            with open(path, 'rt') as f:
                config = json.load(f)
        else:
            cwd_path = os.getcwd() + '/spylunking/log/{}'.format(
                file_name)
            if os.path.exists(cwd_path):
                with open(cwd_path, 'rt') as f:
                    config = json.load(f)
            else:
                rels_path = os.getcwd() + '/../log/{}'.format(
                    file_name)
                if os.path.exists(rels_path):
                    with open(rels_path, 'rt') as f:
                        config = json.load(f)
                else:
                    repo_config = (
                        '/opt/spylunking/spylunking/log/'
                        'shared-logging.json')
                    if os.path.exists(repo_config):
                        if splunk_debug:
                            print(
                                'checking repo_config={}'.format(
                                    repo_config))
                        with open(repo_config, 'rt') as f:
                            config = json.load(f)
        # end of finding a config dictionary
    # end of trying to find a config on disk

    if config:
        if handlers_dict:
            config['handlers'] = handlers_dict

        found_splunk_handler = False
        if handler_name:
            for hidx, h in enumerate(config['handlers']):
                if splunk_debug:
                    print('handler={} name={}'.format(
                        hidx,
                        h))
                if handler_name == h:
                    config['root']['handlers'].append(h)
                # by default splunk_handler_name == 'splunk'
                if splunk_handler_name == h and splunk_token:
                    found_splunk_handler = True

        if found_splunk_handler:
            if splunk_token:
                config['handlers'][splunk_handler_name]['token'] = \
                    splunk_token
                config['handlers'][splunk_handler_name]['verify'] = \
                    splunk_verify
                if splunk_host:
                    config['handlers'][splunk_handler_name]['host'] = \
                        splunk_host
                if splunk_port:
                    config['handlers'][splunk_handler_name]['port'] = \
                        splunk_port
                if splunk_index:
                    config['handlers'][splunk_handler_name]['index'] = \
                        splunk_index

                config['handlers'][splunk_handler_name]['debug'] = \
                    splunk_debug

                if config['handlers'][splunk_handler_name].get(
                        'queue_size',
                        True):
                    key = 'queue_size'
                    config['handlers'][splunk_handler_name][key] = \
                        SPLUNK_QUEUE_SIZE
                # end of checking for queue_size changes

                if SPLUNK_RETRY_COUNT:
                    key = 'retry_count'
                    config['handlers'][splunk_handler_name][key] = \
                        SPLUNK_RETRY_COUNT
                # end of checking for retry_count changes

                if SPLUNK_TIMEOUT:
                    config['handlers'][splunk_handler_name][key] = \
                        SPLUNK_TIMEOUT
                # end of checking for splunk_timeout changes

                key = 'sleep_interval'
                if splunk_sleep_interval >= 0:
                    config['handlers'][splunk_handler_name][key] = \
                        splunk_sleep_interval
                else:
                    if SPLUNK_SLEEP_INTERVAL:
                        key = 'sleep_interval'
                        config['handlers'][splunk_handler_name][key] = \
                            SPLUNK_SLEEP_INTERVAL

                # end of checking for sleep_interval changes

                if found_splunk_handler:
                    config['root']['handlers'].append(
                        splunk_handler_name)
            else:
                if splunk_debug:
                    print(
                        'Unable to get a valid splunk token '
                        '- splunk disabled')
                config['handlers'].pop('splunk', None)
                good_handlers = []
                for k in config['root']['handlers']:
                    if k != splunk_handler_name:
                        good_handlers.append(k)
                config['root']['handlers'] = good_handlers
        else:
            if splunk_debug:
                print(
                    'splunk disabled')
            config['handlers'].pop(splunk_handler_name, None)
            good_handlers = []
            for k in config['root']['handlers']:
                if k != splunk_handler_name:
                    good_handlers.append(k)
            config['root']['handlers'] = good_handlers

        if len(config['root']['handlers']) == 0:
            print((
                'Failed to find logging root.handlers={} in log '
                'config={}').format(
                    config['root']['handlers'],
                    ppj(config)))
        else:
            if splunk_debug:
                print((
                    'Using log config={}').format(
                        ppj(config)))
        logging.config.dictConfig(
            config)
        return
    else:
        if not splunk_host and not splunk_port:
            if SPLUNK_ADDRESS:
                try:
                    addr_split = SPLUNK_ADDRESS.split(':')
                    if len(addr_split) > 1:
                        splunk_host = addr_split[0]
                        splunk_port = int(addr_split[1])
                except Exception as e:
                    print((
                        'Failed building SPLUNK_ADDRESS={} as'
                        'host:port with ex={}').format(
                            SPLUNK_ADDRESS,
                            e))
        else:
            if not splunk_host:
                if SPLUNK_HOST:
                    splunk_host = SPLUNK_HOST
            if not splunk_port:
                if SPLUNK_PORT:
                    splunk_port = SPLUNK_PORT
        # end of connectivity changes from env vars

        config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'colors': {
                    '()': 'colorlog.ColoredFormatter',
                    'format': (
                        '%(log_color)s%(asctime)s - %(name)s - '
                        '%(levelname)s - %(message)s%(reset)s')
                },
                'no_date_colors': {
                    '()': 'colorlog.ColoredFormatter',
                    'format': (
                        '%(log_color)s%(name)s - %(levelname)s '
                        '- %(message)s%(reset)s')
                },
                'simple': {
                    '()': 'colorlog.ColoredFormatter',
                    'format': (
                        '%(log_color)s'
                        '%(message)s%(reset)s')
                },
                '{}'.format(splunk_handler_name): {
                    '()': 'spylunking.log.setup_logging.SplunkFormatter',
                    'format': (
                        '%(asctime)s - %(name)s - %(levelname)s '
                        '- %(message)s [%(filename)s:%(lineno)s]')
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'colors',
                    'stream': 'ext://sys.stdout'
                },
                'no_date_colors': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'no_date_colors',
                    'stream': 'ext://sys.stdout'
                },
                'simple': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'simple',
                    'stream': 'ext://sys.stdout'
                },
                '{}'.format(splunk_handler_name): {
                    'class': (
                        'spylunking.splunk_publisher.SplunkPublisher'),
                    'host': '{}'.format(
                        splunk_host),
                    'port': '{}'.format(
                        splunk_port),
                    'index': '{}'.format(
                        SPLUNK_INDEX),
                    'token': '{}'.format(
                        SPLUNK_TOKEN),
                    'formatter': '{}'.format(splunk_handler_name),
                    'sourcetype': SPLUNK_SOURCETYPE,
                    'verify': SPLUNK_VERIFY,
                    'timeout': SPLUNK_TIMEOUT,
                    'retry_count': SPLUNK_RETRY_COUNT,
                    'sleep_interval': SPLUNK_SLEEP_INTERVAL,
                    'queue_size': SPLUNK_QUEUE_SIZE,
                    'debug': SPLUNK_DEBUG
                }
            },
            'loggers': {
                '': {
                    'level': 'INFO',
                    'propagate': True
                }
            },
            'root': {
                'level': 'INFO',
                'propagate': True,
                'handlers': [
                    'console'
                ]
            }
        }
        if splunk_token:
            config['root']['handlers'].append(
                '{}'.format(splunk_handler_name))
        logging.config.dictConfig(
            config)
        return
    # end of if valid config dict or not
# end of setup_logging


def build_colorized_logger(
        name='lg',
        config='shared-logging.json',
        log_level=logging.INFO,
        log_config_path=None,
        handler_name='console',
        handlers_dict=None,
        enable_splunk=True,
        splunk_user=None,
        splunk_password=None,
        splunk_address=None,
        splunk_api_address=None,
        splunk_index=None,
        splunk_token=None,
        splunk_handler_name='splunk',
        splunk_sleep_interval=-1,
        splunk_verify=None,
        splunk_debug=False):
    """build_colorized_logger

    Build a colorized logger using function arguments and environment
    variables.

    :param name: name that shows in the logger
    :param config: name of the config file
    :param log_level: level to log
    :param log_config_path: path to log config file
    :param handler_name: handler name in the config
    :param handlers_dict: handlers dict
    :param enable_splunk: Turn off splunk even if the env keys are set
                          True by default - all processes that have the
                          ``SPLUNK_*`` env keys will publish logs to splunk
    :param splunk_user: splunk username - defaults to environment variable:
                        SPLUNK_USER
    :param splunk_password: splunk password - defaults to
                            environment variable:
                            SPLUNK_PASSWORD
    :param splunk_address: splunk address - defaults to environment variable:
                           SPLUNK_ADDRESS which is localhost:8088
    :param splunk_api_address: splunk api address - defaults to
                               environment variable:
                               SPLUNK_API_ADDRESS which is localhost:8089
    :param splunk_index: splunk index - defaults to environment variable:
                         SPLUNK_INDEX
    :param splunk_token: splunk token - defaults to environment variable:
                         SPLUNK_TOKEN
    :param splunk_handler_name: splunk log config handler name - defaults to :
                                SPLUNK_HANDLER_NAME
    :param splunk_handler_name: splunk log config handler name - defaults to :
                                SPLUNK_HANDLER_NAME
    :param splunk_sleep_interval: optional splunk sleep interval
    :param splunk_verify: splunk verify - defaults to environment variable:
                          SPLUNK_VERIFY=<1|0>
    :param splunk_debug: print out the connection attempt for debugging
                         Please Avoid on production...
    """

    use_log_config_path = '{}/{}'.format(
        os.getenv(
            'LOG_CFG',
            os.path.dirname(os.path.realpath(__file__))),
        config)
    use_splunk_user = SPLUNK_USER
    use_splunk_password = SPLUNK_PASSWORD
    use_splunk_address = SPLUNK_ADDRESS
    use_splunk_api_address = SPLUNK_API_ADDRESS
    use_splunk_token = SPLUNK_TOKEN
    use_splunk_index = SPLUNK_INDEX
    use_splunk_verify = SPLUNK_VERIFY
    use_splunk_debug = SPLUNK_DEBUG
    use_splunk_handler_name = SPLUNK_HANDLER_NAME
    use_handler_name = LOG_HANDLER_NAME
    use_handlers_dict = None
    use_splunk_host = None
    use_splunk_port = None
    if log_config_path:
        use_log_config_path = log_config_path
    if handler_name:
        use_handler_name = handler_name
    if handlers_dict:
        use_handlers_dict = handlers_dict
    if splunk_user:
        use_splunk_user = splunk_user
    if splunk_password:
        use_splunk_password = splunk_password
    if splunk_address:
        use_splunk_address = splunk_address
    if splunk_api_address:
        if 'https:' in splunk_api_address:
            use_splunk_api_address = splunk_api_address
        else:
            use_splunk_api_address = 'https://{}'.format(
                splunk_api_address)
    else:
        use_splunk_api_address = 'https://{}'.format(
            use_splunk_api_address)
    if splunk_index:
        use_splunk_index = splunk_index
    if splunk_token:
        use_splunk_token = splunk_token
    if splunk_handler_name:
        use_splunk_handler_name = splunk_handler_name
    if splunk_verify:
        use_splunk_verify = splunk_verify
    if splunk_debug:
        use_splunk_debug = splunk_debug

    override_config = os.getenv(
        'SHARED_LOG_CFG',
        None)
    debug_log_config = bool(os.getenv(
        'DEBUG_SHARED_LOG_CFG',
        '0') == '1')
    use_config = (
        './log/{}').format(
            '{}'.format(
                config))
    if override_config:
        if debug_log_config:
            print((
                'creating logger config env var: '
                'SHARED_LOG_CFG={}'.format(
                    override_config)))
        use_config = override_config
    else:
        if debug_log_config:
            print((
                'Not using shared logging env var: '
                'SHARED_LOG_CFG={}'.format(
                    override_config)))
    # allow a shared log config across all components

    if not os.path.exists(use_config):
        use_config = use_log_config_path
        if not os.path.exists(use_config):
            use_config = ('./spylunking/log/{}').format(
                    config)
            if not os.path.exists(use_config):
                use_config = ('./spylunking/log/{}').format(
                    'shared-logging.json')
    # find the log processing

    try:
        use_splunk_host = use_splunk_address.split(':')[0]
        use_splunk_port = int(use_splunk_address.split(':')[1])
    except Exception as e:
        print((
            'Failed parsing Splunk Address={} '
            'with ex={}').format(
                use_splunk_address,
                e))
        use_splunk_host = None
        use_splunk_port = None
    # end of try/ex to parse splunk address

    if enable_splunk and (
            use_splunk_user
            and use_splunk_password
            and use_splunk_address
            and use_splunk_api_address):
        try:
            if SPLUNK_TOKEN:
                use_splunk_token = SPLUNK_TOKEN
            else:
                use_splunk_token = get_token.get_token(
                    user=use_splunk_user,
                    password=use_splunk_password,
                    url=use_splunk_api_address,
                    verify=use_splunk_verify)
            if use_splunk_debug:
                print((
                    'connected to splunk address={} user={} '
                    'password={} token={}').format(
                        use_splunk_address,
                        use_splunk_user,
                        use_splunk_password,
                        use_splunk_token))
        except Exception as e:
            print((
                'Failed connecting to splunk address={} user={} '
                'ex={}').format(
                    use_splunk_api_address,
                    splunk_user,
                    e))
            use_splunk_token = None
        # end of try/ex on splunk login
    # end of try to set the token to use

    if enable_splunk:
        if use_splunk_token and use_splunk_debug:
            print('Using splunk address={} token={}'.format(
                use_splunk_address,
                use_splunk_token))
    else:
        # turn off external keyword arguments (kwargs):
        use_splunk_host = None
        use_splunk_port = None
        use_splunk_index = None
        use_splunk_token = None

    setup_logging(
        default_level=log_level,
        default_path=use_config,
        handler_name=use_handler_name,
        handlers_dict=use_handlers_dict,
        splunk_host=use_splunk_host,
        splunk_port=use_splunk_port,
        splunk_index=use_splunk_index,
        splunk_token=use_splunk_token,
        splunk_handler_name=use_splunk_handler_name,
        splunk_sleep_interval=splunk_sleep_interval,
        splunk_verify=use_splunk_verify,
        splunk_debug=use_splunk_debug)

    if enable_splunk:
        default_fields = {
            'name': SPLUNK_LOG_NAME,
            'dc': SPLUNK_DEPLOY_CONFIG,
            'env': SPLUNK_ENV_NAME
        }

        last_step = ''
        try:
            last_step = (
                'checking if LOG_FIELDS_DICT '
                'has valid JSON using json.loads({})').format(
                    os.getenv(
                        'LOG_FIELDS_DICT',
                        None))
            if use_splunk_debug:
                print(last_step)
            if os.getenv(
                    'LOG_FIELDS_DICT',
                    None):
                default_fields = json.loads(
                    os.getenv(
                        'LOG_FIELDS_DICT',
                        default_fields))
            last_step = (
                'looking for splunk_handler={}').format(
                    splunk_handler_name)
            if use_splunk_debug:
                print(last_step)
            for i in logging.root.handlers:
                handler_class_name = i.__class__.__name__.lower()
                last_step = (
                    'checking splunk_handler_name={} '
                    'in handler_name={} or '
                    'hasattr({}.formatter, set_fields)').format(
                        handler_class_name,
                        splunk_handler_name,
                        handler_class_name)
                if use_splunk_debug:
                    print(last_step)
                if (splunk_handler_name in handler_class_name
                        or hasattr(i.formatter, 'set_fields')):
                    last_step = (
                        'assigning fields={} to formatter={}').format(
                            default_fields,
                            i.formatter.__class__.__name__)
                    if use_splunk_debug:
                        print(last_step)
                    i.formatter.set_fields(
                        new_fields=default_fields)
        except Exception as e:
            print((
                'Failed assigning splunk_handler_name={} '
                'during last_step={} with ex={}').format(
                    splunk_handler_name,
                    last_step,
                    e))
        # end of try/ex for setting the formatter
    return logging.getLogger(name)
# end of build_colorized_logger


def console_logger(
        name='cl',
        config='shared-logging.json',
        log_level=logging.INFO,
        log_config_path=None,
        handler_name='console',
        handlers_dict=None,
        enable_splunk=False,
        splunk_user=None,
        splunk_password=None,
        splunk_address=None,
        splunk_api_address=None,
        splunk_index=None,
        splunk_token=None,
        splunk_handler_name=None,
        splunk_sleep_interval=-1,
        splunk_verify=None,
        splunk_debug=False):
    """console_logger

    Build the full console logger

    :param name: name that shows in the logger
    :param config: name of the config file
    :param log_level: level to log
    :param log_config_path: path to log config file
    :param handler_name: handler name in the config
    :param handlers_dict: handlers dict
    :param enable_splunk: Turn off splunk even if the env keys are set
                          False by default - all processes that have the
                          ``SPLUNK_*`` env keys will publish logs to splunk
    :param splunk_user: splunk username - defaults to environment variable:
                        SPLUNK_USER
    :param splunk_password: splunk password - defaults to
                            environment variable:
                            SPLUNK_PASSWORD
    :param splunk_address: splunk address - defaults to environment variable:
                           SPLUNK_ADDRESS which is localhost:8088
    :param splunk_api_address: splunk api address - defaults to
                               environment variable:
                               SPLUNK_API_ADDRESS which is localhost:8089
    :param splunk_index: splunk index - defaults to environment variable:
                         SPLUNK_INDEX
    :param splunk_token: splunk token - defaults to environment variable:
                         SPLUNK_TOKEN
    :param splunk_handler_name: splunk log config handler name - defaults to :
                           SPLUNK_HANDLER_NAME
    :param splunk_sleep_interval: optional splunk sleep interval
    :param splunk_verify: splunk verify - defaults to environment variable:
                          SPLUNK_VERIFY=<1|0>
    :param splunk_debug: print out the connection attempt for debugging
                         Please Avoid on production...
    """

    return build_colorized_logger(
        name=name,
        config=config,
        log_level=log_level,
        log_config_path=log_config_path,
        handler_name=handler_name,
        handlers_dict=handlers_dict,
        enable_splunk=enable_splunk,
        splunk_user=splunk_user,
        splunk_password=splunk_password,
        splunk_address=splunk_address,
        splunk_api_address=splunk_api_address,
        splunk_index=splunk_index,
        splunk_token=splunk_token,
        splunk_handler_name=splunk_handler_name,
        splunk_sleep_interval=splunk_sleep_interval,
        splunk_verify=splunk_verify,
        splunk_debug=splunk_debug)
# end of console_logger


def no_date_colors_logger(
        name='nd',
        config='shared-logging.json',
        log_level=logging.INFO,
        log_config_path=None,
        handler_name='no_date_colors',
        handlers_dict=None,
        enable_splunk=False,
        splunk_user=None,
        splunk_password=None,
        splunk_address=None,
        splunk_api_address=None,
        splunk_index=None,
        splunk_token=None,
        splunk_handler_name=None,
        splunk_sleep_interval=-1,
        splunk_verify=None,
        splunk_debug=False):
    """no_date_colors_logger

    Build a colorized logger without dates

    :param name: name that shows in the logger
    :param config: name of the config file
    :param log_level: level to log
    :param log_config_path: path to log config file
    :param handler_name: handler name in the config
    :param handlers_dict: handlers dict
    :param enable_splunk: Turn off splunk even if the env keys are set
                          False by default - all processes that have the
                          ``SPLUNK_*`` env keys will publish logs to splunk
    :param splunk_user: splunk username - defaults to environment variable:
                        SPLUNK_USER
    :param splunk_password: splunk password - defaults to
                            environment variable:
                            SPLUNK_PASSWORD
    :param splunk_address: splunk address - defaults to environment variable:
                           SPLUNK_ADDRESS which is localhost:8088
    :param splunk_api_address: splunk api address - defaults to
                               environment variable:
                               SPLUNK_API_ADDRESS which is localhost:8089
    :param splunk_index: splunk index - defaults to environment variable:
                         SPLUNK_INDEX
    :param splunk_token: splunk token - defaults to environment variable:
                         SPLUNK_TOKEN
    :param splunk_handler_name: splunk log config handler name - defaults to :
                           SPLUNK_HANDLER_NAME
    :param splunk_sleep_interval: optional splunk sleep interval
    :param splunk_verify: splunk verify - defaults to environment variable:
                          SPLUNK_VERIFY=<1|0>
    :param splunk_debug: print out the connection attempt for debugging
                         Please Avoid on production...
    """

    return build_colorized_logger(
        name=name,
        config=config,
        log_level=log_level,
        log_config_path=log_config_path,
        handler_name=handler_name,
        handlers_dict=handlers_dict,
        enable_splunk=enable_splunk,
        splunk_user=splunk_user,
        splunk_password=splunk_password,
        splunk_address=splunk_address,
        splunk_api_address=splunk_api_address,
        splunk_index=splunk_index,
        splunk_token=splunk_token,
        splunk_handler_name=splunk_handler_name,
        splunk_sleep_interval=splunk_sleep_interval,
        splunk_verify=splunk_verify,
        splunk_debug=splunk_debug)
# end of no_date_colors_logger


def simple_logger(
        name='',
        config='shared-logging.json',
        log_level=logging.INFO,
        log_config_path=None,
        handler_name='simple',
        handlers_dict=None,
        enable_splunk=False,
        splunk_user=None,
        splunk_password=None,
        splunk_address=None,
        splunk_api_address=None,
        splunk_index=None,
        splunk_token=None,
        splunk_handler_name=None,
        splunk_sleep_interval=-1,
        splunk_verify=None,
        splunk_debug=False):
    """simple_logger

    Build a colorized logger for just the message - Used by
    command line tools.

    :param name: name that shows in the logger
    :param config: name of the config file
    :param log_level: level to log
    :param log_config_path: path to log config file
    :param handler_name: handler name in the config
    :param handlers_dict: handlers dict
    :param enable_splunk: Turn off splunk even if the env keys are set
                          False by default - all processes that have the
                          ``SPLUNK_*`` env keys will publish logs to splunk
    :param splunk_user: splunk username - defaults to environment variable:
                        SPLUNK_USER
    :param splunk_password: splunk password - defaults to
                            environment variable:
                            SPLUNK_PASSWORD
    :param splunk_address: splunk address - defaults to environment variable:
                           SPLUNK_ADDRESS which is localhost:8088
    :param splunk_api_address: splunk api address - defaults to
                               environment variable:
                               SPLUNK_API_ADDRESS which is localhost:8089
    :param splunk_index: splunk index - defaults to environment variable:
                         SPLUNK_INDEX
    :param splunk_token: splunk token - defaults to environment variable:
                         SPLUNK_TOKEN
    :param splunk_handler_name: splunk log config handler name - defaults to :
                           SPLUNK_HANDLER_NAME
    :param splunk_sleep_interval: optional splunk sleep interval
    :param splunk_verify: splunk verify - defaults to environment variable:
                          SPLUNK_VERIFY=<1|0>
    :param splunk_debug: print out the connection attempt for debugging
                         Please Avoid on production...
    """

    return build_colorized_logger(
        name=name,
        config=config,
        log_level=log_level,
        log_config_path=log_config_path,
        handler_name=handler_name,
        handlers_dict=handlers_dict,
        enable_splunk=enable_splunk,
        splunk_user=splunk_user,
        splunk_password=splunk_password,
        splunk_address=splunk_address,
        splunk_api_address=splunk_api_address,
        splunk_index=splunk_index,
        splunk_token=splunk_token,
        splunk_handler_name=splunk_handler_name,
        splunk_sleep_interval=splunk_sleep_interval,
        splunk_verify=splunk_verify,
        splunk_debug=splunk_debug)
# end of simple_logger


def test_logger(
        name='test',
        config='shared-logging.json',
        log_level=logging.INFO,
        log_config_path=None,
        handler_name='console',
        handlers_dict=None,
        enable_splunk=False,
        splunk_user=None,
        splunk_password=None,
        splunk_address=None,
        splunk_api_address=None,
        splunk_index=None,
        splunk_token=None,
        splunk_handler_name=None,
        splunk_sleep_interval=-1,
        splunk_verify=None,
        splunk_debug=False):
    """test_logger

    Build the test logger

    :param name: name that shows in the logger
    :param config: name of the config file
    :param log_level: level to log
    :param log_config_path: path to log config file
    :param handler_name: handler name in the config
    :param handlers_dict: handlers dict
    :param enable_splunk: Turn off splunk even if the env keys are set
                          False by default - all processes that have the
                          ``SPLUNK_*`` env keys will publish logs to splunk
    :param splunk_user: splunk username - defaults to environment variable:
                        SPLUNK_USER
    :param splunk_password: splunk password - defaults to
                            environment variable:
                            SPLUNK_PASSWORD
    :param splunk_address: splunk address - defaults to environment variable:
                           SPLUNK_ADDRESS which is localhost:8088
    :param splunk_api_address: splunk api address - defaults to
                               environment variable:
                               SPLUNK_API_ADDRESS which is localhost:8089
    :param splunk_index: splunk index - defaults to environment variable:
                         SPLUNK_INDEX
    :param splunk_token: splunk token - defaults to environment variable:
                         SPLUNK_TOKEN
    :param splunk_handler_name: splunk log config handler name - defaults to :
                           SPLUNK_HANDLER_NAME
    :param splunk_sleep_interval: optional splunk sleep interval
    :param splunk_verify: splunk verify - defaults to environment variable:
                          SPLUNK_VERIFY=<1|0>
    :param splunk_debug: print out the connection attempt for debugging
                         Please Avoid on production...
    """

    return build_colorized_logger(
        name=name,
        config=config,
        log_level=log_level,
        log_config_path=log_config_path,
        handler_name=handler_name,
        handlers_dict=handlers_dict,
        enable_splunk=enable_splunk,
        splunk_user=splunk_user,
        splunk_password=splunk_password,
        splunk_address=splunk_address,
        splunk_api_address=splunk_api_address,
        splunk_index=splunk_index,
        splunk_token=splunk_token,
        splunk_handler_name=splunk_handler_name,
        splunk_sleep_interval=splunk_sleep_interval,
        splunk_verify=splunk_verify,
        splunk_debug=splunk_debug)
# end of test_logger
