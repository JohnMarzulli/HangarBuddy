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

    def __update_gas_detection__(self):
        if self.current_value is None:
            self.is_gas_detected = False
            return

        # For the warning to be removed, it must drop below an
        # all clear level that is lower than the trigger level.
        # This protects against the alarm triggering over and over
        # again if the sensor is close to the detection level.
        if not self.is_gas_detected:
            self.is_gas_detected = self.current_value >= self.sensor_trigger_threshold
        else:
            self.is_gas_detected = self.current_value >= self.sensor_all_clear_threshold
