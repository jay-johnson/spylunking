#!/usr/bin/env python

"""
A tool for getting splunk service tokens
"""

import sys
import json
import argparse
import requests
import urllib3
from xml.dom.minidom import parseString
from spylunking.log.setup_logging import build_colorized_logger
from spylunking.utils import ev
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


name = 'get-token'
log = build_colorized_logger(
    name=name)


def run_main():
    """run_main

    Get Splunk Service Token
    """

    parser = argparse.ArgumentParser(
            description=(
                'AntiNex - '
                'Get Token from Splunk'))
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
            '-a',
            help='host address: <fqdn:port>',
            required=False,
            dest='address')
    parser.add_argument(
            '-s',
            help='silent',
            required=False,
            dest='silent',
            action='store_true')
    args = parser.parse_args()

    user = ev(
        'API_USER',
        'user-not-set')
    password = ev(
        'API_PASSWORD',
        'password-not-set')
    address = ev(
        'API_ADDRESS',
        'localhost:8088')
    admin_address = ev(
        'API_ADDRESS',
        'localhost:8089')
    host = ev(
        'API_HOST',
        'localhost')
    port = int(ev(
        'API_PORT',
        '8088'))
    verbose = bool(str(ev(
        'API_VERBOSE',
        'true')).lower() == 'true')
    datafile = None

    if args.user:
        user = args.user
    if args.password:
        password = args.password
    if args.address:
        address = args.address
    if args.datafile:
        datafile = args.datafile
    if args.silent:
        verbose = False

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

    servercontent = requests.post(
        'https://{}/services/auth/login'.format(
            admin_address),
        headers={},
        verify=False,
        data={
            'username': user,
            'password': password
        })
    token = parseString(
        servercontent.text).getElementsByTagName(
            'sessionKey')[0].childNodes[0].nodeValue
    log.info((
        'user={} has token={}').format(
            user,
            token))

    if verbose:
        if req_body:
            log.info('starting with req_body')
        else:
            log.info('starting')

    if verbose:
        log.info('done')

# end of run_main


if __name__ == '__main__':
    run_main()
