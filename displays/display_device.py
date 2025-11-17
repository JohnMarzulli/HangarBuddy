"""
Module to control a Sunfounder 1602 LCD

Based on https://github.com/sunfounder/SunFounder_SensorKit_for_RPi2/blob/master/Python/LCD1602.py
"""

#!/usr/bin/env python


class DisplayDevice(object):
    """
    Interface for simple display devices like a 1602 LCD.
    """

    def __init__(self):
        self.enable = True

    def clear(self):
        """
        Clears the screen.
        """

        raise NotImplementedError("clear() method not implemented.")

    def write_text(self, text_to_write):
        """
        Writes a string to the LCD.
        """

        if text_to_write is None:
            return False

        if not self.enable:
            return False

        text_array = text_to_write.split("\n")

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

        raise NotImplementedError("clear() method not implemented.")

