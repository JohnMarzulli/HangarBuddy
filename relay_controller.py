""" Module to control a Relay by SMS """

# encoding: UTF-8

import time
from multiprocessing import Queue as MPQueue

import lib.utilities as utilities
import text
from lib.relay import PowerRelay


class RelayManager(object):
    """
    Class to command and control the power relay.
    """

    def turn_on(self):
        """
        Tells the heater to turn on.
        """

        if not self.is_relay_on():
            self.__heater_queue__.put(text.HEATER_ON_COMMAND)
            return True

        return False

    def turn_off(self):
        """
        Tells the heater to turn off.
        """
        if self.is_relay_on():
            self.__heater_queue__.put(text.HEATER_OFF_COMMAND)
            return True

        return False

    def is_relay_on(self):
        """
        Get the status of the relay.
        True is "ON"
        False is "OFF"
        """

        return self.__heater_relay__.get_io_pin_status() == 1

    def get_heater_time_remaining(self):
        """
        Returns a string saying how much time is left
        for the heater.
        """

        self.__logger__.log_info_message("get_heater_time_remaining()")

        time_remaining = ""

        if self.__heater_shutoff_timer__ is not None:
            self.__logger__.log_info_message("timer is not None")
            delta_time = self.__heater_shutoff_timer__ - time.time()
            self.__logger__.log_info_message("Got the delta")
            time_remaining = utilities.get_time_text(delta_time)
            self.__logger__.log_info_message("Got the text")
        else:
            self.__logger__.log_info_message("No time")
            time_remaining = "No time"

        self.__logger__.log_info_message("adding remaining")
        time_remaining += " left."

        self.__logger__.log_info_message("Done")

        return time_remaining

    def update(self):
        """
        Services the queue from the heater service thread.
        """

        self.__update_shutoff_timer__()

        # check the queue to deal with various issues,
        # such as Max heater time and the gas sensor being tripped
        while not self.__heater_queue__.empty():
            try:
                status_queue = self.__heater_queue__.get()

                if text.HEATER_ON_COMMAND in status_queue:
                    self.__start_heater_immediate__()

                if text.HEATER_OFF_COMMAND in status_queue:
                    self.__stop_heater_immediate__()

                if text.MAX_TIME in status_queue:
                    self.__max_time_immediate__()
            except Queue.Empty:
                pass

    def __init__(self,
                 configuration,
                 logger,
                 heater_on_callback,
                 heater_off_callback,
                 heater_max_time_callback):
        """ Initialize the object. """

        self.__configuration__ = configuration
        self.__logger__ = logger
        self.__on_callback__ = heater_on_callback
        self.__off_callback__ = heater_off_callback
        self.__max_time_callback__ = heater_max_time_callback

        # create heater relay instance
        self.__heater_relay__ = PowerRelay(
            "heater_relay", configuration.heater_pin)
        self.__heater_queue__ = MPQueue()

        # create queue to hold heater timer.
        self.__heater_shutoff_timer__ = None

        # make sure and turn heater off
        self.__heater_relay__.switch_low()

    def __max_time_immediate__(self):
        """
        Trigger everything associated with the timer
        being triggered.
        """
        if self.__max_time_callback__ is not None:
            self.__max_time_callback__()

        self.__stop_heater__()

    def __stop_heater_immediate__(self):
        """
        Turn off the heater.
        """
        if self.__off_callback__ is not None:
            self.__off_callback__()

        self.__stop_heater__()

    def __start_heater_immediate__(self):
        """
        Start the heater.
        """
        if self.__on_callback__ is not None:
            self.__on_callback__()

        self.__start_heater__()

    def __stop_heater__(self):
        """
        Stops the heater.
        """
        self.__logger__.log_info_message("__stop_heater__::switch_low()")
        self.__heater_relay__.switch_low()
        self.__logger__.log_info_message(
            "__stop_heater__::stop_heater_timer()")
        self.__stop_heater_timer__()

    def __start_heater__(self):
        """
        Starts the heater.
        """
        self.__logger__.log_info_message("__start_heater__::switch_high()")
        self.__heater_relay__.switch_high()
        self.__logger__.log_info_message(
            "__start_heater__::start_heater_timer()")
        self.__start_heater_timer__()

    def __stop_heater_timer__(self):
        """
        Stops the heater timer.
        """

        self.__logger__.log_info_message(
            "Cancelling the heater shutoff timer.")
        self.__heater_shutoff_timer__ = None

    def __start_heater_timer__(self):
        """
        Starts the shutdown timer for the heater.
        """
        self.__logger__.log_info_message("Starting the heater shutoff timer.")
        self.__heater_shutoff_timer__ = time.time(
        ) + (self.__configuration__.max_minutes_to_run * 60)

        return True

    def __update_shutoff_timer__(self):
        """
        Check to see if the timer has expired.
        If so, then add it to the action.
        """

        if self.__heater_shutoff_timer__ is not None \
                and self.__heater_shutoff_timer__ < time.time():
            self.__heater_queue__.put(text.MAX_TIME)
        elif self.__heater_shutoff_timer__ is None \
                and self.is_relay_on():
            self.__logger__.log_warning_message(
                "Heater should not be on, but the PIN is still active... attempting shutdown.")
            self.__heater_queue__.put(text.HEATER_OFF_COMMAND)
