Spylunking API Reference
------------------------

Get a Splunk Service Session Key
================================

.. automodule:: spylunking.get_session_key
   :members: get_session_key

Get a Splunk User Token
=======================

.. automodule:: spylunking.get_token
   :members: get_token

Search Splunk
=============

.. automodule:: spylunking.search
   :members: search

Set up a Logger
---------------

There are multiple loggers avaiable depending on the type of logger that is needed.

Simple Logger
-------------

Build a simple, no dates colorized logger that prints just the message in colors and does not publish logs to Splunk using:

.. code-block:: python

    from spylunking.log.setup_logging import simple_logger
    log = simple_logger()
    log.info('simple logger example')
    simple logger example

No Date Colorized Logger
------------------------

Build a colorized logger that preserves the parent application name and log level without a date field and does not publish logs to Splunk using:

.. code-block:: python

    from spylunking.log.setup_logging import no_date_colors_logger
    log = no_date_colors_logger(name='app-name')
    log.info('no date with colors logger example')
    app-name - INFO - no date with colors logger example

Test Logger
-----------

The test logger is for unittests and does not publish to Splunk.

.. code-block:: python

    from spylunking.log.setup_logging import test_logger
    log = test_logger(name='unittest logger')
    log.info('unittest log line')
    2018-06-25 16:01:50,118 - using-a-colorized-logger - INFO - colorized logger example

Console Logger
--------------

The console logger is the same as the ``build_colorized_logger`` which can be created with authenticated Splunk-ready logging using:

.. code-block:: python

    from spylunking.log.setup_logging import build_colorized_logger
    log = build_colorized_logger(name='using-a-colorized-logger')
    log.info('colorized logger example')
    2018-06-25 16:47:54,053 - unittest logger - INFO - unittest log line

Define Custom Fields for Splunk
-------------------------------

You can export a custom JSON dictionary to send as JSON fields for helping drill down on log lines using this environment variable.

::

    export LOG_FIELDS_DICT='{"name":"hello-world","dc":"k8-splunk","env":"development"}'

Or you can export the following environment variables if you just want a couple set in the logs:

::

    export LOG_NAME=<application log name>
    export DEPLOY_CONFIG=<PaaS/CaaS deployment config name>
    export ENV_NAME<deployed environment name>

Log some new test messages to Splunk:

::

    test_logging.py 
    2018-06-25 20:48:51,367 - testingsplunk - INFO - testing INFO message_id=0c5e2a2c-9553-4c8a-8fff-8d77de2be78a
    2018-06-25 20:48:51,368 - testingsplunk - ERROR - testing ERROR message_id=0dc1086d-4fe4-4062-9882-e822f9256d6f
    2018-06-25 20:48:51,368 - testingsplunk - CRITICAL - testing CRITICAL message_id=0c0f56f2-e87f-41a0-babb-b71e2b9d5d5a
    2018-06-25 20:48:51,368 - testingsplunk - WARNING - testing WARN message_id=59b099eb-8c0d-40d0-9d3a-7dfa13fefc90
    2018-06-25 20:48:51,368 - testingsplunk - ERROR - Testing EXCEPTION with ex=Throw for testing exceptions message_id=70fc422d-d33b-4a9e-bb51-ed86aa0a02f9

Once published, you can search for these new logs using those new JSON fields with the ``sp`` search tool. Here is an example of searching for the logs with the application log name ``hello-world``:

::

    sp -q 'index="antinex" AND name=hello-world'
    creating client user=trex address=splunk:8089
    connecting trex@splunk:8089
    2018-06-25 20:48:51,368 testingsplunk - ERROR - Testing EXCEPTION with ex=Throw for testing exceptions message_id=70fc422d-d33b-4a9e-bb51-ed86aa0a02f9 
    2018-06-25 20:48:51,368 testingsplunk - CRITICAL - testing CRITICAL message_id=0c0f56f2-e87f-41a0-babb-b71e2b9d5d5a 
    2018-06-25 20:48:51,368 testingsplunk - ERROR - testing ERROR message_id=0dc1086d-4fe4-4062-9882-e822f9256d6f 
    2018-06-25 20:48:51,367 testingsplunk - INFO - testing INFO message_id=0c5e2a2c-9553-4c8a-8fff-8d77de2be78a 
    done

