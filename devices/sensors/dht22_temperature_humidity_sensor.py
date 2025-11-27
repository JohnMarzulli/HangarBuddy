import os
import time
import traceback
from dataclasses import dataclass
from typing import Optional

if __name__ == "__main__":
    import os
    import sys

    # Ensure the parent directory is in sys.path so 'managers' can be imported
    # This is only needed if running the unit tests directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import lib.local_debug as local_debug
from devices.interfaces.temperature_sensor import TemperatureSensor
from devices.results.temperature_result import TemperatureResult
from lib.system_level_logging import SystemLevelLogger

if local_debug.is_debug():
    raise RuntimeError("DHT22 sensor not supported on PC.")

import lgpio


@dataclass
class DHT22Reading:
    temperature_c: float
    humidity: float


class DHT22Error(Exception):
    """Base class for DHT22 errors."""

    pass


class DHT22:
    """
    Minimal DHT22 reader using lgpio.

    - gpio: BCM pin number (e.g. 4 for GPIO4).
    - chip: gpiochip index (0 on Pi 4 with standard kernel).
    """

    def __init__(self, gpio: int, chip: int = 0):
        self.gpio = gpio
        self.chip = chip
        self._h = lgpio.gpiochip_open(chip)
        self._last_read_ns: int = 0

    # --------- helpers ---------

    def close(self) -> None:
        try:
            lgpio.gpiochip_close(self._h)
        except Exception:
            pass

    def _sleep_us(self, us: int) -> None:
        """Busy-wait sleep in microseconds."""
        target = time.perf_counter_ns() + us * 1000
        while time.perf_counter_ns() < target:
            pass

    def _wait_for_level(self, level: int, timeout_us: int) -> None:
        """
        Wait until pin == level or timeout, else raise DHT22Error.
        """
        start = time.perf_counter_ns()
        while True:
            v = lgpio.gpio_read(self._h, self.gpio)
            if v == level:
                return
            if (time.perf_counter_ns() - start) // 1000 > timeout_us:
                raise DHT22Error(f"Timeout waiting for level {level}")

    # --------- public API ---------

    def read(self, retries: int = 3, min_interval_s: float = 2.0) -> DHT22Reading:
        """
        Read temperature & humidity.

        - Will respect the DHT22 minimum interval between reads.
        - Will retry up to `retries` times before raising DHT22Error.
        """
        now = time.perf_counter_ns()
        elapsed_s = (now - self._last_read_ns) / 1_000_000_000
        if self._last_read_ns != 0 and elapsed_s < min_interval_s:
            # Sensor spec: ~2s between reads
            time.sleep(min_interval_s - elapsed_s)

        last_error: Optional[Exception] = None

        for _ in range(retries):
            try:
                reading = self._read_once()
                self._last_read_ns = time.perf_counter_ns()
                return reading
            except DHT22Error as ex:
                last_error = ex
                # Short pause between retries
                time.sleep(0.2)

        raise DHT22Error(f"Failed to read DHT22 after {retries} attempts: {last_error}")

    # --------- one-shot low-level read ---------

    def _read_once(self) -> DHT22Reading:
        """
        Perform one low-level transaction with the sensor.
        Raises DHT22Error on failure.
        """
        h = self._h
        gpio = self.gpio

        # 1) Start signal: output low for >= 1ms (use 18ms like the datasheet),
        #    then high for 20-40µs.
        lgpio.gpio_claim_output(h, gpio)
        lgpio.gpio_write(h, gpio, 1)
        time.sleep(0.05)  # 50ms idle high
        lgpio.gpio_write(h, gpio, 0)
        time.sleep(0.018)  # 18ms low
        lgpio.gpio_write(h, gpio, 1)
        self._sleep_us(40)  # 40µs high

        # Switch to input to watch the sensor's response.
        lgpio.gpio_free(h, gpio)
        lgpio.gpio_claim_input(h, gpio)

        # 2) Sensor response:
        #    - 80µs low, then 80µs high.
        self._wait_for_level(0, timeout_us=100)  # should go low
        self._wait_for_level(1, timeout_us=100)  # then high
        self._wait_for_level(0, timeout_us=100)  # then low again to start first bit

        # 3) Read 40 bits: each bit is:
        #    - 50µs low
        #    - high for 26-28µs (0) or ~70µs (1)
        bits = []
        for _ in range(40):
            # Wait for the start of the bit's high pulse
            self._wait_for_level(1, timeout_us=80)

            start = time.perf_counter_ns()
            # Stay in this loop while the line is high
            while lgpio.gpio_read(h, gpio) == 1:
                if (time.perf_counter_ns() - start) // 1000 > 120:
                    # Pulse too long, something went wrong
                    raise DHT22Error("Bit pulse too long")
            pulse_us = (time.perf_counter_ns() - start) // 1000

            # Heuristic threshold: >50µs => 1, else 0
            bits.append(1 if pulse_us > 50 else 0)

            # After high pulse, sensor pulls low again for next bit; wait for low.
            self._wait_for_level(0, timeout_us=80)

        # Reclaim as output high (idle) to be nice
        lgpio.gpio_free(h, gpio)
        lgpio.gpio_claim_output(h, gpio)
        lgpio.gpio_write(h, gpio, 1)

        # 4) Convert 40 bits -> 5 bytes
        if len(bits) != 40:
            raise DHT22Error(f"Expected 40 bits, got {len(bits)}")

        data = []
        for i in range(5):
            byte = 0
            for j in range(8):
                byte = (byte << 1) | bits[i * 8 + j]
            data.append(byte)

        hum_hi, hum_lo, temp_hi, temp_lo, checksum = data

        # 5) Verify checksum
        if ((hum_hi + hum_lo + temp_hi + temp_lo) & 0xFF) != checksum:
            raise DHT22Error(f"Checksum mismatch: {data}")

        # 6) Decode values
        humidity = ((hum_hi << 8) | hum_lo) / 10.0

        raw_temp = (temp_hi << 8) | temp_lo
        if raw_temp & 0x8000:  # negative
            raw_temp = raw_temp & 0x7FFF
            temperature_c = -raw_temp / 10.0
        else:
            temperature_c = raw_temp / 10.0

        return DHT22Reading(temperature_c=temperature_c, humidity=humidity)


