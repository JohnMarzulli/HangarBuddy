""" Module to help with the gas sensor. """

import time
import local_debug

if not local_debug.is_debug():
    import smbus

DEFAULT_IC2_BUS = 1
DEFAULT_IC2_ADDRESS = 0x48
DEVICE_REG_MODW1 = 0x00
DEFAULT_CHANNEL_READ_OFFSET = 0x40
DEFAULT_DEVICE_CHANNEL = 0
DEFAULT_TRIGGER_THRESHOLD = 230
DEFAULT_ALL_CLEAR_THRESHOLD = 220

class GasSensorResult(object):
    """
    Object to handle the results from the gas sensor.
    """

    def __init__(self, is_gas_detected, current_value):
        self.is_gas_detected = is_gas_detected
        self.current_value = current_value


class GasSensor(object):
    """
    Class to help with the gas sensor.
    """

    def __init__(self,
                 sensor_trigger_threshold=DEFAULT_TRIGGER_THRESHOLD,
                 sensor_all_clear_threshold=DEFAULT_ALL_CLEAR_THRESHOLD):
        print "Starting init"
        if local_debug.is_debug():
            self.ic2_bus = None
        else:
            self.ic2_bus = smbus.SMBus(DEFAULT_IC2_BUS)

        self.is_gas_detected = False
        self.sensor_trigger_threshold = sensor_trigger_threshold
        self.sensor_all_clear_threshold = sensor_all_clear_threshold
        self.current_value = DEFAULT_ALL_CLEAR_THRESHOLD
        self.simulator_direction = 1

    def __read__(self, read_offset=DEFAULT_CHANNEL_READ_OFFSET):
        """
        Read from the ic2 device.
        """

        # Provide a mock/simulator for debugging on Mac/Windows
        if local_debug.is_debug():
            bounce_up_threshold = DEFAULT_ALL_CLEAR_THRESHOLD * 0.9
            bounce_down_threshold = DEFAULT_TRIGGER_THRESHOLD * 1.1
            if self.simulator_direction < 0 and self.current_value is None \
                    or (self.current_value <= 0 or self.current_value < bounce_up_threshold):
                self.simulator_direction = 1
                self.current_value = DEFAULT_ALL_CLEAR_THRESHOLD * 0.9
            elif self.simulator_direction > 0 and self.current_value > bounce_down_threshold:
                self.current_value = (DEFAULT_TRIGGER_THRESHOLD * 1.2)
                self.simulator_direction = -1

            self.current_value += self.simulator_direction
            return int(self.current_value)

        self.ic2_bus.write_byte(DEFAULT_IC2_ADDRESS,
                                read_offset)

        # Needs a "dummy read" for the conversion to happen
        # The write back needs to compress the range of values
        # from 0-255 to 125 to 255.
        # This makes the LED light up
        self.ic2_bus.read_byte(DEFAULT_IC2_ADDRESS)

        raw_value = self.ic2_bus.read_byte(DEFAULT_IC2_ADDRESS)
        converted_value = raw_value * (255.0 - 125.0) / 255.0 + 125.0
        print "RAW=" + str(raw_value) + ", CONV=" + str(converted_value)

        self.ic2_bus.write_byte_data(
            DEFAULT_IC2_ADDRESS, 0x40, int(converted_value))

        return raw_value

    def update(self, read_offset=DEFAULT_CHANNEL_READ_OFFSET):
        """
        Attempts to look for gas.
        """

        self.current_value = self.__read__(read_offset)

        # For the warning to be removed, it must drop below an
        # all clear level that is lower than the trigger level.
        # This protects against the alarm triggering over and over
        # again if the sensor is close to the detection level.
        if self.is_gas_detected:
            self.is_gas_detected = self.current_value > self.sensor_all_clear_threshold

        self.is_gas_detected |= self.current_value >= self.sensor_trigger_threshold

        return GasSensorResult(self.is_gas_detected, self.current_value)


if __name__ == '__main__':
    SENSOR = GasSensor()

    while True:
        IS_GAS_DETECTED = SENSOR.update()
        print "LVL:" + str(SENSOR.current_value) + ", " + str(IS_GAS_DETECTED)
        time.sleep(0.2)
