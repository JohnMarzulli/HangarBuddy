"""
Module to control a Sunfounder 1602 LCD

Based on https://github.com/sunfounder/SunFounder_SensorKit_for_RPi2/blob/master/Python/LCD1602.py
"""

#!/usr/bin/env python

if __name__ == "__main__":
    import os
    import sys

    # Ensure the parent directory is in sys.path so 'managers' can be imported
    # This is only needed if running the unit tests directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from displays.display_device import DisplayDevice


class ConsoleDisplay(DisplayDevice):
    """
    Console OUTPUT

    Class to simulate a 1602 LCD display in the console
    """

    def __init__(self):
        super().__init__()

        self.__display__text = ["", ""]

    def clear(self):
        """
        Clears the screen.
        """

        self.__display__text = ["", ""]

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

        if pos_y < 0:
            return
        if pos_y > 1:
            return

        new_text: str = (" " * pos_x) + text_to_write.strip()
        new_text = new_text[:16]

        previous_text: str = self.__display__text[pos_y]

        self.__display__text[pos_y] = new_text

        if previous_text != new_text:
            print("-" * 16)
            print(self.__display__text[0])
            print(self.__display__text[1])
            print("-" * 16)


if __name__ == "__main__":
    CONSOLE = ConsoleDisplay()
    CONSOLE.write(0, 0, "CSQ:9 MARGINAL")
    CONSOLE.write(0, 1, "BAT:98% V:4.12")
