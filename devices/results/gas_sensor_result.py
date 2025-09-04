class GasSensorResult(object):
    """
    Object to handle the results from the gas sensor.
    """

    def __init__(
        self, is_gas_detected: bool, current_value: str, threshold_value: str | None
    ):
        self.is_gas_detected: bool = is_gas_detected
        self.current_value: str = current_value
        self.__threshold_value__: str | None = threshold_value

    def get_status_text(self) -> str:
        if self.__threshold_value__ is not None:
            return f"{self.current_value}/{self.__threshold_value__}"

        return self.current_value
