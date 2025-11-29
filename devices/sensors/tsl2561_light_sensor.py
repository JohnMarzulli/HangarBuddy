"""
TSL2561 light sensor adapter for HangarBuddy, matching the LightSensor interface.

This is a TSL2561 port of the earlier TSL2591-based implementation.
"""

import time
import smbus  # type: ignore - Only will be run on Raspberry Pi

if __name__ == "__main__":
    import os
    import sys

    # Ensure the parent directory is in sys.path so 'managers' can be imported
    # This is only needed if running the unit tests directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import lib.local_debug as local_debug
from devices.interfaces.light_sensor import LightSensor
from devices.results.light_sensor_result import LightSensorResult
from lib.system_level_logging import SystemLevelLogger

# Channel selectors (same semantics as before)
VISIBLE = 2  # channel 0 - channel 1
INFRARED = 1  # channel 1
FULLSPECTRUM = 0  # channel 0

# --- TSL2561 constants (T package coefficients & register map) ---

DEFAULT_ADDR = 0x39

# Command / control bits
COMMAND_BIT = 0x80  # 'command' bit for normal I2C access
CLEAR_BIT = 0x40  # Clears pending interrupt
WORD_BIT = 0x20  # 1 = read/write word
BLOCK_BIT = 0x10  # 1 = block read/write

CONTROL_POWERON = 0x03
CONTROL_POWEROFF = 0x00

# Register addresses (TSL2561)
REGISTER_CONTROL = 0x00
REGISTER_TIMING = 0x01
REGISTER_THRESHHOLDL_LOW = 0x02
REGISTER_THRESHHOLDL_HIGH = 0x03
REGISTER_THRESHHOLDH_LOW = 0x04
REGISTER_THRESHHOLDH_HIGH = 0x05
REGISTER_INTERRUPT = 0x06
REGISTER_ID = 0x0A
REGISTER_CHAN0_LOW = 0x0C
REGISTER_CHAN1_LOW = 0x0E

# Integration time codes (TSL2561)
# Real integration times are ~13.7 ms, 101 ms, 402 ms.
INTEGRATIONTIME_13MS = 0x00
INTEGRATIONTIME_101MS = 0x01
INTEGRATIONTIME_402MS = 0x02

# Backwards-ish compatibility aliases (if you ever referenced these):
INTEGRATIONTIME_100MS = INTEGRATIONTIME_101MS

# Gain codes
GAIN_1X = 0x00  # low gain
GAIN_16X = 0x10  # high gain

# Keep old-style names for external callers if needed
GAIN_LOW = GAIN_1X
GAIN_HIGH = GAIN_16X

# Fixed-point lux calculation constants (T package)
LUX_SCALE = 14  # scale by 2^14
RATIO_SCALE = 9  # scale ratio by 2^9
CH_SCALE = 10  # scale channel values by 2^10

CHSCALE_TINT0 = 0x7517  # 13.7 ms
CHSCALE_TINT1 = 0x0FE7  # 101 ms

K1T = 0x0040
B1T = 0x01F2
M1T = 0x01BE

K2T = 0x0080
B2T = 0x0214
M2T = 0x02D1

K3T = 0x00C0
B3T = 0x023F
M3T = 0x037B

K4T = 0x0100
B4T = 0x0270
M4T = 0x03FE

K5T = 0x0138
B5T = 0x016F
M5T = 0x01FC

K6T = 0x019A
B6T = 0x00D2
M6T = 0x00FB

K7T = 0x029A
B7T = 0x0018
M7T = 0x0012

K8T = 0x029A
B8T = 0x0000
M8T = 0x0000


