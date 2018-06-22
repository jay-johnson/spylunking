Spylunking - Splunk + Python Logging
------------------------------------

Splunk Python logging, demonstrations and simple search tools.

This repository is a demo on how to run a local docker splunk container and hook up to the Splunk HEC REST API during the logger's initialization. It supports using previously-shared tokens or logging in using user and password as environment variables.

Here's what your logs can look like in Splunk's web app:

.. image:: https://imgur.com/SUdcyWf.png
    :alt: Splunk web app python logs from the Spylunking test app

.. list-table::
   :header-rows: 1

   * - Travis Build
     - Read the Docs
   * - .. image:: https://travis-ci.org/jay-johnson/spylunking.svg?branch=master
           :alt: Travis Test Status
           :target: https://travis-ci.org/jay-johnson/spylunking
     - .. image:: https://readthedocs.org/projects/spylunking/badge/?version=latest
           :alt: Read the Docs Status
           :target: http://spylunking.readthedocs.io/en/latest/

Getting Started
===============

#.  Clone the repo

    ::

        git clone https://github.com/jay-johnson/spylunking.git spylunking
        cd spylunking

#.  Install the pip 

    ::

        pip install spylunking

    If you want to develop use this command:

    ::

        pip install -e .

#.  Start the Splunk docker container

    ::

       ./run-splunk-in-docker.sh 

Get a Splunk User Token
-----------------------

By default the container creates a user with the credentials:

username: **trex**
password: **123321**

::

    get_splunk_token.py
    955324da-742b-43d4-9746-bcbedf6ae7f4


Please wait a few while the container is getting ready. You may see output like this when the ``splunk`` container is not ready yet or stops running:

::

    get_splunk_token.py 
    Traceback (most recent call last):
    File "<redacted path for doc>", line 171, in _new_conn
        (self._dns_host, self.port), self.timeout, **extra_kw)
    File "<redacted path for doc>", line 79, in create_connection
        raise err
    File "<redacted path for doc>", line 69, in create_connection
        sock.connect(sa)
    ConnectionRefusedError: [Errno 111] Connection refused

Get Splunk Logs from the Command Line Tool
------------------------------------------

Use the command line tool: **spy** to search for recent logs.

::

    spy

Which will log something like:

::

    spy - INFO - creating client user=trex address=localhost:8089 login=localhost:8089 
    spy - INFO - connecting trex@localhost:8089
    spy - INFO - No matches for search={
        "search": "search index=\"antinex\" | head 10"
    }
    spy - INFO - done

Write Splunk Logs
-----------------

By default the container creates an **antinex** index with a user token for the user **trex** to search the index. You can use the included **test_logging.py** script to create some sample logs to verify the splunk logging integration is working.

::

    test_logging.py 
    2018-06-21 16:53:25,507 - testingsplunk - INFO - testing INFO message_id=e5fe48f1-3202-40a8-a6bb-2c483a5730f6
    2018-06-21 16:53:25,507 - testingsplunk - ERROR - testing ERROR message_id=ace412fc-cda5-4a3e-9018-37c0c8e1b952
    2018-06-21 16:53:25,508 - testingsplunk - CRITICAL - testing CRITICAL message_id=085e8800-2c45-468c-bc25-6b49514d52d2
    2018-06-21 16:53:25,508 - testingsplunk - WARNING - testing WARN message_id=4b34d398-382b-467c-932b-ad595ad447b6
    2018-06-21 16:53:25,509 - testingsplunk - ERROR - Testing EXCEPTION with ex=Throw for testing exceptions message_id=b17de717-2c0e-42d6-a54d-98da8299d76f

Get the Test Splunk Logs using the Command Line Tool
----------------------------------------------------

The command line tool called ``spy`` is included with the pip on install. When you run it, it will return the most recent logs from the index (``antinex`` by default) and print them to stdout.

