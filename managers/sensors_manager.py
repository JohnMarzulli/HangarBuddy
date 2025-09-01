"""
Module to abstract and help with keeping our sensors and
configuration in order
"""

import logging
import logging.handlers
import platform

IS_DEBUG: bool = platform.system() in ["win32", "Windows", "darwin"]

from configuration import Configuration
from devices.interfaces.gas_sensor import GasSensor
from devices.interfaces.light_sensor import LightSensor
from devices.interfaces.temperature_sensor import TemperatureSensor
from devices.results.gas_sensor_result import GasSensorResult
from devices.results.light_sensor_result import LightSensorResult
from lib.intermittent_task import IntermittentTask

if not IS_DEBUG:
    from devices.sensors.ds18b20_tempature_sensor import Ds18b20TempatureSensor
    from devices.sensors.mq2_gas_sensor_digital import Mq2GasSensorDigital
    from devices.sensors.tsl2591_light_sensor import Tsl2591LightSensor
else:
    from devices.mocks.simulated_gas_sensor import SimulatedGasSensor
    from devices.mocks.simulated_light_sensor import SimulatedLightSensor
    from devices.mocks.simulated_temperature_sensor import \
        SimulatedTemperatureSensor

DEFAULT_SENSOR_LOG = "sensors.log"
DEFAULT_LIGHT_SENSOR_UPDATE_INTERVAL = 30
DEFAULT_GAS_SENSOR_UPDATE_INTERVAL = 60
DEFAULT_TEMPERATURE_SENSOR_UPDATE_INTEVAL = 120


class SensorsManager:
    """
    Object to handle and help abstract all
    of the sensors we could have or use.
    """

    def __init__(self, configuration: Configuration):
        self.__handler__ = logging.handlers.RotatingFileHandler(
            configuration.get_log_directory() + DEFAULT_SENSOR_LOG,
            maxBytes=1048576,
            backupCount=3,
        )
        self.__handler__.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)-8s %(message)s")
        )

        self.__gas_sensor__: GasSensor = (
            SimulatedGasSensor() if IS_DEBUG else Mq2GasSensorDigital()
        )
        self.__light_sensor__: LightSensor = (
            SimulatedLightSensor() if IS_DEBUG else Tsl2591LightSensor()
        )
        self.__temperature_sensor__: TemperatureSensor = (
            SimulatedTemperatureSensor() if IS_DEBUG else Ds18b20TempatureSensor()
        )

        self.__light_sensor_task__: IntermittentTask = IntermittentTask(
            "__update_light_sensor__",
            DEFAULT_LIGHT_SENSOR_UPDATE_INTERVAL,
            (
                self.__update_light_sensor__
                if configuration.is_light_sensor_enabled
                else self.__noop__
            ),
        )
        self.__gas_sensor_task__: IntermittentTask = IntermittentTask(
            "__update_gas_sensor__",
            DEFAULT_GAS_SENSOR_UPDATE_INTERVAL,
            (
                self.__update_gas_sensor__
                if configuration.is_mq2_enabled
                else self.__noop__
            ),
        )

        self.__temperature_sensor_task__: IntermittentTask = IntermittentTask(
            "__update_temperature_sensor__",
            DEFAULT_TEMPERATURE_SENSOR_UPDATE_INTEVAL,
            (
                self.__update_temperature_sensor__
                if configuration.is_temp_probe_enabled
                else self.__noop__
            ),
        )

        self.current_gas_sensor_reading: GasSensorResult | None = None
        self.current_light_sensor_reading: LightSensorResult | None = None
        self.current_temperature_sensor_reading: int | None = None

        self.update()

    def update(self):
        """
        Updates the sensors and their readings.
        """

        self.__gas_sensor_task__.run()
        self.__light_sensor_task__.run()
        self.__temperature_sensor_task__.run()

    def __noop__(self):
        pass

    def __update_light_sensor__(self):
        """
        Reads the light sensor and saves the result.
        """

        if not self.__light_sensor__.enabled:
            print("LIGHT: Sensor not enabled")

            return

        self.current_light_sensor_reading: LightSensorResult | None = (
            self.__light_sensor__.update()
        )

        if self.current_light_sensor_reading is None:
            print("LIGHT: No reading")

            return

        lux_reading: int = int(self.current_light_sensor_reading.lux)
        visible_reading: int = self.current_light_sensor_reading.full_spectrum
        ir_reading: int = self.current_light_sensor_reading.infrared

        print(f"LIGHT: Lux={lux_reading}, VIS={visible_reading}, IR={ir_reading}")

    def __update_gas_sensor__(self):
        """
        Read the gas sensor and keep it up to date.
        """

        if not self.__gas_sensor__.enabled:
            self.current_gas_sensor_reading = None
            return

        self.current_gas_sensor_reading = self.__gas_sensor__.update()

        if self.current_gas_sensor_reading is not None:
            current_level: int = self.current_gas_sensor_reading.current_value
            is_detected: bool = self.current_gas_sensor_reading.is_gas_detected
            threshold: int = self.__gas_sensor__.sensor_trigger_threshold
            print(
                f"GAS: Level={current_level}, Detected={is_detected}, Threshold={threshold}"
            )

    def __update_temperature_sensor__(self):
        """
        Reads the temperature senso and keep the results.
        """

        if not self.__temperature_sensor__.enabled:
            self.current_temperature_sensor_reading = None
            print("TEMP: Sensor not enabled")
            return

        self.current_temperature_sensor_reading = self.__temperature_sensor__.update()

        if self.current_temperature_sensor_reading is not None:
            print(f"TEMP: Current={self.current_temperature_sensor_reading}F")
        else:
            print("TEMP: ERROR READING SENSOR")
