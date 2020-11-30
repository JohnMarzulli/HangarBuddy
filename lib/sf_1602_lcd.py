"""
Module to control a Sunfounder 1602 LCD

Based on https://github.com/sunfounder/SunFounder_SensorKit_for_RPi2/blob/master/Python/LCD1602.py
"""

#!/usr/bin/env python

import time
from lib import local_debug

if not local_debug.is_debug():
    import smbus

DEFAULT_SMBUS = 1
DEFAULT_1602_ADDRESS = 0x27

class LcdDisplay(object):
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

        if not local_debug.is_debug():
            self.__smbus__ = smbus.SMBus(sm_bus_id)

        self.__blen__ = bl
        self.__lcd_addr__ = adr
        self.enable = True

        try:
            self.send_command(0x33)  # Must initialize to 8-line mode at first
            time.sleep(0.005)
            self.send_command(0x32)  # Then initialize to 4-line mode
            time.sleep(0.005)
            self.send_command(0x28)  # 2 Lines & 5*7 dots
            time.sleep(0.005)
            self.send_command(0x0C)  # Enable display without cursor
            time.sleep(0.005)
            self.send_command(0x01)  # Clear Screen

            if not local_debug.is_debug() and self.__smbus__ is not None:
                self.__smbus__.write_byte(self.__lcd_addr__, 0x08)
        except:
            self.enable = False

    def write_word(self, data):
        """
        Writes a word to the memory in the i2c device

        Arguments:
            data {string} -- The text to write.
        """

        temp = data
        if self.__blen__ == 1:
            temp |= 0x08
        else:
            temp &= 0xF7

        if not local_debug.is_debug() and self.__smbus__ is not None:
            self.__smbus__.write_byte(self.__lcd_addr__, temp)


    def send_command(self, comm):
        """
        Sends a command to the I2C device

        Arguments:
            comm {hex} -- The i2c command
        """

        # Send bit7-4 firstly
        buf = comm & 0xF0
        buf |= 0x04               # RS = 0, RW = 0, EN = 1
        self.write_word(buf)
        time.sleep(0.002)
        buf &= 0xFB               # Make EN = 0
        self.write_word(buf)

        # Send bit3-0 secondly
        buf = (comm & 0x0F) << 4
        buf |= 0x04               # RS = 0, RW = 0, EN = 1
        self.write_word(buf)
        time.sleep(0.002)
        buf &= 0xFB               # Make EN = 0
        self.write_word(buf)


    def send_data(self, data):
        """
        Sends data to the i2c device

        Arguments:
            data {string} -- The data to write.
        """

        # Send bit7-4 firstly
        buf = data & 0xF0
        buf |= 0x05               # RS = 1, RW = 0, EN = 1
        self.write_word(buf)
        time.sleep(0.002)
        buf &= 0xFB               # Make EN = 0
        self.write_word(buf)

        # Send bit3-0 secondly
        buf = (data & 0x0F) << 4
        buf |= 0x05               # RS = 1, RW = 0, EN = 1
        self.write_word(buf)
        time.sleep(0.002)
        buf &= 0xFB               # Make EN = 0
        self.write_word(buf)

    def clear(self):
        """
        Clears the screen.
        """

        self.send_command(0x01)  # Clear Screen


    def openlight(self):  # Enable the backlight
        """
        Turns on the backlight.
        """
        if self.__smbus__ is not None:
            self.__smbus__.write_byte(DEFAULT_1602_ADDRESS, 0x08)
            self.__smbus__.close()

    def write_text(self, text_to_write):
        """
        Writes a string to the LCD.
        """

        if text_to_write is None:
            return False

        text_array = text_to_write.split('\n')

        array_count = len(text_array)

        if array_count <= 0:
            return False

        if array_count >= 1:
            self.clear()
            self.write(0, 0, text_array[0])

        if array_count >= 2:
            self.write(0, 1, text_array[1])

        return True

    def write(self, pos_x, pos_y, text_to_write):
        """
        Writes to the screen.

        Arguments:
            x {int} -- The x position (in characters)
            y {int} -- The y position (in characters)
            text_to_write {string} -- The text to write.
        """

        if pos_x < 0:
            pos_x = 0
        if pos_x > 15:
            pos_x = 15
        if pos_y < 0:
            pos_y = 0
        if pos_y > 1:
            pos_y = 1

        # Move cursor
        addr = 0x80 + 0x40 * pos_y + pos_x
        self.send_command(addr)

        for char in text_to_write:
            self.send_data(ord(char))


if __name__ == '__main__':
    LCD = LcdDisplay(1, DEFAULT_1602_ADDRESS, 1)  # Slave with background light
    LCD.write(0, 0, 'CSQ:9 MARGINAL')
    LCD.write(0, 1, 'BAT:98% V:4.12')
