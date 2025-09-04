"""Module to simulate the gas sensor."""

from devices.interfaces.gas_sensor import GasSensor
from devices.mocks.sensor_simulator import SensorSimulator
from devices.results.gas_sensor_result import GasSensorResult

DEFAULT_TRIGGER_THRESHOLD = 245
DEFAULT_ALL_CLEAR_THRESHOLD = 235


class SimulatedGasSensor(GasSensor):
    """
    Simulates a gas sensor for testing purposes.
    """

    def __init__(
        self,
        sensor_trigger_threshold=DEFAULT_TRIGGER_THRESHOLD,
        sensor_all_clear_threshold=DEFAULT_ALL_CLEAR_THRESHOLD,
    ):
        super().__init__(sensor_trigger_threshold, sensor_all_clear_threshold)

        print("Starting init")

        self.enabled = True
        self.is_gas_detected = False
        self.sensor_trigger_threshold = sensor_trigger_threshold
        self.__sensor_all_clear_threshold__ = sensor_all_clear_threshold
        self.__sensor_simulator__: SensorSimulator = SensorSimulator(
            sensor_all_clear_threshold * 0.5, sensor_trigger_threshold * 1.1, 2.5
        )
        self.current_value = int(self.__sensor_simulator__.get_current_value())

    def update(self):
        """
        Simulates an I2C based MQ2 gas sensor reading.
        """

        self.current_value = int(self.__sensor_simulator__.read())

        self.__update_gas_detection__()

        return GasSensorResult(self.is_gas_detected, self.get_current_measurement_with_units())
