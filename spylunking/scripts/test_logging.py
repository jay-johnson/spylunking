#!/usr/bin/env python

import uuid
from spylunking.log.setup_logging import build_colorized_logger


log = build_colorized_logger(
    name="testingsplunk",
    splunk_user="trex",
    splunk_password="123321",
    # handler_name="simple",
    # handler_name="not-real",
    # splunk_address="localhost:8088",
    # splunk_token="55df5127-cb0e-4182-932e-c71c454699b8",
    splunk_debug=False)

log.debug("testing DEBUG message_id={}".format(
    str(uuid.uuid4())))
log.info("testing INFO message_id={}".format(
    str(uuid.uuid4())))
log.error("testing ERROR message_id={}".format(
    str(uuid.uuid4())))
log.critical("testing CRITICAL message_id={}".format(
    str(uuid.uuid4())))
log.warn("testing WARN message_id={}".format(
    str(uuid.uuid4())))

try:
    raise Exception("Throw for testing exceptions")
except Exception as e:
    log.error((
        "Testing EXCEPTION with ex={} message_id={}").format(
            e,
            str(uuid.uuid4())))
# end of try/ex
