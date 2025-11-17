"""
Module to control a Sunfounder 1602 LCD

Based on https://github.com/sunfounder/SunFounder_SensorKit_for_RPi2/blob/master/Python/LCD1602.py
"""

#!/usr/bin/env python

import time

if __name__ == "__main__":
    import os
    import sys

    # Ensure the parent directory is in sys.path so 'managers' can be imported
    # This is only needed if running the unit tests directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import lib.local_debug as local_debug
from displays.display_device import DisplayDevice

if not local_debug.is_debug():
    import smbus

DEFAULT_SMBUS = 1
DEFAULT_1602_ADDRESS = 0x27


class Sf1602Display(DisplayDevice):
    """
    LCD OUTPUT

    Class to abstract a 1602 LCD display
    """

    def __init__(self, sm_bus_id=DEFAULT_SMBUS, adr=DEFAULT_1602_ADDRESS, bl=1):
        """
        Intializer for a SunFounder 1602

        Arguments:
            sm_bus {int} -- Which SMBUS to use
        """

        super().__init__()

        try:
            if not local_debug.is_debug():
                self.__smbus__ = smbus.SMBus(sm_bus_id)

            self.__blen__ = bl
            self.__lcd_addr__ = adr
            self.enable = True

            self.__send_command__(0x33)  # Must initialize to 8-line mode at first
            time.sleep(0.005)
            self.__send_command__(0x32)  # Then initialize to 4-line mode
            time.sleep(0.005)
            self.__send_command__(0x28)  # 2 Lines & 5*7 dots
            time.sleep(0.005)
            self.__send_command__(0x0C)  # Enable display without cursor
            time.sleep(0.005)
            self.__send_command__(0x01)  # Clear Screen

            if not local_debug.is_debug() and self.__smbus__ is not None:
                self.__smbus__.write_byte(self.__lcd_addr__, 0x08)
        except:
            self.enable = False

    def clear(self):
        """
        Clears the screen.
        """

        self.__send_command__(0x01)  # Clear Screen

    def write(self, pos_x, pos_y, text_to_write):
        """
        Writes to the screen.

        Arguments:
            x {int} -- The x position (in characters)
            y {int} -- The y position (in characters)
            text_to_write {string} -- The text to write.
        """

        if not self.enable:
            return

        pos_x = max(pos_x, 0)
        pos_x = min(pos_x, 15)
        pos_y = max(pos_y, 0)
        pos_y = min(pos_y, 1)

        # Move cursor
        addr = 0x80 + 0x40 * pos_y + pos_x
        self.__send_command__(addr)

        for char in text_to_write:
            self.__send_data__(ord(char))

    def __write_word__(self, data):
        """
        Writes a word to the memory in the i2c device

        Arguments:
            data {string} -- The text to write.
        """

        if not self.enable:
            return

        temp = data
        if self.__blen__ == 1:
            temp |= 0x08
        else:
            temp &= 0xF7

        if not local_debug.is_debug() and self.__smbus__ is not None:
            self.__smbus__.write_byte(self.__lcd_addr__, temp)

    def __send_command__(self, comm):
        """
        Sends a command to the I2C device

        Arguments:
            comm {hex} -- The i2c command
        """

        if not self.enable:
            return

        # Send bit7-4 firstly
        buf = comm & 0xF0
        buf |= 0x04  # RS = 0, RW = 0, EN = 1
        self.__write_word__(buf)
        time.sleep(0.002)
        buf &= 0xFB  # Make EN = 0
        self.__write_word__(buf)

        # Send bit3-0 secondly
        buf = (comm & 0x0F) << 4
        buf |= 0x04  # RS = 0, RW = 0, EN = 1
        self.__write_word__(buf)
        time.sleep(0.002)
        buf &= 0xFB  # Make EN = 0
        self.__write_word__(buf)

    def __send_data__(self, data):
        """
        Sends data to the i2c device

        Arguments:
            data {string} -- The data to write.
        """

        if not self.enable:
            return

        # Send bit7-4 firstly
        buf = data & 0xF0
        buf |= 0x05  # RS = 1, RW = 0, EN = 1
        self.__write_word__(buf)
        time.sleep(0.002)
        buf &= 0xFB  # Make EN = 0
        self.__write_word__(buf)

        # Send bit3-0 secondly
        buf = (data & 0x0F) << 4
        buf |= 0x05  # RS = 1, RW = 0, EN = 1
        self.__write_word__(buf)
        time.sleep(0.002)
        buf &= 0xFB  # Make EN = 0
        self.__write_word__(buf)

    def __openlight__(self):  # Enable the backlight
        """
        Turns on the backlight.
        """
        if self.__smbus__ is not None:
            self.__smbus__.write_byte(DEFAULT_1602_ADDRESS, 0x08)
            self.__smbus__.close()


if __name__ == "__main__":
    LCD = Sf1602Display(1, DEFAULT_1602_ADDRESS, 1)  # Slave with background light
    LCD.write(0, 0, "CSQ:9 MARGINAL")
    LCD.write(0, 1, "BAT:98% V:4.12")
