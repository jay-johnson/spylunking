#!/usr/bin/env python

import sys
import json
import socket
import datetime
import time
from spylunking.consts import SPLUNK_TOKEN
from spylunking.consts import SPLUNK_HOSTNAME
from spylunking.consts import SPLUNK_SOURCETYPE
from spylunking.consts import SPLUNK_SOURCE
from spylunking.consts import SPLUNK_INDEX
from spylunking.consts import SPLUNK_LOG_NAME
from spylunking.consts import SPLUNK_DEPLOY_CONFIG
from spylunking.consts import SPLUNK_ENV_NAME
from spylunking.consts import SPLUNK_TCP_ADDRESS


def format_record(
        msg,
        token=None):
    """format_record

    :param token: existing splunk token
    """
    use_token = token
    if not use_token:
        use_token = SPLUNK_TOKEN

    filename = __file__.split('/')[-1]
    log_dict = {
        'message': 'hello-world messages with json fields show up in splunk',
        'name': SPLUNK_LOG_NAME,
        'env': SPLUNK_ENV_NAME,
        'dc': SPLUNK_DEPLOY_CONFIG,
        'index': SPLUNK_INDEX,
        'tags': [
            'pci',
            'ecomm'
        ],
        'hostname': SPLUNK_HOSTNAME,
        'source': SPLUNK_SOURCE,
        'sourcetype': SPLUNK_SOURCETYPE,
        'levelname': 'INFO',
        'logger_name': filename.replace('.py', '').replace('_', '-'),
        'filename': filename,
        'path': __file__,
        'lineno': 123,
        'exc': None,
        'timestamp': time.time(),
        'time': datetime.datetime.utcnow().strftime(
            '%Y-%m-%d %H:%M:%S,%f')
    }

    log_msg = ('{}').format(
        json.dumps(log_dict))
    if use_token:
        log_msg = ('token={}, body={}').format(
            use_token,
            json.dumps(log_dict))
    return log_msg
# end of format_record


def run_main(
        token=None,
        address=None):
    """run_main

    Publish logs to Splunk over a TCP data input with
    the sourcetype set to ``_json``

    :param token: splunk token to use
    :param address: splunk TCP endpoint address <fqdn:port>
    """

    use_token = token
    if not use_token:
        use_token = SPLUNK_TOKEN
    use_address = address
    if not use_address:
        use_address = SPLUNK_TCP_ADDRESS

    address_split = use_address.split(':')
    host = address_split[0]
    port = int(address_split[1])
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    log_msg = format_record(
        msg='hello-world messages with json fields show up in splunk',
        token=token)
    if log_msg:
        is_py2 = sys.version[0] == '2'
        if is_py2:
            print('publishing log={} address={}'.format(
                log_msg,
                use_address))
            s.send(log_msg)
        else:
            print('publishing log={} address={}'.format(
                log_msg.encode(),
                use_address))
            s.send(log_msg.encode())
    else:
        print('failed to build a log msg={}'.format(
            log_msg))
# end of run_main


if __name__ == '__main__':
    run_main()
