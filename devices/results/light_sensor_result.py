from devices.results.light_level import LightLevel


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

    def get_light_level(self) -> LightLevel:
        """
        Gets the light level based on the lux reading.

        Returns:
            LightLevel: The light level.
        """

        if self.lux < 50:
            return LightLevel.DARK

        return LightLevel.DIM if self.lux < 200 else LightLevel.BRIGHT
