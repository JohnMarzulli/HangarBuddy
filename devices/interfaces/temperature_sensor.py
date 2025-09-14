"""
Code related to core temperature sensor services and conversions.
"""

if __name__ == "__main__":
    import os
    import sys

    # Ensure the parent directory is in sys.path so 'managers' can be imported
    # This is only needed if running the unit tests directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from devices.results.temperature_result import TemperatureResult
from lib.system_level_logging import SystemLevelLogger


class TemperatureSensor:
    """
    Interface for a light sensor.

    Provides common functionality and hooks for a temperature sensor.
    """

    def __init__(self, logger: SystemLevelLogger):
        self.enabled: bool = False
        self.current_value: int | None = None

        self.__logger__: SystemLevelLogger = logger

    def update(self) -> TemperatureResult | None:
        """
        Services the sensor. May cause a new reading to be taken.

        Returns:
            int | None: The latest temperature reading in Fahrenheit.
        """
        return None