::

    spy - INFO - creating client user=trex address=localhost:8089 login=localhost:8089 
    spy - INFO - connecting trex@localhost:8089
    spy - ERROR - {
        "asctime": "2018-06-21 16:53:25,509",
        "custom_key": "custom value",
        "exc": null,
        "filename": "test_logging.py",
        "levelname": "ERROR",
        "lineno": 34,
        "logger_name": "testingsplunk",
        "message": "Testing EXCEPTION with ex=Throw for testing exceptions message_id=b17de717-2c0e-42d6-a54d-98da8299d76f",
        "name": "testingsplunk",
        "path": "<redacted>/spylunking/scripts/test_logging.py",
        "tags": [],
        "timestamp": 1529625205.5090911
    }
    spy - CRITICAL - {
        "asctime": "2018-06-21 16:53:25,508",
        "custom_key": "custom value",
        "exc": null,
        "filename": "test_logging.py",
        "levelname": "CRITICAL",
        "lineno": 24,
        "logger_name": "testingsplunk",
        "message": "testing CRITICAL message_id=085e8800-2c45-468c-bc25-6b49514d52d2",
        "name": "testingsplunk",
        "path": "<redacted>/spylunking/scripts/test_logging.py",
        "tags": [],
        "timestamp": 1529625205.5082061
    }
    spy - ERROR - {
        "asctime": "2018-06-21 16:53:25,507",
        "custom_key": "custom value",
        "exc": null,
        "filename": "test_logging.py",
        "levelname": "ERROR",
        "lineno": 22,
        "logger_name": "testingsplunk",
        "message": "testing ERROR message_id=ace412fc-cda5-4a3e-9018-37c0c8e1b952",
        "name": "testingsplunk",
        "path": "<redacted>/spylunking/scripts/test_logging.py",
        "tags": [],
        "timestamp": 1529625205.5078382
    }
    spy - INFO - {
        "asctime": "2018-06-21 16:53:25,507",
        "custom_key": "custom value",
        "exc": null,
        "filename": "test_logging.py",
        "levelname": "INFO",
        "lineno": 20,
        "logger_name": "testingsplunk",
        "message": "testing INFO message_id=e5fe48f1-3202-40a8-a6bb-2c483a5730f6",
        "name": "testingsplunk",
        "path": "<redacted>/spylunking/scripts/test_logging.py",
        "tags": [],
        "timestamp": 1529625205.5072436
    }
    spy - INFO - done

Logging to Splunk from a Python Shell
-------------------------------------

Here are python commands to build a colorized, splunk-ready python logger. On startup, the logger will authenticate with splunk using the provided credentials. Once authenticated you can use it like a normal logger.

.. note:: The ``build_colorized_logger`` and ``search`` method also support authentication using a pre-existing ``splunk_token=<token string>`` or by setting a ``SPLUNK_TOKEN`` environment key

::

    python -c '\
        import json;\
        from spylunking.log.setup_logging import build_colorized_logger;\
        import spylunking.search as sp;\
        from spylunking.ppj import ppj;\
        print("build the logger");\
        log = build_colorized_logger(\
            name="spylunking-in-a-shell",\
            splunk_user="trex", \
            splunk_password="123321");\
        print("import the search wrapper");\
        res = sp.search(\
            user="trex",\
            password="123321",\
            address="localhost:8089",\
            query_dict={\
                "search": "search index=\"antinex\" | head 1"\
            });\
        print("pretty print the first record in the result list");\
        log.critical("found search results={}".format(ppj(json.loads(res["record"]["results"][0]["_raw"]))))'

Here is sample output from running this command:

::

    build the logger
    import the search wrapper
    pretty print the first record in the result list
    2018-06-21 22:38:38,475 - spylunking-in-a-shell - CRITICAL - found search results={
        "asctime": "2018-06-21 22:13:36,279",
        "custom_key": "custom value",
        "exc": null,
        "filename": "<stdin>",
        "levelname": "INFO",
        "lineno": 1,
        "logger_name": "spylunking-in-a-shell",
        "message": "testing from a python shell",
        "name": "spylunking-in-a-shell",
        "path": "<stdin>",
        "tags": [],
        "timestamp": 1529644416.2790444
    }

Here it is from a python shell:

