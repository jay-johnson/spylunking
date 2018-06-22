"""
Utility - get environment key
"""

import os


def ev(k, v):
    """ev

    Get environment key and strip

    :param k: environment variable key
    :param v: environment variable value
    """
    return os.getenv(
        k,
        v).strip()
# end of ev
