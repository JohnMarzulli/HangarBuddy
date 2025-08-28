from devices.results.light_sensor_result import LightSensorResult


class LightSensor:
    """
    Interface for a light sensor.
    """

    def __init__(self):
        self.enabled: bool = False
        self.current_value: LightSensorResult | None = None

    def update(self) -> LightSensorResult | None:
        pass
