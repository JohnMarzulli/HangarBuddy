import os

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

import adafruit_dht
import board

# ---------------------------------------------------------------
# Note:
# The DH22's data pin must be connected to pin7.
##
# ---------------------------------------------------------------

DHT_DEVICE = adafruit_dht.DHT22(board.D4)


def __read_sensor__() -> TemperatureResult | None:
    """
    Reads temperature from sensor and prints to stdout
    id is the id of the sensor.
    """

    try:
        temperature_c = dht_device.temperature
        humidity = dht_device.humidity

        temperature = float(temperature_c)
        print(f"Sensor: {humidity}%" + ", %0.3f C" % temperature)

        return TemperatureResult(temperature)
    except Exception:
        return None


def __read_sensors__() -> list[TemperatureResult]:
    """
    Reads temperature from all sensors found in /sys/bus/w1/devices/
    starting with "28-...
    """
    temperature_probe_values: list[TemperatureResult] = []

    try:
        probe_value = __read_sensor__()

        if probe_value is not None:
            temperature_probe_values.append(probe_value)
    except Exception:
        print("Failed to read sensor")

    return temperature_probe_values


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

    def update(self) -> TemperatureResult | None:
        """
        Services the sensor. May cause a new reading to be taken.

        Returns:
            TemperatureResult | None: The latest temperature reading, which contains both Celsius and Fahrenheit values.
        """
        if not self.enabled:
            return None

        temperature_values = __read_sensors__()
        if temperature_values is not None and len(temperature_values) > 0:
            self.current_value = temperature_values[0]
        else:
            self.current_value = None
            self.enabled = False

        return self.current_value


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
