"""Module to deal with the SunFounder temperature probe."""

import os
import time

from devices.interfaces.temperature_sensor import (TemperatureSensor,
                                                   celcius_to_farenheit)

# ---------------------------------------------------------------
# Note:
# ds18b20's data pin must be connected to pin7.
#
# The following steps must be taken from the kernel to make sure
# probe is ready for use.
# sudo modprobe w1-gpio
# sudo modprobe w1-therm
#
# You also must modify the /boot/config.txt to include:
# dtoverlay=w1-gpio
# ---------------------------------------------------------------

# Modified from SunFounder's page at
# https://www.sunfounder.com/learn/Sensor-Kit-v1-0-for-Raspberry-Pi/lesson-17-ds18b20-temperature-sensor-sensor-kit-v1-0-for-pi.html


class Ds18b20TempatureSensor(TemperatureSensor):
    def __init__(self):
        super().__init__()
        self.enabled: bool = True
        self.current_value: int | None = None

    def update(self) -> int | None:
        if not self.enabled:
            return None

        temperature_values = read_sensors()
        if temperature_values is not None and len(temperature_values) > 0:
            self.current_value = int(temperature_values[0])
        else:
            self.current_value = None
            self.enabled = False

        return self.current_value


def read_sensor(sensor_id):
    """
    Reads temperature from sensor and prints to stdout
    id is the id of the sensor.

    >>> read_sensor(None)
    >>> read_sensor("1")
    """

    try:
        tfile = open("/sys/bus/w1/devices/" + sensor_id + "/w1_slave")
        text = tfile.read()
        tfile.close()
        secondline = text.split("\n")[1]
        temperaturedata = secondline.split(" ")[9]
        temperature = float(temperaturedata[2:])
        temperature /= 1000
        print(f"Sensor: {sensor_id}" + " : %0.3f C" % temperature)
        print(f"Sensor: {sensor_id}" + " : %0.3f F" % celcius_to_farenheit(temperature))

        return celcius_to_farenheit(temperature)
    except:
        return None


def read_sensors():
    """
    Reads temperature from all sensors found in /sys/bus/w1/devices/
    starting with "28-...

    >>> read_sensors()
    Drivers not available.
    No sensors found! Check connection.
    []
    """
    temperature_probe_values = []

    try:
        for driver_file in os.listdir("/sys/bus/w1/devices/"):
            if driver_file.startswith("28-"):
                try:
                    probe_value = read_sensor(driver_file)

                    if probe_value is not None:
                        temperature_probe_values.append(probe_value)
                except:
                    print("Failed to read sensor")
    except:
        print("Drivers not available.")

    array_length = 0
    if temperature_probe_values is not None:
        array_length = len(temperature_probe_values)

    if array_length == 0:
        print("No sensors found! Check connection.")

    return temperature_probe_values


def loop():
    """read temperature every second for all connected sensors"""
    while True:
        read_sensors()
        time.sleep(1)


# Nothing to cleanup
def destroy():
    """Tears down the  object."""
    pass


##############
# UNIT TESTS #
##############
if __name__ == "__main__":
    import doctest

    print("Starting tests.")

    doctest.testmod()

    print("Tests finished")