::

    python
    Python 3.6.5 (default, Apr  1 2018, 05:46:30) 
    [GCC 7.3.0] on linux
    Type "help", "copyright", "credits" or "license" for more information.
    >>> from spylunking.log.setup_logging import build_colorized_logger
    >>> log = build_colorized_logger(
            name='spylunking-in-a-shell',
            splunk_user='trex',
            splunk_password='123321')
    >>> import spylunking.search as sp
    >>> res = sp.search(
            user='trex',
            password='123321',
            address="localhost:8089",
            query_dict={
                'search': 'search index="antinex" | head 1'
            })
    >>> from spylunking.ppj import ppj
    >>> log.critical('found search results={}'.format(ppj(json.loads(res['record']['results'][0]['_raw']))))
    2018-06-21 22:31:04,231 - spylunking-in-a-shell - CRITICAL - found search results={
        "asctime": "2018-06-21 22:13:36,279",
        "custom_key": "custom value",
        "exc": null,
        "filename": "<stdin>",
        "levelname": "INFO",
        "lineno": 1,
        "logger_name": "spylunking-in-a-shell",
        "message": "testing from a python shell",
        "name": "spylunking-in-a-shell",
        "path": "<stdin>",
        "tags": [],
        "timestamp": 1529644416.2790444
    }

Login to Splunk from a Browser
------------------------------

Open this url in a browser to view the **splunk** container's web application:

http://127.0.0.1:8000

Login with the credentials:

username: **trex**
password: **123321**

Troubleshooting
---------------

Here is a debugging python shell session for showing some common errors you can expect to see as you start to play around with ``spylunking``.

::

    python
    Python 3.6.5 (default, Apr  1 2018, 05:46:30)
    [GCC 7.3.0] on linux
    Type "help", "copyright", "credits" or "license" for more information.
    >>> from spylunking.log.setup_logging import build_colorized_logger
    >>> log = build_colorized_logger(
            name='spylunking-in-a-shell',
            splunk_user='trex',
            splunk_password='123321')
    >>> log.info("testing from a python shell")
    2018-06-21 22:13:36,279 - spylunking-in-a-shell - INFO - testing from a python shell
    >>> import spylunking.search as sp
    >>> res = sp.search(
            user='trex',
            password='123321',
            query_dict={
                    'search': 'index="antinex" | head 1'
            },
            verify=False)
    >>> log.info('job status={}'.format(res['status']))
    2018-06-21 22:16:22,158 - spylunking-in-a-shell - INFO - job status=2
    >>> log.info('job err={}'.format(res['err']))
    2018-06-21 22:16:28,945 - spylunking-in-a-shell - INFO - job err=Failed to get splunk token for user=trex url=https://None ex=HTTPSConnectionPool(host='none', port=443): Max retries exceeded with url: /services/auth/login (Caused by NewConnectionError('<urllib3.connection.VerifiedHTTPSConnection object at 0x7f869c2f2cc0>: Failed to establish a new connection: [Errno -2] Name or service not known',))
    >>> print("now search with the url set")
    now search with the url set
    >>> res = sp.search(
            user='trex',
            password='123321',
            query_dict={
                    'search': 'index="antinex" | head 1'
            },
            address="localhost:8089")
    2018-06-21 22:18:15,380 - spylunking.search - ERROR - Failed searching splunk response=<?xml version="1.0" encoding="UTF-8"?>
    <response>
    <messages>
        <msg type="ERROR">Search Factory: Unknown search command 'index'.</msg>
    </messages>
    </response>
    for query={
        "search": "index=\"antinex\" | head 1"
    } url=https://localhost:8089/services/search/jobs ex=list index out of range
    >>> print("now nest the search correctly")
    now nest the search correctly
    >>> res = sp.search(
            user='trex',
            password='123321',
            address="localhost:8089",
            query_dict={
                    'search': 'search index="antinex" | head 1'
            })
    >>> log.info('job status={}'.format(res['status']))
    2018-06-21 22:20:10,142 - spylunking-in-a-shell - INFO - job status=0
    >>> log.info('job err={}'.format(res['err']))
    2018-06-21 22:20:14,667 - spylunking-in-a-shell - INFO - job err=
    >>> from spylunking.ppj import ppj
    >>> log.critical('found search results={}'.format(ppj(res['record'])))
    2018-06-21 22:21:25,977 - spylunking-in-a-shell - CRITICAL - found search results={
        "fields": [
            {
                "name": "_bkt"
            },
            {
                "name": "_cd"
            },
            {
                "name": "_indextime"
            },
            {
                "name": "_raw"
            },
            {
                "name": "_serial"
            },
            {
                "name": "_si"
            },
            {
                "name": "_sourcetype"
            },
            {
                "name": "_subsecond"
            },
            {
                "name": "_time"
            },
            {
                "name": "host"
            },
            {
                "name": "index"
            },
            {
                "name": "linecount"
            },
            {
                "name": "source"
            },
            {
                "name": "sourcetype"
            },
            {
                "name": "splunk_server"
            }
        ],
        "highlighted": {},
        "init_offset": 0,
        "messages": [],
        "preview": false,
        "results": [
            {
                "_bkt": "antinex~0~791398E7-6A0B-4640-B8D5-5D25E7EF3D02",
                "_cd": "0:3",
                "_indextime": "1529644419",
                "_raw": "{\"asctime\": \"2018-06-21 22:13:36,279\", \"name\": \"spylunking-in-a-shell\", \"levelname\": \"INFO\", \"message\": \"testing from a python shell\", \"filename\": \"<stdin>\", \"lineno\": 1, \"timestamp\": 1529644416.2790444, \"path\": \"<stdin>\", \"custom_key\": \"custom value\", \"tags\": [], \"exc\": null, \"logger_name\": \"spylunking-in-a-shell\"}",
                "_serial": "0",
                "_si": [
                    "splunkenterprise",
                    "antinex"
                ],
                "_sourcetype": "json",
                "_subsecond": ".2792356",
                "_time": "2018-06-22T05:13:36.279+00:00",
                "host": "dev",
                "index": "antinex",
                "linecount": "1",
                "source": "<stdin>",
                "sourcetype": "json",
                "splunk_server": "splunkenterprise"
            }
        ]
    }
    >>> exit()

