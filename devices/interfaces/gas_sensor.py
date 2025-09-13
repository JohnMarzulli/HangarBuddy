from devices.results.gas_sensor_result import GasSensorResult

DEFAULT_TRIGGER_THRESHOLD: int = 245
DEFAULT_ALL_CLEAR_THRESHOLD: int = 235


class GasSensor(object):
    """
    Interface for a gas sensor.
    Provides basic functionality to all sensors, and allows for simulators/mocks.

    Should not be created directly.
    """

    def __init__(
        self,
        sensor_trigger_threshold: int = DEFAULT_TRIGGER_THRESHOLD,
        sensor_all_clear_threshold: int = DEFAULT_ALL_CLEAR_THRESHOLD,
    ):
        """
        Initial the base functionality of the gas sensor.

        Args:
            sensor_trigger_threshold (int, optional): If a reading is equal, or greater than, this value then gas is detected . Defaults to DEFAULT_TRIGGER_THRESHOLD.
            sensor_all_clear_threshold (int, optional): If gas is detected, then the value must be equal or less than this value for the alert to clear. Defaults to DEFAULT_ALL_CLEAR_THRESHOLD.
        """
        self.current_value: int | None = DEFAULT_ALL_CLEAR_THRESHOLD
        self.enabled: bool = False
        self.is_gas_detected: bool = False
        self.sensor_trigger_threshold: int = sensor_trigger_threshold
        self.__sensor_all_clear_threshold__: int = sensor_all_clear_threshold

    def get_trigger_threshold_with_units(self) -> str:
        """
        Get text for the trigger threshold with units.
        Suitable for display or a message.

        Returns:
            str: The text to display.
        """
        return f"{self.sensor_trigger_threshold}PPM"

    def get_current_measurement_with_units(self) -> str:
        """
        Get the current measurement with units.

        Returns:
            str: The current measurement with units. Suitable for display or a message.
        """

        return (
            f"{self.current_value}PPM"
            if self.current_value is not None
            else "UNAVILABLE"
        )

    def update(self) -> GasSensorResult:
        """
        Update the gas sensor reading (if time to do so).

        Returns the latest reading (if available).

        Returns:
            GasSensorResult: The most recent gas sensor reading.
        """
        return GasSensorResult(
            False, "UNAVILABLE", self.get_trigger_threshold_with_units()
        )

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
            self.is_gas_detected = (
                self.current_value >= self.__sensor_all_clear_threshold__
            )
