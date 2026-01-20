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

    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        if ip_address.startswith("127."):
            # Try to get the first non-loopback IPv4 address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                # Doesn't need to be reachable
                s.connect(("8.8.8.8", 80))
                ip_address = s.getsockname()[0]
            finally:
                s.close()
        return ip_address
    except Exception:
        return "127.0.0.1"
