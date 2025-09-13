class GasSensorResult(object):
    """
    Object to handle the results from the gas sensor.
    """

    def __init__(
        self, is_gas_detected: bool, current_value: str, threshold_value: str | None
    ):
        """
        Initialize the result.

        Args:
            is_gas_detected (bool): Is gas detected?
            current_value (str): The most current reading, should include units.
            threshold_value (str | None): The value that trips the sensor. Should include units.
        """
        self.is_gas_detected: bool = is_gas_detected
        self.current_value: str = current_value
        self.__threshold_value__: str | None = threshold_value

    def get_status_text(self) -> str:
        """
        Get friendly text. Intended for messaging or logging.

        Returns:
            str: Text describing the reading.
        """
        if self.__threshold_value__ is not None:
            return f"{self.current_value}/{self.__threshold_value__}"

        return self.current_value
