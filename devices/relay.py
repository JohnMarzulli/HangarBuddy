"""
Module to handle sending commands to the power relay.
"""

import platform
import time

if __name__ == "__main__":
    import os
    import sys

    # Ensure the parent directory is in sys.path so 'managers' can be imported
    # This is only needed if running the unit tests directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lib.system_level_logging import SystemLevelLogger

IS_DEBUG: bool = platform.system() in ["win32", "Windows", "darwin"]

if not IS_DEBUG:
    import RPi.GPIO as GPIO

DEFAULT_RELAY_TYPE = "always_off"
DEFAULT_PIN = 22


class PowerRelay:
    """
    Class that controls an AC/DC control relay

    Attributes:
    name: Relay name (IE - Heater, Light, etc.
    GPIO_PIN: (BOARD) GPIO PIN on Raspberry Pi that
    the AC/D control relay is plugged into
    """

    def __init__(self, logger: SystemLevelLogger, name, GPIO_PIN, relay_type=DEFAULT_RELAY_TYPE):
        """
        Creates a relay controller.

        Args:
            name (_type_): The name of the relay or what the relay is controlling.
            GPIO_PIN (_type_): The pin (using board numbering) that sends the signal to the relay.
            relay_type (_type_, optional): Ignored. Defaults to DEFAULT_RELAY_TYPE.
        """
        self.name = name
        self.gpio_pin = GPIO_PIN
        self.type = relay_type
        self.expected_status = 0

        self.__logger__: SystemLevelLogger = logger

        # setup GPIO Pins

        if not IS_DEBUG:
            self.__logger__.info(f"Setting {str(GPIO_PIN)} to BOARD/OUT")
            self.expected_status = GPIO.LOW
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(GPIO_PIN, GPIO.OUT)

    def switch_high(self):
        """
        Sets the GPIO pin to HIGH.
        This will cause the controlled device to turn on.
        """

        if IS_DEBUG:
            self.expected_status = 1
            return True

        try:
            print("Setting to OUT/HIGH")
            self.expected_status = GPIO.HIGH
            GPIO.output(self.gpio_pin, GPIO.HIGH)
            time.sleep(3)
        except:
            return False
        return True

    def switch_low(self):
        """
        Sets the GPIO pin to LOW.

        This will cause the device to turn off.
        """

        if IS_DEBUG:
            self.expected_status = 0
            return True

        try:
            self.__logger__.info("Setting to OUT/LOW")
            self.expected_status = GPIO.LOW
            GPIO.output(self.gpio_pin, GPIO.LOW)
            time.sleep(3)
        except:
            return False

        return True

    def get_io_pin_status(self):
        """
        return current status of switch, 0 or 1
        """

        if IS_DEBUG:
            return self.expected_status

        try:
            return GPIO.input(self.gpio_pin)
        except:
            return 0


if __name__ == "__main__":
    import doctest

    from configuration import Configuration

    print("Starting tests.")

    doctest.testmod()

    print("Tests finished")

    TEST_RELAY = PowerRelay(SystemLevelLogger(Configuration(), "RelayTest"), "Heater", DEFAULT_PIN)
    TEST_RELAY.switch_high()
    print(TEST_RELAY.get_io_pin_status())
    time.sleep(10)
    TEST_RELAY.switch_low()
    print(TEST_RELAY.get_io_pin_status())
