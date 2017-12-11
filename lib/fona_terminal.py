"""
Runs an interactive terminal to
allow for experimentation and
diagnosis with the Fona unit.
"""

import fona
import local_debug
from logger import Logger

if __name__ == '__main__':
    import serial
    import logging

    if local_debug.is_debug():
        SERIAL_CONNECTION = None
    else:
        SERIAL_CONNECTION = serial.Serial('/dev/ttyUSB0', 9600)

    FONA = fona.Fona(Logger(logging.getLogger("terminal")),
                     SERIAL_CONNECTION,
                     fona.DEFAULT_POWER_STATUS_PIN,
                     fona.DEFAULT_RING_INDICATOR_PIN)

    if not FONA.is_power_on():
        print "Power is off.."
        exit()

    FONA.simple_terminal()
