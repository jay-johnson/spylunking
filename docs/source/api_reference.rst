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

::

    from spylunking.log.setup_logging import simple_logger
    log = simple_logger()
    log.info('simple logger example')
    simple logger example

No Date Colorized Logger
------------------------

Build a colorized logger that preserves the parent application name and log level without a date field and does not publish logs to Splunk using:

::

    from spylunking.log.setup_logging import no_date_colors_logger
    log = no_date_colors_logger(name='app-name')
    log.info('no date with colors logger example')
    app-name - INFO - no date with colors logger example


Console Logger
--------------

The console logger is the same as the ``build_colorized_logger`` which can be created with authenticated Splunk-ready logging using:

::

    from spylunking.log.setup_logging import build_colorized_logger
    log = build_colorized_logger(name='using-a-colorized-logger')
    log.info('colorized logger example')
    2018-06-25 16:01:50,118 - using-a-colorized-logger - INFO - colorized logger example

Full Console Logger with Splunk
-------------------------------

To build a logger please use the ``build_colorized_logger`` method. Under the hood, this method will authenticate with Splunk and if it gets a valid token it will enable the ``splunk`` handlers by default and install the token into the logging configuration dictionary before starting up the python logger.

The ``build_colorized_logger`` calls the ``setup_logging`` method that builds the formatters, handlers and the python logging system.

.. automodule:: spylunking.log.setup_logging
   :members: build_colorized_logger,setup_logging,SplunkFormatter,console_logger,no_date_colors_logger,simple_logger

.. toctree::
   :maxdepth: 2

   utilities

