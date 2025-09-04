"""
Module to help with mocking/bypassing
RaspberryPi specific code to enable for
debugging on a Mac or Windows host.
"""

import socket
from sys import platform


def is_debug():
    """
    returns True if this should be run as a local debug (Mac or Windows).
    """

    return platform in ["win32", "darwin"]


def get_ip_address() -> str:
    """
    Get the current IP address of this host.

    Returns:
        str: The current IP address.
    """

    hostname = socket.gethostname()

    return socket.gethostbyname(hostname)
