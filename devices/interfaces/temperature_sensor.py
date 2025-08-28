def celcius_to_farenheit(temp_in_celcius: float) -> float:
    """
    converts celcius to F.
    Needs a float.
    """
    return ((temp_in_celcius * 9.0) / 5.0) + 32.0


class TemperatureSensor:
    """
    Interface for a light sensor.
    """

    def __init__(self):
        self.enabled: bool = False
        self.current_value: int | None = None

    def update(self) -> int | None:
        pass
