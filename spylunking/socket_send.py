from spylunking.consts import IS_PY2


def socket_send(
        sock,
        msg,
        debug=False):
    """socket_send

    Send the ``msg`` over the connected socket ``sock``.
    This will throw for any errors.

    :param sock: connected socket
    :param msg: message as a string
    :param debug: debug bool
    """
    if IS_PY2:
        sock.send(msg)
    else:
        sock.send(msg.encode())
# end of socket_send
