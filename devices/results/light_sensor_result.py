class LightSensorResult:
    """
    Stores the reading of a light sensor.
    """

    def __init__(self, full_spectrum: int, infrared: int, lux: int):
        """
        Reads the sensor and stores the results.
        """

        self.full_spectrum: int = full_spectrum
        self.infrared: int = infrared
        self.lux: int = lux
