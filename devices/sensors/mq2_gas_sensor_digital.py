"""Module to help with the gas sensor."""

import time
import platform

IS_DEBUG: bool = platform.system() in ["win32", "Windows", "darwin"]

if not IS_DEBUG:
    from gpiozero import DigitalInputDevice

if __name__ == "__main__":
    import sys
    import os

    # Ensure the parent directory is in sys.path so 'managers' can be imported
    # This is only needed if running the unit tests directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from devices.interfaces.gas_sensor import (
    GasSensor,
)
from devices.results.gas_sensor_result import GasSensorResult

MQ2_DIGITAL_INPUT_PIN: int = 26


class Mq2GasSensorDigital(GasSensor):
    """
    Class to help with the gas sensor.
    """

    def __init__(
        self,
    ):
        super().__init__(1, 0)

        print("Starting init")

        self.enabled: bool = False

        if not IS_DEBUG:
            try:
                self.__digital_input_device__ = DigitalInputDevice(
                    MQ2_DIGITAL_INPUT_PIN
                )
                self.enabled = True
            except Exception as ex:
                self.enabled = False

                print(ex)

        self.is_gas_detected: bool = False
        self.current_value: bool = False

    def get_current_measurement_with_units(self) -> str:
        """
        Get the current measurement with units.

        Returns:
            str: The current measurement with units. Suitable for display or a message.
        """

        if not self.enabled:
            return "UNAVAILABLE"

        return "DETECTED" if self.is_gas_detected else "CLEAR"

    def get_trigger_threshold_with_units(self) -> str:
        """
        Get text for the trigger threshold with units.
        Suitable for display or a message.

        Returns:
            str: The text to display.
        """
        return "DETECTED"

    def update(self):
        """
        Attempts to look for gas.
        """
        if not self.enabled:
            return GasSensorResult(False, "UNK", None)

        # Make sure this is normalized so "bigger number bad"
        self.is_gas_detected = self.__read__()
        self.current_value = self.is_gas_detected

        self.__update_gas_detection__()

        return GasSensorResult(
            self.is_gas_detected, self.get_current_measurement_with_units(), None
        )

    def __read__(self) -> bool:
        """
        Read from the ic2 device.
        """

        if not self.enabled:
            return False

        try:
            # Low is "Gas Present"
            # https://newbiely.com/tutorials/raspberry-pi/raspberry-pi-gas-sensor
            read_value = self.__digital_input_device__.value

            print(f"read_value={read_value}")

            return not read_value
        except:
            self.enabled = False
            return False


if __name__ == "__main__":

    print("Attempting to connect to MQ2 gas sensor")
    SENSOR = Mq2GasSensorDigital()
    print("Connected" if SENSOR.enabled else "ERROR")

    while SENSOR.enabled:
        IS_GAS_DETECTED = SENSOR.update()
        print(
            f"LVL:{str(IS_GAS_DETECTED.current_value)}, {str(IS_GAS_DETECTED.is_gas_detected)}"
        )
        time.sleep(2)
