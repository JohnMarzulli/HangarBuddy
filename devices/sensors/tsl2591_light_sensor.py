"""
This code is basically an adaptation of the Arduino_TSL2591 library from
adafruit: https://github.com/adafruit/Adafruit_TSL2591_Library

for configuring I2C in a raspberry
https://learn.adafruit.com/adafruits-raspberry-pi-lesson-4-gpio-setup/configuring-i2c

datasheet:
http://ams.com/eng/Products/Light-Sensors/Light-to-Digital-Sensors/TSL25911

Taken from https://github.com/maxlklaxl/python-tsl2591/blob/master/tsl2591/read_tsl.py

"""

import time
import smbus  # type: ignore - Only will be run on Raspberry Pi

if __name__ == "__main__":
    import sys
    import os
    # Ensure the parent directory is in sys.path so 'managers' can be imported
    # This is only needed if running the unit tests directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import lib.local_debug as local_debug
from devices.interfaces.light_sensor import LightSensor
from devices.results.light_sensor_result import LightSensorResult

VISIBLE = 2  # channel 0 - channel 1
INFRARED = 1  # channel 1
FULLSPECTRUM = 0  # channel 0

ADDR = 0x29
READBIT = 0x01
COMMAND_BIT = 0xA0  # bits 7 and 5 for 'command normal'
CLEAR_BIT = 0x40  # Clears any pending interrupt (write 1 to clear)
WORD_BIT = 0x20  # 1 = read/write word (rather than byte)
BLOCK_BIT = 0x10  # 1 = using block read/write
ENABLE_POWERON = 0x01
ENABLE_POWEROFF = 0x00
ENABLE_AEN = 0x02
ENABLE_AIEN = 0x10
CONTROL_RESET = 0x80
LUX_DF = 408.0
LUX_COEFB = 1.64  # CH0 coefficient
LUX_COEFC = 0.59  # CH1 coefficient A
LUX_COEFD = 0.86  # CH2 coefficient B

REGISTER_ENABLE = 0x00
REGISTER_CONTROL = 0x01
REGISTER_THRESHHOLDL_LOW = 0x02
REGISTER_THRESHHOLDL_HIGH = 0x03
REGISTER_THRESHHOLDH_LOW = 0x04
REGISTER_THRESHHOLDH_HIGH = 0x05
REGISTER_INTERRUPT = 0x06
REGISTER_CRC = 0x08
REGISTER_ID = 0x0A
REGISTER_CHAN0_LOW = 0x14
REGISTER_CHAN0_HIGH = 0x15
REGISTER_CHAN1_LOW = 0x16
REGISTER_CHAN1_HIGH = 0x17
INTEGRATIONTIME_100MS = 0x00
INTEGRATIONTIME_200MS = 0x01
INTEGRATIONTIME_300MS = 0x02
INTEGRATIONTIME_400MS = 0x03
INTEGRATIONTIME_500MS = 0x04
INTEGRATIONTIME_600MS = 0x05

GAIN_LOW = 0x00  # low gain (1x)
GAIN_MED = 0x10  # medium gain (25x)
GAIN_HIGH = 0x20  # medium gain (428x)
GAIN_MAX = 0x30  # max gain (9876x)


