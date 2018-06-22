Spylunking
----------

Splunk-ready Python logging, demonstrations and integration tools.

This repository is a demo on how to run a local docker splunk container and hook up to the Splunk HEC REST API during the logger's initialization. It supports using previously-shared tokens or logging in using user and password as environment variables.

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

::

    spy

Which should return output showing the newly published logs:

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

Login to Splunk from a Browser
------------------------------

Open these urls in a browser that is running on the same host as the **splunk** docker container:

http://127.0.0.1:8000

Login with the credentials:

username: **trex**
password: **123321**

Troubleshooting
---------------

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
