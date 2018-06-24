#!/usr/bin/env python

"""
A tool for searching splunk with python - spylunking

Examples
--------

Pull Logs with a Query on the Command Line
==========================================

::

    sp -q 'index="antinex" AND levelname=INFO | head 10' \
        -u trex -p 123321 -a splunkenterprise:8089

Pull Logs with a Query on the Command Line
==========================================

Get CRITICAL logs
=================

::

    sp -q 'index="antinex" AND levelname="CRITICAL"'

Get First 10 ERROR logs
=======================

::

    sp -q 'index="antinex" AND levelname="ERROR" | head 10' \
        -u trex -p 123321 -a splunkenterprise:8089

"""

import sys
import json
import argparse
import datetime
from spylunking.log.setup_logging import \
    build_colorized_logger
import spylunking.search as sp
from spylunking.ev import ev
from spylunking.consts import SUCCESS
from spylunking.ppj import ppj


log = build_colorized_logger(
    name='search_splunk',
    handler_name='simple',
    enable_splunk=False)

"""
Additional optional argument values for build_colorized_logger
==============================================================

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
        help='earliest_time minutes back',
        required=False,
        dest='earliest_time_minutes')
    parser.add_argument(
        '-l',
        help='latest_time minutes back',
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
        help='view as json dictionary logs',
        required=False,
        dest='json_view',
        action='store_true')
    parser.add_argument(
        '-v',
        help='verify certs - disabled by default',
        required=False,
        dest='verify',
        action='store_true')
    parser.add_argument(
        '-s',
        help='silent',
        required=False,
        dest='silent',
        action='store_true')
    args = parser.parse_args()

    user = ev(
        'SPLUNK_USER',
        'user-not-set')
    password = ev(
        'SPLUNK_PASSWORD',
        'password-not-set')
    address = ev(
        'SPLUNK_API_ADDRESS',
        'localhost:8089')
    index_name = ev(
        'SPLUNK_INDEX',
        'antinex')
    verbose = bool(str(ev(
        'SPLUNK_VERBOSE',
        'true')).lower() == 'true')
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
    if args.silent:
        verbose = False
    if args.json_view:
        json_view = True
        code_view = False

    default_search_query = 'index="{}" | head 10'.format(
        index_name)
    search_query = ev(
        'SPLUNK_QUERY',
        default_search_query)
    if args.query_args:
        search_query = ' '.join(
            args.query_args)

    usage = ('Please run with -u <username> '
             '-p <password> '
             '-a <host address as: fqdn:port> ')

    valid = True
    if not user or user == 'user-not-set':
        log.error('missing user')
        valid = False
    if not password or password == 'password-not-set':
        log.error('missing password')
        valid = False
    if not valid:
        log.error(usage)
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
            org_rec = json.loads(log_record['_raw'])
            if code_view:
                rec = org_rec
                comp_name = rec.get(
                    'name',
                    '')
                logger_name = rec.get(
                    'logger_name',
                    '')
                use_log_name = (
                    '{}').format(
                    logger_name)
                if comp_name and logger_name:
                    use_log_name = '{}.{}'.format(
                        comp_name,
                        logger_name)
                elif comp_name:
                    use_log_name = '{}'.format(
                        comp_name)

                prefix_log = (
                    '{} {} -').format(
                        use_log_name,
                        rec.get(
                            'asctime',
                            ''))
                suffix_log = (
                    'dc={} env={} '
                    'source={} line={} ex={}').format(
                        rec.get(
                            'dc',
                            ''),
                        rec.get(
                            'env',
                            ''),
                        rec.get(
                            'path',
                            ''),
                        rec.get(
                            'lineno',
                            ''),
                        rec.get(
                            'exc',
                            ''))
                msg = (
                    '{} {} {}').format(
                        prefix_log,
                        rec.get(
                            'message',
                            ''),
                        suffix_log)

                if rec['levelname'] == 'INFO':
                    log.info((
                        '{}').format(
                            msg))
                elif rec['levelname'] == 'DEBUG':
                    log.debug((
                        '{}').format(
                            msg))
                elif rec['levelname'] == 'ERROR':
                    log.error((
                        '{}').format(
                            msg))
                elif rec['levelname'] == 'CRITICAL':
                    log.critical((
                        '{}').format(
                            msg))
                elif rec['levelname'] == 'WARN':
                    log.warn((
                        '{}').format(
                            msg))
                else:
                    log.debug((
                        '{}').format(
                            msg))
            elif json_view:
                rec = org_rec
                if rec['levelname'] == 'INFO':
                    log.info((
                        '{}').format(
                            ppj(rec)))
                elif rec['levelname'] == 'DEBUG':
                    log.debug((
                        '{}').format(
                            ppj(rec)))
                elif rec['levelname'] == 'ERROR':
                    log.error((
                        '{}').format(
                            ppj(rec)))
                elif rec['levelname'] == 'CRITICAL':
                    log.critical((
                        '{}').format(
                            ppj(rec)))
                elif rec['levelname'] == 'WARN':
                    log.warn((
                        '{}').format(
                            ppj(rec)))
                else:
                    log.debug((
                        '{}').format(
                            ppj(rec)))
        # end of finding responses

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
