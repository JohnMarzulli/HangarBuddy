"""
Code related to core temperature sensor services and conversions.
"""


def celsius_to_fahrenheit(temp_in_celsius: float) -> float:
    """
    converts celsius to F.
    Needs a float.
    """
    return ((temp_in_celsius * 9.0) / 5.0) + 32.0


class TemperatureSensor:
    """
    Interface for a light sensor.

    Provides common functionality and hooks for a temperature sensor.
    """

    def __init__(self):
        self.enabled: bool = False
        self.current_value: int | None = None

    def update(self) -> int | None:
        """
        Services the sensor. May cause a new reading to be taken.

        Returns:
            int | None: The latest temperature reading in Fahrenheit.
        """
        pass
