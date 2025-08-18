"""Module to control a Relay by SMS"""

import contextlib
import time
from logging import Logger
from multiprocessing import Queue as MPQueue

import lib.text_utils as text_utils
from configuration import Configuration
from devices.relay import PowerRelay



class RelayManager(object):
    """
    Class to command and control the power relay.
    """

    def turn_on(self):
        """
        Tells the relay to turn on the device.
        """

        if not self.is_relay_on():
            self.__message_queue__.put(True)
            return True

        return False

    def turn_off(self):
        """
        Tells the relay to turn off the device.
        """
        if self.is_relay_on():
            self.__message_queue__.put(False)
            return True

        return False

    def is_relay_on(self):
        """
        Get the status of the relay.
        True is "ON"
        False is "OFF"
        """

        return self.__relay__.get_io_pin_status() == 1

    def get_time_remaining(self):
        """
        Returns a string saying how much time is left
        for the relay to be on.
        """

        self.__logger__.debug("get_time_remaining()")

        time_remaining = ""

        if self.__shutoff_timer__ is not None:
            self.__logger__.info("timer is not None")
            delta_time = self.__shutoff_timer__ - time.time()
            self.__logger__.info("Got the delta")
            time_remaining = text_utils.get_time_text(delta_time)
            self.__logger__.info("Got the text")
        else:
            self.__logger__.info("No time")
            time_remaining = "No time"

        self.__logger__.info("adding remaining")
        time_remaining += " left."

        self.__logger__.debug("Done")

        return time_remaining

    def update(self):
        """
        Services the queue from the service thread.
        """

        self.__update_shutoff_timer__()

        # check the queue to deal with various issues,
        # such as the time limit or another system requesting
        # the the relay to be turned on or off.
        while not self.__message_queue__.empty():
            with contextlib.suppress(Exception):
                status_queue = self.__message_queue__.get()

                if True in status_queue:
                    self.__turn_on_immediate__()

                if False in status_queue:
                    self.__turn_off_immediate__()

    def __init__(
        self, configuration: Configuration, logger: Logger, send_message_callback
    ):
        """Initialize the object."""

        self.__configuration__: Configuration = configuration
        self.__logger__: Logger = logger
        self.__send_message_callback__ = send_message_callback

        # create heater relay instance
        self.__relay__ = PowerRelay("heater_relay", configuration.heater_pin)
        self.__message_queue__ = MPQueue()

        # create queue to hold heater timer.
        self.__shutoff_timer__ = None

        # make sure and turn heater off
        self.__relay__.switch_low()

    def __max_time_immediate__(self):
        """
        Trigger everything associated with the timer
        being triggered.
        """
        self.__turn_off_relay__()

    def __turn_off_immediate__(self):
        """
        Turn off the relay RIGHT NOW.
        """

        self.__send_message__("Turning relay OFF.")
        self.__turn_off_relay__()

    def __turn_on_immediate__(self):
        """
        Turn on the relay RIGHT NOW.
        """
        self.__send_message__("Turning relay ON.")
        self.__turn_on_relay__()

    def __send_message__(self, message: str):
        """
        Sends a message using the configured callback.
        """
        if self.__send_message_callback__ is not None:
            self.__send_message_callback__(message)
        else:
            self.__logger__.warning("No send message callback defined.")

    def __turn_off_relay__(self):
        """
        Tells the relay to stop sending power.
        """
        self.__logger__.info("__turn_off_relay__::switch_low()")
        self.__relay__.switch_low()
        self.__logger__.info("__turn_off_relay__::stop_heater_timer()")
        self.__stop_auto_off_timer__()

    def __turn_on_relay__(self):
        """
        Tells the relay to start sending power.
        """
        self.__logger__.info("__turn_on_relay__::switch_high()")
        self.__relay__.switch_high()
        self.__logger__.info("__turn_on_relay__::__start_automatic_shutoff_timer__()")
        self.__start_automatic_shutoff_timer__()

    def __stop_auto_off_timer__(self):
        """
        Stops the auto-off timer.
        """

        self.__logger__.info("Cancelling the heater shutoff timer.")
        self.__shutoff_timer__ = None

    def __start_automatic_shutoff_timer__(self):
        """
        Starts the automatic shutdown timer for the device.
        """
        self.__logger__.info("Starting the auto-off timer.")
        self.__shutoff_timer__ = time.time() + (
            self.__configuration__.max_minutes_to_run * 60
        )

        return True

    def __update_shutoff_timer__(self):
        """
        Check to see if the timer has expired.
        If so, then add it to the action.
        """

        if self.__shutoff_timer__ is not None and self.__shutoff_timer__ < time.time():
            self.__message_queue__.put(False)
        elif self.__shutoff_timer__ is None and self.is_relay_on():
            self.__logger__.warning(
                "The relay should not be on, but the PIN is still active... attempting shutdown."
            )
            self.__message_queue__.put(False)
