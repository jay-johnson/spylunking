

def send_to_splunk(
        session=None,
        url=None,
        data=None,
        headers=None,
        verify=False,
        ssl_options=None,
        timeout=10.0):
    """send_to_splunk

    Send formatted msgs to Splunk. This will throw exceptions
    for any errors. It is decoupled from the publishers to
    make testing easier with mocks.

    :param session: requests.Session
    :param url: url for splunk logs
    :param data: data to send
    :param headers: headers for splunk
    :param verify: verify certs
    :param ssl_options: certs dictionary
    :param timeout: timeout in seconds
    """
    r = session.post(
        url=url,
        data=data,
        headers=headers,
        verify=verify,
        timeout=timeout
    )
    r.raise_for_status()  # Throws exception for 4xx/5xx status
    return r
# end of send_to_splunk
