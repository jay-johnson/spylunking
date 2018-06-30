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

Splunk optional tuning environment variables:

::

    export SPLUNK_RETRY_COUNT="<number of attempts to send logs>"
    export SPLUNK_TIMEOUT="<timeout in seconds per attempt>"
    export SPLUNK_QUEUE_SIZE="<integer value or 0 for infinite>"
    export SPLUNK_SLEEP_INTERVAL="<seconds to sleep between publishes>"
    export SPLUNK_DEBUG="<debug the Splunk Publisher by setting to 1>"

"""

import os
import copy
import datetime
import json
import logging.config
import spylunking.get_token as get_token
from spylunking.ppj import ppj
from pythonjsonlogger import jsonlogger


class SplunkFormatter(jsonlogger.JsonFormatter):
    """SplunkFormatter"""

    fields_to_add = {}
    org_fields = {}

    def set_fields(
            self,
            new_fields):
        """set_fields

        :param new_fields: new fields to patch in
        """
        self.org_fields = copy.deepcopy(
            new_fields)
        self.fields_to_add = new_fields
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
        self.fields_to_add = copy.deepcopy(self.org_fields)
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
            record):
        """format

        :param record: message object to format
        """
        message = {
            'timestamp': record.created,
            'path': record.pathname,
            'message': record.getMessage(),
            'exc': None,
            'logger_name': record.name
        }

        if 'asctime' in self._required_fields:
            record.asctime = self.formatTime(
                record,
                self.datefmt)

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
    :param splunk_debug: optional splunk debug - default to False

    """

    if os.getenv(
            'SPLUNK_DEBUG',
            '0') == '1':
        splunk_debug = True

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

                if os.getenv(
                        'SPLUNK_QUEUE_SIZE',
                        None):
                    # assume infinite to safeguard issues
                    queue_size = 0
                    try:
                        queue_size = int(os.getenv(
                            'SPLUNK_QUEUE_SIZE',
                            queue_size))
                    except Exception as e:
                        queue_size = 0
                        print(
                            'Invalid queue_size={} env value'.format(
                                os.getenv(
                                    'SPLUNK_QUEUE_SIZE',
                                    None)))
                    # end of try/ex parsing SPLUNK_QUEUE_SIZE
                    key = 'queue_size'

                    config['handlers'][splunk_handler_name][key] = \
                        queue_size
                # end of checking for queue_size changes

                if os.getenv(
                        'SPLUNK_SLEEP_INTERVAL',
                        None):
                    # assume 1.0 seconds to safeguard issues
                    sleep_interval = 1.0
                    try:
                        sleep_interval = float(os.getenv(
                            'SPLUNK_SLEEP_INTERVAL',
                            sleep_interval))
                    except Exception as e:
                        sleep_interval = 1.0
                        print(
                            'Invalid sleep_interval={} env value'.format(
                                os.getenv(
                                    'SPLUNK_SLEEP_INTERVAL',
                                    None)))
                    # end of try/ex parsing SPLUNK_SLEEP_INTERVAL
                    key = 'sleep_interval'

                    config['handlers'][splunk_handler_name][key] = \
                        sleep_interval
                # end of checking for sleep_interval changes

                if os.getenv(
                        'SPLUNK_RETRY_COUNT',
                        None):
                    # assume 20 to safeguard issues
                    retry_count = 20
                    try:
                        retry_count = int(os.getenv(
                            'SPLUNK_RETRY_COUNT',
                            retry_count))
                    except Exception as e:
                        retry_count = 20
                        print(
                            'Invalid retry_count={} env value'.format(
                                os.getenv(
                                    'SPLUNK_RETRY_COUNT',
                                    None)))
                    # end of try/ex parsing SPLUNK_RETRY_COUNT
                    key = 'retry_count'

                    config['handlers'][splunk_handler_name][key] = \
                        retry_count
                # end of checking for retry_count changes

                if os.getenv(
                        'SPLUNK_TIMEOUT',
                        None):
                    # assume 10 to safeguard issues
                    splunk_timeout = 10
                    try:
                        splunk_timeout = float(os.getenv(
                            'SPLUNK_TIMEOUT',
                            splunk_timeout))
                    except Exception as e:
                        splunk_timeout = 10
                        print(
                            'Invalid splunk_timeout={} env value'.format(
                                os.getenv(
                                    'SPLUNK_TIMEOUT',
                                    None)))
                    # end of try/ex parsing SPLUNK_TIMEOUT
                    key = 'timeout'

                    config['handlers'][splunk_handler_name][key] = \
                        splunk_timeout
                # end of checking for splunk_timeout changes

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
                        splunk_index),
                    'token': '{}'.format(
                        splunk_token),
                    'formatter': '{}'.format(splunk_handler_name),
                    'sourcetype': 'json',
                    'verify': False,
                    'timeout': 10,
                    'retry_count': 60,
                    'sleep_interval': 1.0,
                    'queue_size': 1000000,
                    'debug': False
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
    use_splunk_user = os.getenv(
        'SPLUNK_USER',
        None)
    use_splunk_password = os.getenv(
        'SPLUNK_PASSWORD',
        None)
    use_splunk_address = os.getenv(
        'SPLUNK_ADDRESS',
        'localhost:8088')
    use_splunk_api_address = os.getenv(
        'SPLUNK_API_ADDRESS',
        'localhost:8089')
    use_splunk_token = os.getenv(
        'SPLUNK_TOKEN',
        None)
    use_splunk_index = os.getenv(
        'SPLUNK_INDEX',
        'antinex')
    use_handlers_dict = None
    use_handler_name = os.getenv(
        'LOG_HANDLER_NAME',
        'console')
    use_splunk_handler_name = os.getenv(
        'SPLUNK_HANDLER_NAME',
        'splunk')
    use_splunk_verify = bool(os.getenv(
        'SPLUNK_VERIFY',
        '0').strip() == '1')
    use_splunk_debug = bool(os.getenv(
        'SPLUNK_DEBUG',
        '0').strip() == '1')
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
            if os.getenv(
                    'SPLUNK_TOKEN',
                    False):
                use_splunk_token = os.getenv(
                    'SPLUNK_TOKEN',
                    'not-a-good-token').strip()
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
        splunk_verify=use_splunk_verify,
        splunk_debug=use_splunk_debug)

    if enable_splunk:
        default_fields = {
            'name': os.getenv(
                'LOG_NAME',
                ''),
            'dc': os.getenv(
                'DEPLOY_CONFIG',
                ''),
            'env': os.getenv(
                'ENV_NAME',
                'DEV')
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
        splunk_verify=splunk_verify,
        splunk_debug=splunk_debug)
# end of test_logger
