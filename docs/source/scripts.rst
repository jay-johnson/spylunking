Examples and Scripts
--------------------

Environment Variables
=====================

Please use these environment variables to publish logs and run searches with a local or remote splunk server:

::

    export SPLUNK_ADDRESS="splunkenterprise:8088"
    export SPLUNK_API_ADDRESS="splunkenterprise:8089"
    export SPLUNK_PASSWORD="123321"
    export SPLUNK_USER="trex"
    export SPLUNK_TOKEN="<Optional pre-existing Splunk token>"

Search Splunk with a Dictionary
===============================

The command line client ``sp`` is actually a copy of the ``search_splunk.py`` script. Note, this will likely change in the future, but for now this makes the docs easy to host on RTD.

.. automodule:: spylunking.scripts.search_splunk
   :members: run_main

Publish Logs to Splunk
======================

.. automodule:: spylunking.scripts.test_logging
   :members: run_main

Get a Splunk User Token
=======================

.. automodule:: spylunking.scripts.get_splunk_token
   :members: run_main

Get Splunk Service Token (Session Key)
======================================

.. automodule:: spylunking.scripts.show_service_token
   :members: run_main

