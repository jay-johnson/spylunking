#!/usr/bin/env python

"""
A tool for searching splunk with python - spylunking

Examples
--------

Please use these environment variables to publish logs and run searches
with a local or remote splunk server:

::

    export SPLUNK_ADDRESS="splunkenterprise:8088"
    export SPLUNK_API_ADDRESS="splunkenterprise:8089"
    export SPLUNK_PASSWORD="123321"
    export SPLUNK_USER="trex"
    export SPLUNK_TOKEN="<Optional pre-existing Splunk token>"
    export SPLUNK_INDEX="<splunk index>"

Pull Logs with a Query on the Command Line
==========================================

::

    sp -q 'index="antinex" AND levelname=INFO | head 10 | reverse' \
        -u trex -p 123321 -a splunkenterprise:8089

Pull Logs with a Query on the Command Line
==========================================

Get CRITICAL logs
=================

::

    sp -q 'index="antinex" AND levelname="CRITICAL" | reverse'

Get First 10 ERROR logs
=======================

::

    sp -q 'index="antinex" AND levelname="ERROR" | head 10 | reverse' \
        -u trex -p 123321 -a splunkenterprise:8089

"""

import sys
import json
import argparse
import datetime
from spylunking.log.setup_logging import \
    simple_logger
import spylunking.search as sp
from spylunking.ev import ev
from spylunking.ppj import ppj
from spylunking.consts import SUCCESS
from spylunking.consts import SPLUNK_USER
from spylunking.consts import SPLUNK_PASSWORD
from spylunking.consts import SPLUNK_TOKEN
from spylunking.consts import SPLUNK_API_ADDRESS
from spylunking.consts import SPLUNK_INDEX
from spylunking.consts import SPLUNK_VERBOSE


log = simple_logger()

"""
Additional optional argument values for simple_logger
=====================================================

::

    # dates on all logs
    handler_name=None
    # same as None, shows dates on all logs
    handler_name=colors
    # debug authentication issues during
    # functional integration testing
    splunk_debug=True
    splunk_user=os.getenv(
        'SPLUNK_USER',
        None)
    splunk_password=os.getenv(
        'SPLUNK_PASSWORD',
        None)
    splunk_address=os.getenv(
        'SPLUNK_API_ADDRESS',
        'localhost:8089')
    splunk_token=os.getenv(
        'SPLUNK_TOKEN',
        None)
"""


def show_search_results(
        log_rec,
        code_view=True,
        json_view=False,
        show_message_details=False):
    """show_search_results

    Show search results like rsyslog or as pretty-printed
    JSON dictionaries per log for debugging drill-down fields

    :param log_rec: log record from splunk
    :param code_view: show as a normal tail -f <log file> view
    :param json_view: pretty print each log's dictionary
    :param show_message_details
    """

    log_dict = None
    try:
        log_dict = json.loads(
            log_rec)
    except Exception as e:
        log.error((
            'Failed logging record={} with ex={}').format(
                log_rec,
                e))
        return
    # end of try/ex

    if not log_dict:
        log.error((
            'Failed to parse log_rec={} as a dictionary').format(
                log_rec))
        return

    if code_view:
        comp_name = log_dict.get(
            'name',
            '')
        logger_name = log_dict.get(
            'logger_name',
            '')
        use_log_name = (
            '{}').format(
            logger_name)
        if logger_name:
            use_log_name = '{}'.format(
                logger_name)
        else:
            if comp_name:
                use_log_name = '{}'.format(
                    comp_name)

        prefix_log = (
            '{} {} - {} -').format(
                log_dict.get(
                    'systime',
                    log_dict.get(
                        'asctime',
                        '')),
                use_log_name,
                log_dict.get(
                    'levelname',
                    ''))

        suffix_log = ''
        if log_dict.get(
                'exc',
                ''):
            suffix_log = (
                '{} exc={}').format(
                    suffix_log,
                    log_dict.get(
                        'exc',
                        ''))

        if show_message_details:
            suffix_log = (
                'dc={} env={} '
                'source={} line={}').format(
                    log_dict.get(
                        'dc',
                        ''),
                    log_dict.get(
                        'env',
                        ''),
                    log_dict.get(
                        'path',
                        ''),
                    log_dict.get(
                        'lineno',
                        ''))

        msg = (
            '{} {} {}').format(
                prefix_log,
                log_dict.get(
                    'message',
                    ''),
                suffix_log)

        if log_dict['levelname'] == 'INFO':
            log.info((
                '{}').format(
                    msg))
        elif log_dict['levelname'] == 'DEBUG':
            log.debug((
                '{}').format(
                    msg))
        elif log_dict['levelname'] == 'ERROR':
            log.error((
                '{}').format(
                    msg))
        elif log_dict['levelname'] == 'CRITICAL':
            log.critical((
                '{}').format(
                    msg))
        elif log_dict['levelname'] == 'WARNING':
            log.warning((
                '{}').format(
                    msg))
        else:
            log.debug((
                '{}').format(
                    msg))
    elif json_view:
        if log_dict['levelname'] == 'INFO':
            log.info((
                '{}').format(
                    ppj(log_dict)))
        elif log_dict['levelname'] == 'DEBUG':
            log.debug((
                '{}').format(
                    ppj(log_dict)))
        elif log_dict['levelname'] == 'ERROR':
            log.error((
                '{}').format(
                    ppj(log_dict)))
        elif log_dict['levelname'] == 'CRITICAL':
            log.critical((
                '{}').format(
                    ppj(log_dict)))
        elif log_dict['levelname'] == 'WARNING':
            log.warning((
                '{}').format(
                    ppj(log_dict)))
        else:
            log.debug((
                '{}').format(
                    ppj(log_dict)))
    else:
        log.error((
            'Please use either code_view or json_view to view the logs'))
    # end of handling different log view presentation types

