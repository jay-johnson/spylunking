"""
Spylunking
----------

Splunk-ready python logging functions, classes and tools

Author: Jay Johnson (https://github.com/jay-johnson)
License: Apache 2.0

"""

import os
import copy
import datetime
import json
import logging.config
import spylunking.get_token as get_token
from spylunking.utils import ppj
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
            'custom_key': 'custom value',
            'tags': [
            ],
            'exc': None,
            'logger_name': record.name
        }

        if 'asctime' in self._required_fields:
            record.asctime = self.formatTime(
                record,
                self.datefmt)

        if record.exc_info and not message.get('exc_info'):
            message['exc'] = self.formatException(
                record.exc_info)
        if not message.get(
                'exc_info') and record.exc_text:
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
    config = None
    if os.getenv(
            'LOG_DICT',
            False):
        config = json.loads(os.getenv(
            'LOG_DICT',
            None).strip())
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

        if os.getenv(
                'SPLUNK_ENABLED',
                '1').strip() == '1' and found_splunk_handler:
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
                'no_dates_colors': {
                    '()': 'colorlog.ColoredFormatter',
                    'format': (
                        '%(log_color)s%(name)s - %(levelname)s '
                        '- %(message)s%(reset)s')
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
                'simple': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'no_dates_colors',
                    'stream': 'ext://sys.stdout'
                },
                '{}'.format(splunk_handler_name): {
                    'class': 'splunk_handler.SplunkHandler',
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
                    'flush_interval': 5,
                    'retry_count': 5,
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
        if os.getenv(
                'SPLUNK_ENABLED',
                '1').strip() == '1' and splunk_token:
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
        splunk_user=None,
        splunk_password=None,
        splunk_address=None,
        splunk_login_address=None,
        splunk_index=None,
        splunk_token=None,
        splunk_handler_name='splunk',
        splunk_verify=None,
        splunk_debug=False):
    """build_colorized_logger

    :param name: name that shows in the logger
    :param config: name of the config file
    :param log_level: level to log
    :param log_config_path: path to log config file
    :param handler_name: handler name in the config
    :param handlers_dict: handlers dict
    :param splunk_user: splunk username - defaults to environment variable:
                        SPLUNK_USER
    :param splunk_password: splunk password - defaults to
                            environment variable:
                            SPLUNK_PASSWORD
    :param splunk_address: splunk address - defaults to environment variable:
                           SPLUNK_ADDRESS
    :param splunk_login_address: splunk login address - defaults to
                                 environment variable:
                                 SPLUNK_LOGIN_ADDRESS
    :param splunk_index: splunk index - defaults to environment variable:
                         SPLUNK_INDEX
    :param splunk_token: splunk token - defaults to environment variable:
                         SPLUNK_TOKEN
    :param splunk_hanlder: splunk log config handler name - defaults to :
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
    use_splunk_index = os.getenv(
        'SPLUNK_INDEX',
        'antinex')
    use_splunk_hec_address = os.getenv(
        'SPLUNK_LOGIN_ADDRESS',
        'https://localhost:8089')
    use_splunk_token = os.getenv(
        'SPLUNK_TOKEN',
        None)
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
    if splunk_login_address:
        use_splunk_hec_address = 'https://{}'.format(
            splunk_login_address)
    if splunk_index:
        use_splunk_index = splunk_index
    if splunk_token:
        use_splunk_token = splunk_token
    if splunk_handler_name:
        use_splunk_handler_name = splunk_handler_name
    if splunk_verify:
        use_splunk_verify = splunk_verify

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
                    'logging.json')
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

    if use_splunk_user and use_splunk_password and use_splunk_address:
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
                    url=use_splunk_hec_address,
                    verify=use_splunk_verify)
            if splunk_debug:
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
                    use_splunk_hec_address,
                    splunk_user,
                    e))
            use_splunk_token = None
        # end of try/ex on splunk login
    # end of try to set the token to use

    if use_splunk_token and splunk_debug:
        print('Using splunk address={} token={}'.format(
            use_splunk_address,
            use_splunk_token))

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
        splunk_debug=splunk_debug)

    if os.getenv(
            'SPLUNK_ENABLED',
            '1').strip() == '1':

        default_fields = {
            'name': os.getenv(
                'COMPONENT_NAME',
                ''),
            'dc': os.getenv(
                'DEPLOYED_DC',
                ''),
            'env': os.getenv(
                'ENV_NAME',
                'DEV')
        }

        for i in logging.root.handlers:
            if splunk_handler_name in logging.root.handlers:
                i.set_fields(
                    fields_to_add=default_fields)

    return logging.getLogger(name)
# end of build_colorized_logger
