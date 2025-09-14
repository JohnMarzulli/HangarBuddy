def celsius_to_fahrenheit(temp_in_celsius: float) -> float:
    """
    converts celsius to F.
    Needs a float.
    """
    return ((temp_in_celsius * 9.0) / 5.0) + 32.0


class TemperatureResult:
    """
    Stores the result from a temperature probe
    """

    def __init__(self, temp_in_celsius: float):
        self.celsius: float = temp_in_celsius
        """
        The temperature in Metric.
        """
        self.fahrenheit: float = celsius_to_fahrenheit(temp_in_celsius)
        """
        The temperature in Imperial.
        """

    def get_celsius(self) -> str:
        """
        Get the formatted temperature, with units, in Metric.

        Returns:
            str: The formatted temperature, with units, in Metric.
        """
        return f"{self.celsius:0.1f}C"

    def get_fahrenheit(self) -> str:
        """
        Get the formatted temperature, with units, in Imperial.

        Returns:
            str: The formatted temperature, with units, in Imperial.
        """
        return f"{self.fahrenheit:0.1f}F"
