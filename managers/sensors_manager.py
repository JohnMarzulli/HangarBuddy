"""
Module to abstract and help with keeping our sensors and
configuration in order
"""

import platform

IS_DEBUG: bool = platform.system() in ["win32", "Windows", "darwin"]

if __name__ == "__main__":
    import os
    import sys

    # Ensure the parent directory is in sys.path so 'managers' can be imported
    # This is only needed if running the unit tests directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from configuration import Configuration
from devices.interfaces.gas_sensor import GasSensor
from devices.interfaces.light_sensor import LightSensor
from devices.interfaces.temperature_sensor import TemperatureSensor
from devices.results.gas_sensor_result import GasSensorResult
from devices.results.light_sensor_result import LightSensorResult
from lib.intermittent_task import IntermittentTask
from lib.system_level_logging import SystemLevelLogger

if not IS_DEBUG:
    from devices.sensors.ds18b20_temperature_sensor import Ds18b20TemperatureSensor
    from devices.sensors.mq2_gas_sensor_digital import Mq2GasSensorDigital
    from devices.sensors.tsl2591_light_sensor import Tsl2591LightSensor

from devices.mocks.simulated_gas_sensor import SimulatedGasSensor
from devices.mocks.simulated_light_sensor import SimulatedLightSensor
from devices.mocks.simulated_temperature_sensor import SimulatedTemperatureSensor

DEFAULT_LIGHT_SENSOR_UPDATE_INTERVAL = 1
DEFAULT_GAS_SENSOR_UPDATE_INTERVAL = 15
DEFAULT_TEMPERATURE_SENSOR_UPDATE_INTERVAL = 120


class SensorsManager:
    """
    Object to handle and help abstract all
    of the sensors we could have or use.
    """

    def __init__(
        self,
        configuration: Configuration,
        logger: SystemLevelLogger,
    ):
        """
        Manager to handle and control servicing any attached sensors.
        Handles initialization.

        Args:
            configuration (Configuration): The configuration that would contain pin and bus settings.
        """
        self.__logger__: SystemLevelLogger = logger

        self.__gas_sensor__: GasSensor = SimulatedGasSensor(logger) if IS_DEBUG else Mq2GasSensorDigital(logger)
        self.__light_sensor__: LightSensor = SimulatedLightSensor(logger) if IS_DEBUG else Tsl2591LightSensor(logger)
        self.__temperature_sensor__: TemperatureSensor = (
            SimulatedTemperatureSensor(logger) if IS_DEBUG else Ds18b20TemperatureSensor(logger)
        )

        self.__light_sensor_task__: IntermittentTask = IntermittentTask(
            "__update_light_sensor__",
            DEFAULT_LIGHT_SENSOR_UPDATE_INTERVAL,
            (self.__update_light_sensor__ if configuration.is_light_sensor_enabled else self.__noop__),
        )
        self.__log_light_sensor_task__: IntermittentTask = IntermittentTask(
            "__log_light_sensor__",
            30,
            self.__log_light_sensor__,
        )
        self.__gas_sensor_task__: IntermittentTask = IntermittentTask(
            "__update_gas_sensor__",
            DEFAULT_GAS_SENSOR_UPDATE_INTERVAL,
            (self.__update_gas_sensor__ if configuration.is_mq2_enabled else self.__noop__),
        )

        self.__temperature_sensor_task__: IntermittentTask = IntermittentTask(
            "__update_temperature_sensor__",
            DEFAULT_TEMPERATURE_SENSOR_UPDATE_INTERVAL,
            (self.__update_temperature_sensor__ if configuration.is_temp_probe_enabled else self.__noop__),
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
        self.__log_light_sensor_task__.run()
        self.__temperature_sensor_task__.run()

    def __noop__(self):
        pass

    def __update_light_sensor__(self):
        """
        Reads the light sensor and saves the result.
        """

        if not self.__light_sensor__.enabled:
            self.__logger__.warning("LIGHT: Sensor not enabled")

            return

        self.current_light_sensor_reading: LightSensorResult | None = self.__light_sensor__.update()

        if self.current_light_sensor_reading is None:
            self.__logger__.warning("LIGHT: No reading")

    def __log_light_sensor__(self):
        if self.current_light_sensor_reading is None:
            return

        lux_reading: int = int(self.current_light_sensor_reading.lux)
        visible_reading: int = self.current_light_sensor_reading.full_spectrum
        ir_reading: int = self.current_light_sensor_reading.infrared

        self.__logger__.info(
            f"LIGHT: Level={self.current_light_sensor_reading.get_light_level().name}, Lux={lux_reading}, VIS={visible_reading}, IR={ir_reading}"
        )

    def __update_gas_sensor__(self):
        """
        Read the gas sensor and keep it up to date.
        """

        if not self.__gas_sensor__.enabled:
            self.current_gas_sensor_reading = None
            return

        self.current_gas_sensor_reading = self.__gas_sensor__.update()

        if self.current_gas_sensor_reading is not None:
            current_level: str = self.current_gas_sensor_reading.current_value
            is_detected: bool = self.current_gas_sensor_reading.is_gas_detected
            threshold: int = self.__gas_sensor__.sensor_trigger_threshold
            self.__logger__.info(f"GAS: Level={current_level}, Detected={is_detected}, Threshold={threshold}")

    def __update_temperature_sensor__(self):
        """
        Reads the temperature sensor and keep the results.
        """

        if not self.__temperature_sensor__.enabled:
            self.current_temperature_sensor_reading = None
            self.__logger__.warning("TEMP: Sensor not enabled")
            return

        self.current_temperature_sensor_reading = self.__temperature_sensor__.update()

        if self.current_temperature_sensor_reading is not None:
            self.__logger__.info(f"TEMP: Current={self.current_temperature_sensor_reading}F")
        else:
            self.__logger__.warning("TEMP: ERROR READING SENSOR")
