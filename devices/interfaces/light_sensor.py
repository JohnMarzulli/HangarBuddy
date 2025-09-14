from devices.results.light_sensor_result import LightSensorResult
from lib.system_level_logging import SystemLevelLogger


class LightSensor:
    """
    Interface for a light sensor.
    Provides basic functionality to all sensors, and allows for simulators/mocks.

    Should not be created directly.
    """

    def __init__(self, logger: SystemLevelLogger):
        """
        Initialize the base functionality of a light sensor.
        """
        self.enabled: bool = False
        self.current_value: LightSensorResult | None = None

        self.__logger__: SystemLevelLogger = logger

    def update(self) -> LightSensorResult | None:
        """
        Services the sensor. May cause measurements to be taken.

        Returns:
            LightSensorResult | None: The most recent sensor reading.
        """
        pass
