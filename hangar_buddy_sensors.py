"""
Module to abstract and help with keeping our sensors and
configuration in order
"""

import logging
import logging.handlers

from lib.gas_sensor import GasSensor
from lib.light_sensor import LightSensor, LightSensorResult
import lib.temp_probe as temp_probe
from lib.recurring_task import RecurringTask

DEFAULT_SENSOR_LOG = 'sensors.log'
DEFAULT_LIGHT_SENSOR_UPDATE_INTERVAL = 30
DEFAULT_GAS_SENSOR_UPDATE_INTERVAL = 60
DEFAULT_TEMPERATURE_SENSOR_UPDATE_INTEVAL = 120


class Sensors(object):
    """
    Object to handle and help abstract all
    of the sensors we could have or use.
    """

    def __init__(
        self,
        configuration
    ):
        self.__logger__ = logging.getLogger("sensors")
        self.__logger__.setLevel(logging.INFO)
        self.__handler__ = logging.handlers.RotatingFileHandler(
            configuration.get_log_directory() + DEFAULT_SENSOR_LOG,
            maxBytes=1048576,
            backupCount=3)
        self.__handler__.setFormatter(
            logging.Formatter(
                '%(asctime)s %(levelname)-8s %(message)s'))
        self.__logger__.addHandler(self.__handler__)

        self.__gas_sensor__ = None
        self.__light_sensor__ = None

        self.current_gas_sensor_reading = None
        self.current_light_sensor_reading = None
        self.current_temperature_sensor_reading = None

        self.__light_sensor__ = LightSensor()

        if self.__light_sensor__.enabled:
            RecurringTask(
                "__update_light_sensor__",
                DEFAULT_LIGHT_SENSOR_UPDATE_INTERVAL,
                self.__update_light_sensor__,
                self.__logger__)

        if configuration.is_mq2_enabled:
            self.__gas_sensor__ = GasSensor()

            if self.__gas_sensor__ is not None and self.__gas_sensor__.enabled:
                RecurringTask(
                    "__update_gas_sensor__",
                    DEFAULT_GAS_SENSOR_UPDATE_INTERVAL,
                    self.__update_gas_sensor__,
                    self.__logger__)

        if configuration.is_temp_probe_enabled:
            RecurringTask(
                "__update_temperature_sensor__",
                DEFAULT_TEMPERATURE_SENSOR_UPDATE_INTEVAL,
                self.__update_temperature_sensor__,
                self.__logger__)

    def __update_light_sensor__(
        self
    ):
        """
        Reads the light sensor and saves the result.
        """

        self.current_light_sensor_reading = LightSensorResult(
            self.__light_sensor__)
        self.__logger__.info(
            "LIGHT: Lux={}, VIS={}, IR={}".format(
                int(self.current_light_sensor_reading.lux),
                self.current_light_sensor_reading.full_spectrum,
                self.current_light_sensor_reading.infrared))

    def __update_gas_sensor__(
        self
    ):
        """
        Read the gas sensor and keep it up to date.
        """

        if not self.__gas_sensor__.enabled:
            self.current_gas_sensor_reading = None
            return

        self.current_gas_sensor_reading = self.__gas_sensor__.update()

        if self.current_gas_sensor_reading is not None:
            self.__logger__.info(
                "GAS: Level={}, Detected={}".format(
                    self.current_gas_sensor_reading.current_value,
                    self.current_gas_sensor_reading.is_gas_detected))

    def __update_temperature_sensor__(
        self
    ):
        """
        Reads the temperature senso and keep the results.
        """

        sensor_readings = temp_probe.read_sensors()
        if sensor_readings is not None:
            results_count = len(sensor_readings)
            if results_count > 0:
                self.current_temperature_sensor_reading = int(
                    sensor_readings[0])
                self.__logger__.info(
                    "TEMP: F={}".format(
                        self.current_temperature_sensor_reading))
            else:
                self.current_temperature_sensor_reading = None
