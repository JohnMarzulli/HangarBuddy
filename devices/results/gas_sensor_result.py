class GasSensorResult(object):
    """
    Object to handle the results from the gas sensor.
    """

    def __init__(self, is_gas_detected, current_value):
        self.is_gas_detected = is_gas_detected
        self.current_value = current_value