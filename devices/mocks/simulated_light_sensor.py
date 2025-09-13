from devices.interfaces.light_sensor import LightSensor
from devices.mocks.sensor_simulator import SensorSimulator
from devices.results.light_sensor_result import LightSensorResult


class SimulatedLightSensor(LightSensor):
    """
    Simulates a light sensor for testing purposes.
    """

    def __init__(self):
        super().__init__()
        self.enabled: bool = True
        self.current_value: LightSensorResult | None = None

        self.__simulated_lux__: SensorSimulator = SensorSimulator(0, 100, 0.1)

    def update(self) -> LightSensorResult | None:
        current_value: float = self.__simulated_lux__.read()

        return LightSensorResult(
            full_spectrum=int(current_value),
            infrared=0,
            lux=int(current_value),
        )
