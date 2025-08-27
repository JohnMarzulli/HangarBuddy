import random
from datetime import datetime


class SensorSimulator:
    """
    Simulates a sensor that changes value over time.
    This can be any sort of sensor (temperature, humidity, gas, light).
    """

    def __init__(self, min_value: float, max_value: float, units_per_minute: float):
        """
        Initialize the simulator with the range of values and the speed of change.

        Args:
            min_value (float): The minimum value the sensor simulator will return.
            max_value (float): The maximum value the sensor simulator will return.
            units_per_minute (float): How quickly the sensor value changes, in units per minute.
        """

        self.min_value: float = min_value
        self.max_value: float = max_value
        self.units_per_minute: float = units_per_minute
        self.current_value: float = random.uniform(self.min_value, self.max_value)
        self.direction: int = 1
        self.last_update_time: datetime = datetime.now()

    def get_current_value(self) -> float:
        """
        What is the current value of the "sensor"?

        Returns:
            float: The simulated sensor value, as a number.
        """
        return self.current_value

    def read(self) -> float:
        """
        Simulates reading the sensor, updating its value based on time elapsed.

        Returns:
            float: The new "value" that was "read" by the sensor simulator.
        """
        seconds_since_last_update: float = (
            datetime.now() - self.last_update_time
        ).total_seconds()
        change_amount: float = (
            self.units_per_minute / 60.0
        ) * seconds_since_last_update
        self.current_value += change_amount * self.direction

        if self.current_value >= self.max_value:
            self.current_value = self.max_value
            self.direction = -1
        elif self.current_value <= self.min_value:
            self.current_value = self.min_value
            self.direction = 1

        return round(self.current_value, 2)