class Tsl2591LightSensor(LightSensor):
    """
    Object to handle the Adafruit light sensor.
    """

    def __init__(
        self,
        i2c_bus=1,
        sensor_address=0x29,
        integration=INTEGRATIONTIME_100MS,
        gain=GAIN_LOW,
    ):
        super().__init__()

        try:
            if not local_debug.is_debug():
                print("Initializing i2c bus")
                self.bus = smbus.SMBus(i2c_bus)

            self.sensor_address = sensor_address
            self.integration_time = integration
            self.gain = gain
            self.enabled = True

            print("Setting timing")
            self.__set_timing__(self.integration_time)
            self.__set_gain__(self.gain)
            self.__disable__()  # to be sure
            print("Enabled")
        except:
            print("Failed to initialize")
            self.enabled = False

    def update(self) -> LightSensorResult | None:
        """
        Updates the sensor reading.
        """

        try:
            full, ir = self.__get_full_luminosity__()
            lux = self.__get_calculated_lux__(full, ir)

            self.current_value = LightSensorResult(full, ir, lux)
        except Exception as ex:
            print(f"Failed to read light sensor: {ex}")
            self.current_value = None

        return self.current_value

    def __set_timing__(self, integration):
        if not self.enabled:
            return

        self.__is_enable__()
        self.integration_time = integration
        if not local_debug.is_debug():
            print("set_timing:Writing data byte")
            self.bus.write_byte_data(
                self.sensor_address,
                COMMAND_BIT | REGISTER_CONTROL,
                self.integration_time | self.gain,
            )
        self.__disable__()

    def __set_gain__(self, gain):
        self.__is_enable__()
        self.gain = gain

        if not self.enabled:
            return

        if local_debug.is_debug():
            return

        self.bus.write_byte_data(
            self.sensor_address,
            COMMAND_BIT | REGISTER_CONTROL,
            self.integration_time | self.gain,
        )
        self.__disable__()

    def __get_calculated_lux__(self, full, ir):
        # Check for overflow conditions first
        if (full == 0xFFFF) | (ir == 0xFFFF):
            return 0

        case_integ = {
            INTEGRATIONTIME_100MS: 100.0,
            INTEGRATIONTIME_200MS: 200.0,
            INTEGRATIONTIME_300MS: 300.0,
            INTEGRATIONTIME_400MS: 400.0,
            INTEGRATIONTIME_500MS: 500.0,
            INTEGRATIONTIME_600MS: 600.0,
        }
        if self.integration_time in case_integ.keys():
            atime = case_integ[self.integration_time]
        else:
            atime = 100.0

        case_gain = {
            GAIN_LOW: 1.0,
            GAIN_MED: 25.0,
            GAIN_HIGH: 428.0,
            GAIN_MAX: 9876.0,
        }

        again = case_gain.get(self.gain, 1.0)

        # cpl = (ATIME * AGAIN) / DF
        cpl = (atime * again) / LUX_DF
        lux1 = (full - (LUX_COEFB * ir)) / cpl

        lux2 = ((LUX_COEFC * full) - (LUX_COEFD * ir)) / cpl

        # The highest value is the approximate lux equivalent
        return max([lux1, lux2])

    def __is_enable__(self):
        if local_debug.is_debug():
            return

        if not self.enabled:
            return

        print("enable:writing to data bus.")
        self.bus.write_byte_data(
            self.sensor_address,
            COMMAND_BIT | REGISTER_ENABLE,
            ENABLE_POWERON | ENABLE_AEN | ENABLE_AIEN,
        )  # Enable
        print("Done enabling")

    def __disable__(self):
        if not self.enabled or local_debug.is_debug():
            return

        self.bus.write_byte_data(
            self.sensor_address, COMMAND_BIT | REGISTER_ENABLE, ENABLE_POWEROFF
        )

    def __get_full_luminosity__(self):
        self.__is_enable__()
        # not sure if we need it "// Wait x ms for ADC to complete"
        time.sleep(0.120 * self.integration_time + 1)

        if not self.enabled or local_debug.is_debug():
            return 0, 0

        full = self.bus.read_word_data(
            self.sensor_address, COMMAND_BIT | REGISTER_CHAN0_LOW
        )
        ir = self.bus.read_word_data(
            self.sensor_address, COMMAND_BIT | REGISTER_CHAN1_LOW
        )
        self.__disable__()
        return full, ir


if __name__ == "__main__":

    tsl = Tsl2591LightSensor()  # initialize

    #    tsl.set_gain(GAIN_MED)
    #    tsl.set_timing(INTEGRATIONTIME_100MS)

    result: LightSensorResult | None = tsl.update()
    result_text:str = "ERROR" if result is None else result.lux

    print(f"Lux={result_text}")
