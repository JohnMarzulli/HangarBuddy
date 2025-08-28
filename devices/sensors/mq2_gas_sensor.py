"""Module to help with the gas sensor."""

import time

# Only will be run on Raspberry Pi
import smbus  # type: ignore

from devices.interfaces.gas_sensor import (
    DEFAULT_ALL_CLEAR_THRESHOLD,
    DEFAULT_TRIGGER_THRESHOLD,
    GasSensor,
)
from devices.results.gas_sensor_result import GasSensorResult

DEFAULT_IC2_BUS = 1
DEFAULT_IC2_ADDRESS = 0x48
DEVICE_REG_MODW1 = 0x00
DEFAULT_CHANNEL_READ_OFFSET = 0x40
DEFAULT_DEVICE_CHANNEL = 0


class Mq2GasSensor(GasSensor):
    """
    Class to help with the gas sensor.
    """

    def __init__(
        self,
        sensor_trigger_threshold=DEFAULT_TRIGGER_THRESHOLD,
        sensor_all_clear_threshold=DEFAULT_ALL_CLEAR_THRESHOLD,
    ):
        super().__init__(sensor_trigger_threshold, sensor_all_clear_threshold)

        print("Starting init")

        try:
            self.ic2_bus = smbus.SMBus(DEFAULT_IC2_BUS)
            self.enabled = True
        except:
            self.enabled = False

        self.is_gas_detected = False
        self.sensor_trigger_threshold = sensor_trigger_threshold
        self.sensor_all_clear_threshold = sensor_all_clear_threshold
        self.current_value = DEFAULT_ALL_CLEAR_THRESHOLD

    def __read__(self, read_offset=DEFAULT_CHANNEL_READ_OFFSET):
        """
        Read from the ic2 device.
        """

        if not self.enabled:
            return None

        try:
            self.ic2_bus.write_byte(DEFAULT_IC2_ADDRESS, read_offset)

            # Needs a "dummy read" for the conversion to happen
            # The write back needs to compress the range of values
            # from 0-255 to 125 to 255.
            # This makes the LED light up
            self.ic2_bus.read_byte(DEFAULT_IC2_ADDRESS)

            raw_value = self.ic2_bus.read_byte(DEFAULT_IC2_ADDRESS)
            converted_value = raw_value * (255.0 - 125.0) / 255.0 + 125.0
            print(f"RAW={str(raw_value)}, CONV={str(converted_value)}")

            self.ic2_bus.write_byte_data(
                DEFAULT_IC2_ADDRESS, 0x40, int(converted_value)
            )

            return raw_value
        except:
            self.enabled = False
            return None

    def update(self):
        """
        Attempts to look for gas.
        """

        self.current_value = self.__read__(DEFAULT_CHANNEL_READ_OFFSET)

        if self.current_value is None or not self.enabled:
            return GasSensorResult(False, DEFAULT_ALL_CLEAR_THRESHOLD)

        self.__update_gas_detection__()

        return GasSensorResult(self.is_gas_detected, self.current_value)


if __name__ == "__main__":
    SENSOR = GasSensor()

    while SENSOR.enabled:
        IS_GAS_DETECTED = SENSOR.update()
        print(
            f"LVL:{str(IS_GAS_DETECTED.current_value)}, {str(IS_GAS_DETECTED.is_gas_detected)}"
        )
        time.sleep(0.2)