# end of show_search_results


def show_non_search_results(
        log_rec,
        code_view=True,
        json_view=False,
        show_message_details=False):
    """show_non_search_results

    Show non-search results for search jobs like:
    ``index="antinex" | stats count``

    :param log_rec: log record from splunk
    :param code_view: show as a normal tail -f <log file> view
    :param json_view: pretty print each log's dictionary
    :param show_message_details
    """

    log_dict = None
    try:
        log_dict = json.loads(
            log_rec)
    except Exception as e:
        log_dict = None
    # end of try/ex

    if not log_dict:
        log.info((
            '{}').format(
                ppj(log_rec)))
    else:
        log.info((
            '{}').format(
                ppj(log_dict)))
# end of show_non_search_results


def run_main():
    """run_main

    Search Splunk
    """

    parser = argparse.ArgumentParser(
        description=(
            'Search Splunk'))
    parser.add_argument(
        '-u',
        help='username',
        required=False,
        dest='user')
    parser.add_argument(
        '-p',
        help='user password',
        required=False,
        dest='password')
    parser.add_argument(
        '-f',
        help='splunk-ready request in a json file',
        required=False,
        dest='datafile')
    parser.add_argument(
        '-i',
        help='index to search',
        required=False,
        dest='index_name')
    parser.add_argument(
        '-a',
        help='host address: <fqdn:port>',
        required=False,
        dest='address')
    parser.add_argument(
        '-e',
        help='(Optional) earliest_time minutes back',
        required=False,
        dest='earliest_time_minutes')
    parser.add_argument(
        '-l',
        help='(Optional) latest_time minutes back',
        required=False,
        dest='latest_time_minutes')
    parser.add_argument(
        '-q',
        '--queryargs',
        nargs='*',
        help=(
            'query string for searching splunk: '
            'search index="antinex" AND levelname="ERROR"'),
        required=False,
        dest='query_args')
    parser.add_argument(
        '-j',
        help='(Optional) view as json dictionary logs',
        required=False,
        dest='json_view',
        action='store_true')
    parser.add_argument(
        '-t',
        help=(
            '(Optional) pre-existing Splunk token '
            'which can be set using export '
            'SPLUNK_TOKEN=<token>  - if provided '
            'the user (-u) and password (-p) '
            'arguments are not required'),
        required=False,
        dest='token')
    parser.add_argument(
        '-m',
        help='(Optional) verbose message when getting logs',
        required=False,
        dest='message_details',
        action='store_true')
    parser.add_argument(
        '-v',
        help='(Optional) verify certs - disabled by default',
        required=False,
        dest='verify',
        action='store_true')
    parser.add_argument(
        '-b',
        help='verbose',
        required=False,
        dest='verbose',
        action='store_true')
    args = parser.parse_args()

    user = SPLUNK_USER
    password = SPLUNK_PASSWORD
    token = SPLUNK_TOKEN
    address = SPLUNK_API_ADDRESS
    index_name = SPLUNK_INDEX
    verbose = SPLUNK_VERBOSE
    show_message_details = bool(str(ev(
        'MESSAGE_DETAILS',
        '0')).lower() == '1')
    earliest_time_minutes = None
    latest_time_minutes = None
    verify = False
    code_view = True
    json_view = False
    datafile = None

    if args.user:
        user = args.user
    if args.password:
        password = args.password
    if args.address:
        address = args.address
    if args.datafile:
        datafile = args.datafile
    if args.index_name:
        index_name = args.index_name
    if args.verify:
        verify = args.verify
    if args.earliest_time_minutes:
        earliest_time_minutes = int(args.earliest_time_minutes)
    if args.latest_time_minutes:
        latest_time_minutes = int(args.latest_time_minutes)
    if args.verbose:
        verbose = True
    if args.message_details:
        show_message_details = args.message_details
    if args.token:
        token = args.token
    if args.json_view:
        json_view = True
        code_view = False

    default_search_query = 'index="{}" | head 10 | reverse'.format(
        index_name)
    search_query = ev(
        'SPLUNK_QUERY',
        default_search_query)
    if args.query_args:
        search_query = ' '.join(
            args.query_args)

    valid = True
    if not user or user == 'user-not-set':
        log.critical('missing user')
        valid = False
    if not password or password == 'password-not-set':
        log.critical('missing password')
        valid = False
    if not index_name:
        log.critical('missing splunk index')
        valid = False
    if token:
        # if the token is present,
        # then the user and the password are not required
        if not valid and index_name:
            valid = True
    if not valid:
        log.critical(
            'Please run with the following arguments:\n')
        log.error(
            '-u <username> -p <password> '
            '-i <index> -t <token if user and password not set> '
            '-a <host address as: fqdn:port>')
        log.critical(
            '\n'
            'Or you can export the following '
            'environment variables and retry the command: '
            '\n')
        log.error(
            'export SPLUNK_ADDRESS="splunkenterprise:8088"\n'
            'export SPLUNK_API_ADDRESS="splunkenterprise:8089"\n'
            'export SPLUNK_PASSWORD="123321"\n'
            'export SPLUNK_USER="trex"\n'
            'export SPLUNK_INDEX="antinex"\n'
            'export SPLUNK_TOKEN="<Optional pre-existing Splunk token>"\n')
        sys.exit(1)

    if verbose:
        log.info((
            'creating client user={} address={}').format(
                user,
                address))

    last_msg = ''
    host = ''
    port = -1
    try:
        last_msg = (
            'Invalid address={}').format(
                address)
        address_split = address.split(':')
        last_msg = (
            'Failed finding host in address={} '
            '- please use: -a <fqdn:port>').format(
                address)
        host = address_split[0]
        last_msg = (
            'Failed finding integer port in address={} '
            '- please use: -a <fqdn:port>').format(
                address)
        port = int(address_split[1])
    except Exception as e:
        log.error((
            'Failed to parse -a {} for the '
            'splunk host address: {} which threw an '
            'ex={}').format(
                address,
                last_msg,
                e))
        sys.exit(1)
    # end of try ex

    if verbose:
        log.info((
            'connecting {}@{}:{}').format(
                user,
                host,
                port))

    req_body = None
    if datafile:
        if verbose:
            log.info((
                'loading request in datafile={}').format(
                    datafile))

        with open(datafile, 'r') as f:
            req_body = json.loads(f.read())

    earliest_time = None
    latest_time = None
    now = datetime.datetime.now()
    if earliest_time_minutes:
        min_15_ago = now - datetime.timedelta(
            minutes=earliest_time_minutes)
        earliest_time = min_15_ago.strftime(
            '%Y-%m-%dT%H:%M:%S.000-00:00')
    if latest_time_minutes:
        latest_time = (now - datetime.timedelta(
            minutes=latest_time_minutes)).strftime(
                '%Y-%m-%dT%H:%M:%S.000-00:00')

    # Step 2: Create a search job
    if not search_query.startswith('search'):
        search_query = 'search {}'.format(
            search_query)

    search_data = req_body
    if not search_data:
        search_data = {
            'search': search_query
        }
        if earliest_time:
            search_data['earliest_time'] = earliest_time
        if latest_time:
            search_data['latest_time'] = latest_time

    res = sp.search(
        user=user,
        password=password,
        address=address,
        token=token,
        query_dict=search_data,
        verify=verify)

    if res['status'] == SUCCESS:
        result_list = []
        try:
            result_list = res['record'].get(
                'results',
                result_list)
            if len(result_list) == 0:
                log.info((
                    'No matches for search={} '
                    'response={}').format(
                        ppj(search_data),
                        ppj(res['record'])))
        except Exception as e:
            result_list = []
            log.error((
                'Failed to find results for the query={} '
                'with ex={}').format(
                    ppj(search_data),
                    e))

        for ridx, log_record in enumerate(result_list):
            log_raw = log_record.get(
                '_raw',
                None)
            if log_raw:
                show_search_results(
                    log_rec=log_raw,
                    code_view=code_view,
                    json_view=json_view,
                    show_message_details=show_message_details)
            else:
                show_non_search_results(
                    log_rec=log_record,
                    code_view=code_view,
                    json_view=json_view,
                    show_message_details=show_message_details)
            # end of handling log record presentation as a view
        # end for all log records
    else:
        log.error((
            'Failed searching splunk with status={} and '
            'error: {}').format(
                res['status'],
                res['err']))
    # end of if job_id

    if verbose:
        log.info('done')

# end of run_main


if __name__ == '__main__':
    run_main()
