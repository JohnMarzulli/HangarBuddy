from devices.interfaces.temperature_sensor import TemperatureSensor
from devices.mocks.sensor_simulator import SensorSimulator
from lib.system_level_logging import SystemLevelLogger


class SimulatedTemperatureSensor(TemperatureSensor):
    """
    Simulates a light sensor for testing purposes.
    """

    def __init__(self, logger: SystemLevelLogger):
        super().__init__(logger)
        self.enabled: bool = True
        self.current_value: int | None = None

        self.__simulated_thermometer__: SensorSimulator = SensorSimulator(0, 100, 5)

    def update(self) -> int | None:
        current_value: int = int(self.__simulated_thermometer__.read())

        return current_value