Please refer to the command line tool's updated usage prompt for help searching for logs:

::

    usage: spy [-h] [-u USER] [-p PASSWORD] [-f DATAFILE] [-i INDEX_NAME]
           [-a ADDRESS] [-e EARLIEST_TIME_MINUTES] [-l LATEST_TIME_MINUTES]
           [-v VERIFY] [-s]

    Search Splunk

    optional arguments:
    -h, --help            show this help message and exit
    -u USER               username
    -p PASSWORD           user password
    -f DATAFILE           splunk-ready request in a json file
    -i INDEX_NAME         index to search
    -a ADDRESS            host address: <fqdn:port>
    -e EARLIEST_TIME_MINUTES
                            earliest_time minutes back
    -l LATEST_TIME_MINUTES
                            latest_time minutes back
    -v VERIFY             verify certs - disabled by default
    -s                    silent

Cleanup
-------

Remove the docker container with the commands:

::

    docker stop splunk
    docker rm splunk


Manual Splunk Commands
======================

Create Token

::

    curl -k -u admin:changeme https://localhost:8089/servicesNS/admin/splunk_httpinput/data/inputs/http -d name=antinex-token 

List Token

::

    curl -k -u admin:changeme https://localhost:8089/servicesNS/admin/splunk_httpinput/data/inputs/http

Using Splunk CLI
================

List Tokens

::

    ./bin/splunk http-event-collector list -uri 'https://localhost:8089' -auth 'admin:changeme'

Add Index

::

    ./bin/splunk add index antinex -auth 'admin:changeme'

Create Token

::

    ./bin/splunk \
        http-event-collector create  \
        antinex-token 'antinex logging token'  \
        -index antinex \
        -uri 'https://localhost:8089' \
        -auth 'admin:changeme'

Cut and Paste Example
---------------------

Here is a cut and paste example for python 3:

::

    import json
    from spylunking.log.setup_logging import build_colorized_logger
    import spylunking.search as sp
    from spylunking.ppj import ppj
    print("build the logger")
    log = build_colorized_logger(
        name="spylunking-in-a-shell",
        splunk_user="trex",
        splunk_password="123321")
    print("import the search wrapper")
    res = sp.search(
        user="trex",
        password="123321",
        address="localhost:8089",
        query_dict={
            "search": "search index=\"antinex\" | head 1"
        })
    print("pretty print the first record in the result list")
    log.critical("found search results={}".format(ppj(json.loads(res["record"]["results"][0]["_raw"]))))'

Development
-----------

Setting up your development environment (right now this demo is using virtualenv):

::

    virtualenv -p python3 ~/.venvs/spylunk && source ~/.venvs/spylunk/bin/activate && pip install -e .

Testing
-------

Run all

::

    py.test

Linting
-------

flake8 .

pycodestyle .

License
-------

Apache 2.0 - Please refer to the LICENSE_ for more details

.. _License: https://github.com/jay-johnson/spylunking/blob/master/LICENSE