class Tsl2561LightSensor(LightSensor):
    """
    Light sensor adapter for the TSL2561 device.

    Matches the existing LightSensor interface and LightSensorResult(full, ir, lux)
    used in HangarBuddy.
    """

    def __init__(
        self,
        logger: SystemLevelLogger,
        i2c_bus: int = 1,
        sensor_address: int = DEFAULT_ADDR,
        integration: int = INTEGRATIONTIME_402MS,
        gain: int = GAIN_LOW,
    ):
        super().__init__(logger)

        try:
            if not local_debug.is_debug():
                self.__logger__.info("Initializing I2C bus for TSL2561")
                self.bus = smbus.SMBus(i2c_bus)

            self.sensor_address = sensor_address
            self.integration_time = integration
            self.gain = gain
            self.enabled = True

            self.__logger__.debug("Configuring TSL2561 timing and gain")
            self.__set_timing__(self.integration_time)
            self.__set_gain__(self.gain)
            self.__disable__()  # start powered down
            self.__logger__.info("TSL2561 light sensor initialized")
        except Exception as ex:
            self.__logger__.error(f"TSL2561: Failed to initialize: {ex}")
            self.enabled = False

    def update(self) -> LightSensorResult | None:
        """
        Updates the sensor reading and returns a LightSensorResult.
        """
        try:
            full, ir = self.__get_full_luminosity__()
            lux = self.__get_calculated_lux__(full, ir)

            self.current_value = LightSensorResult(full, ir, int(lux))
        except Exception as ex:
            self.__logger__.error(f"TSL2561: Failed to read light sensor: {ex}")
            self.current_value = None

        return self.current_value

    # --- Low-level configuration ---

    def __set_timing__(self, integration: int) -> None:
        if not self.enabled:
            return

        self.__is_enable__()
        self.integration_time = integration

        if local_debug.is_debug():
            return

        # TIMING register: lower bits = integration, bit4 = gain (we OR in gain here)
        self.__logger__.debug("TSL2561: Writing TIMING register")
        self.bus.write_byte_data(
            self.sensor_address,
            COMMAND_BIT | REGISTER_TIMING,
            self.integration_time | self.gain,
        )
        self.__disable__()

    def __set_gain__(self, gain: int) -> None:
        if not self.enabled:
            return

        self.__is_enable__()
        self.gain = gain

        if local_debug.is_debug():
            return

        # TIMING register encodes both gain and integration time
        self.__logger__.debug("TSL2561: Writing gain into TIMING register")
        self.bus.write_byte_data(
            self.sensor_address,
            COMMAND_BIT | REGISTER_TIMING,
            self.integration_time | self.gain,
        )
        self.__disable__()

    def __is_enable__(self) -> None:
        """
        Power on the sensor if needed.
        """
        if local_debug.is_debug() or not self.enabled:
            return

        self.__logger__.debug("TSL2561: Enabling sensor (CONTROL=0x03)")
        self.bus.write_byte_data(
            self.sensor_address,
            COMMAND_BIT | REGISTER_CONTROL,
            CONTROL_POWERON,
        )

    def __disable__(self) -> None:
        """
        Power down the sensor.
        """
        if not self.enabled or local_debug.is_debug():
            return

        self.__logger__.debug("TSL2561: Disabling sensor (CONTROL=0x00)")
        self.bus.write_byte_data(
            self.sensor_address,
            COMMAND_BIT | REGISTER_CONTROL,
            CONTROL_POWEROFF,
        )

    # --- Reading and lux computation ---

    def __get_full_luminosity__(self) -> tuple[int, int]:
        """
        Returns (full_spectrum, infrared) raw counts.
        Sensor is assumed to be already powered on & configured.
        """

        if not self.enabled or local_debug.is_debug():
            self.__logger__.warning("TSL2561: Sensor not enabled or in debug mode")
            
            return 0, 0

        # Wait for conversion based on integration time
        if self.integration_time == INTEGRATIONTIME_13MS:
            time.sleep(0.014)
        elif self.integration_time == INTEGRATIONTIME_101MS:
            time.sleep(0.102)
        else:  # 402ms
            time.sleep(0.403)

        # IMPORTANT: use same pattern as the simple test script
        data0 = self.bus.read_i2c_block_data(
            self.sensor_address,
            0x80 | 0x0C,  # COMMAND_BIT | CH0 low
            2,
        )
        data1 = self.bus.read_i2c_block_data(
            self.sensor_address,
            0x80 | 0x0E,  # COMMAND_BIT | CH1 low
            2,
        )

        full = (data0[1] << 8) | data0[0]
        ir = (data1[1] << 8) | data1[0]

        self.__logger__.debug(f"TSL2561 raw: CH0={full}, CH1={ir}")
        return full, ir

    def __get_calculated_lux__(self, ch0: int, ch1: int) -> float:
        """
        Convert raw channel readings to lux using the standard TSL2561
        fixed-point algorithm (T package).
        """
        # Saturation / overflow guard
        if ch0 == 0xFFFF or ch1 == 0xFFFF:
            return 0.0

        # Integration time scaling
        if self.integration_time == INTEGRATIONTIME_13MS:
            ch_scale = CHSCALE_TINT0
        elif self.integration_time == INTEGRATIONTIME_101MS:
            ch_scale = CHSCALE_TINT1
        else:
            ch_scale = 1 << CH_SCALE  # 402ms, no extra scaling

        # Gain scaling: if at 1x, scale up as if measurement were taken at 16x
        if self.gain == GAIN_1X:
            ch_scale <<= 4  # multiply by 16

        # Scale channel values
        channel0 = (ch0 * ch_scale) >> CH_SCALE
        channel1 = (ch1 * ch_scale) >> CH_SCALE

        # Avoid divide-by-zero
        if channel0 == 0:
            return 0.0

        # Compute ratio (channel1 / channel0) in fixed point
        ratio1 = (channel1 << (RATIO_SCALE + 1)) // channel0
        ratio = (ratio1 + 1) >> 1  # round

        # Select appropriate coefficients for T package
        if 0 <= ratio <= K1T:
            b, m = B1T, M1T
        elif ratio <= K2T:
            b, m = B2T, M2T
        elif ratio <= K3T:
            b, m = B3T, M3T
        elif ratio <= K4T:
            b, m = B4T, M4T
        elif ratio <= K5T:
            b, m = B5T, M5T
        elif ratio <= K6T:
            b, m = B6T, M6T
        elif ratio <= K7T:
            b, m = B7T, M7T
        else:
            b, m = B8T, M8T

        temp = (channel0 * b) - (channel1 * m)

        if temp < 0:
            temp = 0

        # Round and strip fractional part
        temp += 1 << (LUX_SCALE - 1)
        lux = temp >> LUX_SCALE

        return float(lux)


if __name__ == "__main__":
    from configuration import Configuration

    logger = SystemLevelLogger(Configuration(), "LightSensorTest_TSL2561")
    tsl = Tsl2561LightSensor(logger)  # initialize with defaults

    result: LightSensorResult | None = tsl.update()
    result_text: str = "ERROR" if result is None else str(result.full_spectrum)
    print(f"Full={result_text}")

    if result is not None:
        print(f"IR={result.infrared}, Lux={result.lux}")