And you can view log the full JSON dictionaries using the ``-j`` argument on the ``sp`` command:

::

    sp -q 'index="antinex" AND name=hello-world' -j
    creating client user=trex address=splunk:8089
    connecting trex@splunk:8089
    {
        "asctime": "2018-06-25 20:48:51,368",
        "custom_key": "custom value",
        "dc": "k8-deploy",
        "env": "development",
        "exc": null,
        "filename": "test_logging.py",
        "levelname": "ERROR",
        "lineno": 41,
        "logger_name": "testingsplunk",
        "message": "Testing EXCEPTION with ex=Throw for testing exceptions message_id=70fc422d-d33b-4a9e-bb51-ed86aa0a02f9",
        "name": "hello-world",
        "path": "/opt/spylunking/spylunking/scripts/test_logging.py",
        "tags": [],
        "timestamp": 1529984931.3688767
    }
    {
        "asctime": "2018-06-25 20:48:51,368",
        "custom_key": "custom value",
        "dc": "k8-deploy",
        "env": "development",
        "exc": null,
        "filename": "test_logging.py",
        "levelname": "CRITICAL",
        "lineno": 31,
        "logger_name": "testingsplunk",
        "message": "testing CRITICAL message_id=0c0f56f2-e87f-41a0-babb-b71e2b9d5d5a",
        "name": "hello-world",
        "path": "/opt/spylunking/spylunking/scripts/test_logging.py",
        "tags": [],
        "timestamp": 1529984931.3684626
    }
    {
        "asctime": "2018-06-25 20:48:51,368",
        "custom_key": "custom value",
        "dc": "k8-deploy",
        "env": "development",
        "exc": null,
        "filename": "test_logging.py",
        "levelname": "ERROR",
        "lineno": 29,
        "logger_name": "testingsplunk",
        "message": "testing ERROR message_id=0dc1086d-4fe4-4062-9882-e822f9256d6f",
        "name": "hello-world",
        "path": "/opt/spylunking/spylunking/scripts/test_logging.py",
        "tags": [],
        "timestamp": 1529984931.3682773
    }
    {
        "asctime": "2018-06-25 20:48:51,367",
        "custom_key": "custom value",
        "dc": "k8-deploy",
        "env": "development",
        "exc": null,
        "filename": "test_logging.py",
        "levelname": "INFO",
        "lineno": 27,
        "logger_name": "testingsplunk",
        "message": "testing INFO message_id=0c5e2a2c-9553-4c8a-8fff-8d77de2be78a",
        "name": "hello-world",
        "path": "/opt/spylunking/spylunking/scripts/test_logging.py",
        "tags": [],
        "timestamp": 1529984931.3679354
    }
    done

Debug the Logger
----------------

Export this variable before creating a logger.

::

    export SPLUNK_DEBUG=1

Full Console Logger with Splunk
-------------------------------

To build a logger please use the ``build_colorized_logger`` method. Under the hood, this method will authenticate with Splunk and if it gets a valid token it will enable the ``splunk`` handlers by default and install the token into the logging configuration dictionary before starting up the python logger.

The ``build_colorized_logger`` calls the ``setup_logging`` method that builds the formatters, handlers and the python logging system.

.. automodule:: spylunking.log.setup_logging
   :members: build_colorized_logger,setup_logging,SplunkFormatter,console_logger,no_date_colors_logger,simple_logger

.. toctree::
   :maxdepth: 2

   utilities


Splunk Publisher
================

The Splunk Publisher handles sending logs to the configured Splunk server. It was originally inspired from https://github.com/zach-taylor/splunk_handler but after encountering issues within Celery tasks this class was created to maintain a stable logger from inside a Celery task.

.. automodule:: spylunking.log.splunk_publisher
   :members: SplunkPublisher
