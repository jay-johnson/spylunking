import datetime


def rnow(
        format='%Y-%m-%d %H:%M:%S',
        in_utc=False):
    """rnow

    Get right now as a string formatted datetime

    :param format: string output format for datetime
    :param in_utc: bool timezone in utc or local time
    """

    if in_utc:
        return datetime.datetime.utcnow().strftime(
            format)
    else:
        return datetime.datetime.now().strftime(
            format)
# end of rnow
