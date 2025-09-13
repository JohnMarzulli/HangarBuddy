"""Module to deal with the SunFounder temperature probe."""

import os
import pathlib

if __name__ == "__main__":
    import sys
    import os

    # Ensure the parent directory is in sys.path so 'managers' can be imported
    # This is only needed if running the unit tests directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from devices.interfaces.temperature_sensor import (
    TemperatureSensor,
    celsius_to_fahrenheit,
)

# ---------------------------------------------------------------
# Note:
# ds18b20's data pin must be connected to pin7.
#
# You will need to enabled "1 wire" in raspi-config
#
# If you are still having problems:
#
# Verify /boot/firmware/config.txt to includes:
# dtoverlay=w1-gpio
#
# sudo modprobe w1-gpio
# sudo modprobe w1-therm
#
# ---------------------------------------------------------------

# Modified from SunFounder's page at
# https://www.sunfounder.com/learn/Sensor-Kit-v1-0-for-Raspberry-Pi/lesson-17-ds18b20-temperature-sensor-sensor-kit-v1-0-for-pi.html


def __read_sensor__(sensor_id: str) -> float | None:
    """
    Reads temperature from sensor and prints to stdout
    id is the id of the sensor.

    >>> __read_sensor__(None)
    >>> __read_sensor__("1")
    """

    try:
        text = pathlib.Path(f"/sys/bus/w1/devices/{sensor_id}/w1_slave").read_text()
        secondline = text.split("\n")[1]
        temperaturedata = secondline.split(" ")[9]
        temperature = float(temperaturedata[2:])
        temperature /= 1000
        print(f"Sensor: {sensor_id}" + " : %0.3f C" % temperature)
        print(
            f"Sensor: {sensor_id}" + " : %0.3f F" % celsius_to_fahrenheit(temperature)
        )

        return celsius_to_fahrenheit(temperature)
    except Exception:
        return None


def __read_sensors__() -> list[float]:
    """
    Reads temperature from all sensors found in /sys/bus/w1/devices/
    starting with "28-...
    """
    temperature_probe_values: list[float] = []
    driver_files: list[str] = []

    try:
        driver_files = os.listdir("/sys/bus/w1/devices/")
    except Exception:
        print("Drivers not available.")
        return []

    for driver_file in driver_files:
        if not driver_file.startswith("28-"):
            pass

        try:
            probe_value = __read_sensor__(driver_file)

            if probe_value is not None:
                temperature_probe_values.append(probe_value)
        except Exception:
            print("Failed to read sensor")

    return temperature_probe_values


class Ds18b20TemperatureSensor(TemperatureSensor):
    """
    Attempts to connect to a DS18B20 sensor.

    If the sensor is not present, then `enabled` will be set to
    false causing all sensor interactions to be bypassed.

    Args:
        TemperatureSensor (_type_): _description_
    """

    def __init__(self):
        """
        Attempt to connect to the temperature sensor.
        """
        super().__init__()
        self.enabled: bool = True
        self.current_value: int | None = None

    def update(self) -> int | None:
        """
        Services the sensor. May cause a new reading to be taken.

        Returns:
            int | None: The latest temperature reading in Fahrenheit.
        """
        if not self.enabled:
            return None

        temperature_values = __read_sensors__()
        if temperature_values is not None and len(temperature_values) > 0:
            self.current_value = int(temperature_values[0])
        else:
            self.current_value = None
            self.enabled = False

        return self.current_value


##############
# UNIT TESTS #
##############
if __name__ == "__main__":
    import doctest

    print("Starting tests.")

    doctest.testmod()

    sensor: Ds18b20TemperatureSensor = Ds18b20TemperatureSensor()
    temp: int = sensor.update()

    print(f"{temp}F")

    print("Tests finished")