DHT_GPIO = 4


class Dh22TemperatureHumiditySensor(TemperatureSensor):
    """
    Attempts to connect to a DS18B20 sensor.

    If the sensor is not present, then `enabled` will be set to
    false causing all sensor interactions to be bypassed.

    Args:
        TemperatureSensor (_type_): _description_
    """

    def __init__(self, logger: SystemLevelLogger):
        """
        Attempt to connect to the temperature sensor.
        """
        super().__init__(logger)
        self.enabled: bool = True
        self.current_value: TemperatureResult | None = None
        self.__sensor__: DHT22 = DHT22(DHT_GPIO)

    def update(self) -> TemperatureResult | None:
        """
        Services the sensor. May cause a new reading to be taken.

        Returns:
            TemperatureResult | None: The latest temperature reading, which contains both Celsius and Fahrenheit values.
        """
        if not self.enabled:
            return None

        value = self.__read_sensor__()

        if value is not None:
            self.current_value = value

        # if self.current_value is None:
        #    self.enabled = False

        return self.current_value

    def __read_sensor__(self) -> TemperatureResult | None:
        """
        Reads temperature from sensor and prints to stdout
        id is the id of the sensor.
        """

        if not self.enabled:
            return None

        try:
            sensor_reading = self.__sensor__.read()
            temperature_c = float(sensor_reading.temperature_c)
            humidity = float(sensor_reading.humidity)

            print(f"Sensor: {humidity}%" + ", %01f C" % temperature_c)

            return TemperatureResult(temperature_c)
        except DHT22Error as ex:
            # Expected timing/checksum issues – log and retry next update.
            print(f"DHT22 read failed: {ex}")
            traceback.print_exc()
            return None
        except Exception as ex:
            # Unexpected fatal error – disable the sensor.
            print(f"DHT22 fatal error: {ex}")
            traceback.print_exc()
            self.enabled = False
            return None


##############
# UNIT TESTS #
##############
if __name__ == "__main__":
    import doctest

    from configuration import Configuration

    print("Starting tests.")

    doctest.testmod()

    sensor: Dh22TemperatureHumiditySensor = Dh22TemperatureHumiditySensor(
        SystemLevelLogger(Configuration(), "TempSensorTest")
    )
    temp: TemperatureResult | None = sensor.update()

    if temp is not None:
        print(f"{temp.get_celsius()}/{temp.get_fahrenheit()}")
    else:
        raise RuntimeError("Unable to get a reading from the sensor")

    print("Tests finished")
