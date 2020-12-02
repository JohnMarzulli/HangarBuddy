""" Module to deal with the SunFounder temperature probe. """

import os
import time

from lib import local_debug

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


def celcius_to_farenheit(
    temp_in_celcius
):
    """
    converts celcius to F.
    Needs a float.
    """
    return ((temp_in_celcius * 9.0) / 5.0) + 32.0


def read_sensor(
    sensor_id
):
    """
    Reads temperature from sensor and prints to stdout
    id is the id of the sensor.

    >>> read_sensor(None)
    >>> read_sensor("1")
    """

    try:
        tfile = open("/sys/bus/w1/devices/{}/w1_slave".format(sensor_id))
        text = tfile.read()
        tfile.close()
        secondline = text.split("\n")[1]
        temperaturedata = secondline.split(" ")[9]
        temperature = float(temperaturedata[2:])
        temperature = temperature / 1000
        print("Sensor: {0} : {1:0.3}C".format(temperature))
        print("Sensor: {0} : {1:0.3}F".format(
            celcius_to_farenheit(temperature)))

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

    if local_debug.is_debug():
        return temperature_probe_values

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
    """ read temperature every second for all connected sensors """
    while True:
        read_sensors()
        time.sleep(1)


# Nothing to cleanup
def destroy():
    """ Tears down the  object. """
    pass


##############
# UNIT TESTS #
##############
if __name__ == '__main__':
    import doctest

    print("Starting tests.")

    doctest.testmod()

    print("Tests finished")

    if local_debug.is_debug():
        print("Debug mode, will not attempt to read sensor")
    else:
        sensor_readings = read_sensors()
        if sensor_readings is not None:
            results_count = len(sensor_readings)
            if results_count > 0:
                print("TEMP, F={}".format(sensor_readings[0]))
            else:
                print("Unable to read temperature sensor")
