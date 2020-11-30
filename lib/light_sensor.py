'''
This code is basically an adaptation of the Arduino_TSL2591 library from
adafruit: https://github.com/adafruit/Adafruit_TSL2591_Library

for configuring I2C in a raspberry
https://learn.adafruit.com/adafruits-raspberry-pi-lesson-4-gpio-setup/configuring-i2c

datasheet:
http://ams.com/eng/Products/Light-Sensors/Light-to-Digital-Sensors/TSL25911

Taken from https://github.com/maxlklaxl/python-tsl2591/blob/master/tsl2591/read_tsl.py

'''

import time

from lib import local_debug

if not local_debug.is_debug():
    import smbus

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


class LightSensor(object):
    """
    Object to handle the Adafruit light sensor.
    """

    def __init__(
        self,
        i2c_bus=1,
        sensor_address=0x29,
        integration=INTEGRATIONTIME_100MS,
        gain=GAIN_LOW
    ):
        if not local_debug.is_debug():
            print("Initializing i2c bus")
            self.bus = smbus.SMBus(i2c_bus)

        self.sensor_address = sensor_address
        self.integration_time = integration
        self.gain = gain
        self.enabled = True

        try:
            print("Setting timing")
            self.set_timing(self.integration_time)
            self.set_gain(self.gain)
            self.disable()  # to be sure
            print("Enabled")
        except:
            print("Failed to initialize")
            self.enabled = False

    def set_timing(
        self,
        integration
    ):
        if not self.enabled:
            print("set_timing:Not enbabled")
            return

        print("set_timing:Enabling")
        self.enable()
        self.integration_time = integration
        if not local_debug.is_debug():
            print("set_timing:Writing data byte")
            self.bus.write_byte_data(
                self.sensor_address,
                COMMAND_BIT | REGISTER_CONTROL,
                self.integration_time | self.gain
            )
        print("Disabling")
        self.disable()

    def get_timing(
        self
    ):
        return self.integration_time

    def set_gain(
        self,
        gain
    ):
        self.enable()
        self.gain = gain

        if not self.enabled:
            return

        if local_debug.is_debug():
            return

        self.bus.write_byte_data(
            self.sensor_address,
            COMMAND_BIT | REGISTER_CONTROL,
            self.integration_time | self.gain
        )
        self.disable()

    def get_gain(
        self
    ):
        """
        Returns the gain being used by the sensor.
        """
        return self.gain

    def calculate_lux(
        self,
        full,
        ir
    ):
        # Check for overflow conditions first
        if (full == 0xFFFF) | (ir == 0xFFFF):
            return 0

        case_integ = {
            INTEGRATIONTIME_100MS: 100.,
            INTEGRATIONTIME_200MS: 200.,
            INTEGRATIONTIME_300MS: 300.,
            INTEGRATIONTIME_400MS: 400.,
            INTEGRATIONTIME_500MS: 500.,
            INTEGRATIONTIME_600MS: 600.,
        }
        if self.integration_time in case_integ.keys():
            atime = case_integ[self.integration_time]
        else:
            atime = 100.

        case_gain = {
            GAIN_LOW: 1.,
            GAIN_MED: 25.,
            GAIN_HIGH: 428.,
            GAIN_MAX: 9876.,
        }

        if self.gain in case_gain.keys():
            again = case_gain[self.gain]
        else:
            again = 1.

        # cpl = (ATIME * AGAIN) / DF
        cpl = (atime * again) / LUX_DF
        lux1 = (full - (LUX_COEFB * ir)) / cpl

        lux2 = ((LUX_COEFC * full) - (LUX_COEFD * ir)) / cpl

        # The highest value is the approximate lux equivalent
        return max([lux1, lux2])

    def enable(
        self
    ):
        print("Entering enable")
        if local_debug.is_debug():
            print("Local debug")
            return
        if not self.enabled:
            print("Not enabled")
            return

        print("enable:writing to data bus.")
        self.bus.write_byte_data(
            self.sensor_address,
            COMMAND_BIT | REGISTER_ENABLE,
            ENABLE_POWERON | ENABLE_AEN | ENABLE_AIEN
        )  # Enable
        print("Done enabling")

    def disable(
        self
    ):
        if not self.enabled or local_debug.is_debug():
            return

        self.bus.write_byte_data(
            self.sensor_address,
            COMMAND_BIT | REGISTER_ENABLE,
            ENABLE_POWEROFF
        )

    def get_full_luminosity(
        self
    ):
        self.enable()
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
        self.disable()
        return full, ir

    def get_luminosity(
        self,
        channel
    ):
        full, ir = self.get_full_luminosity()
        if channel == FULLSPECTRUM:
            # Reads two byte value from channel 0 (visible + infrared)
            return full
        elif channel == INFRARED:
            # Reads two byte value from channel 1 (infrared)
            return ir
        elif channel == VISIBLE:
            # Reads all and subtracts out ir to give just the visible!
            return full - ir

        # unknown channel!
        return 0


class LightSensorResult(object):
    """
    Stores the reading of a light sensor.
    """

    def __init__(
        self,
        tsl_sensor
    ):
        """
        Reads the sensor and stores the results.
        """

        try:
            full, ir = tsl_sensor.get_full_luminosity()
            lux = tsl_sensor.calculate_lux(full, ir)

            self.full_spectrum = full
            self.infrared = ir
            self.lux = lux
            self.enabled = True
        except:
            self.full_spectrum = 0
            self.infrared = 0
            self.lux = 0
            self.enabled = False


if __name__ == '__main__':

    TSL = LightSensor()  # initialize

#    tsl.set_gain(GAIN_MED)
#    tsl.set_timing(INTEGRATIONTIME_100MS)

    RESULT = LightSensorResult(TSL)
    print("Lux={}".format(RESULT.lux))
