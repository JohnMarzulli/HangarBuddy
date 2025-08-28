from devices.results.gas_sensor_result import GasSensorResult

DEFAULT_TRIGGER_THRESHOLD: int = 245
DEFAULT_ALL_CLEAR_THRESHOLD: int = 235


class GasSensor(object):
    """
    Class to help with the gas sensor.
    """

    def __init__(
        self,
        sensor_trigger_threshold: int = DEFAULT_TRIGGER_THRESHOLD,
        sensor_all_clear_threshold: int = DEFAULT_ALL_CLEAR_THRESHOLD,
    ):
        self.current_value: int | None = DEFAULT_ALL_CLEAR_THRESHOLD
        self.sensor_trigger_threshold: int = sensor_trigger_threshold
        self.sensor_all_clear_threshold: int = sensor_all_clear_threshold
        self.enabled: bool = False
        self.is_gas_detected: bool = False

    def update(self) -> GasSensorResult:
        return GasSensorResult(False, 0)
