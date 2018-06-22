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

Setup the Logger
================

To build a logger please use the ``build_colorized_logger`` method. Under the hood, this method will authenticate with Splunk and if it gets a valid token it will enable the ``splunk`` handlers by default and install the token into the logging configuration dictionary before starting up the python logger.

The ``build_colorized_logger`` calls the ``setup_logging`` method that builds the formatters, handlers and the python logging system.

.. automodule:: spylunking.log.setup_logging
   :members: build_colorized_logger,setup_logging,SplunkFormatter



.. toctree::
   :maxdepth: 2

   utilities

