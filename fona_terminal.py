"""
Runs an interactive terminal to
allow for experimentation and
diagnosis with the Fona unit.
"""

from lib import fona, local_debug
from lib.hangar_buddy_logger import HangarBuddyLogger

if __name__ == '__main__':
    import logging

    import serial

    if local_debug.is_debug():
        SERIAL_CONNECTION = None
    else:
        SERIAL_CONNECTION = serial.Serial('/dev/ttyUSB0', 9600)

    FONA = fona.Fona(
        HangarBuddyLogger(logging.getLogger("terminal")),
        SERIAL_CONNECTION,
        fona.DEFAULT_POWER_STATUS_PIN,
        fona.DEFAULT_RING_INDICATOR_PIN)

    if FONA.is_power_on():
        FONA.simple_terminal()
    else:
        print("Power is off..")

    exit()
