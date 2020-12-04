from lib import temp_probe, gas_sensor, light_sensor, local_debug


def test_temp_probe():
    print("Testing temperature sensor")

    sensor_readings = temp_probe.read_sensors()

    results_count = len(sensor_readings)
    if results_count > 0:
        print("TEMP, F={}".format(sensor_readings[0]))
    else:
        print("Unable to read temperature sensor")


def test_light_sensor():
    print("Testing light sensor")

    sensor = light_sensor.LightSensor()  # initialize
    result = light_sensor.LightSensorResult(sensor)
    print("Lux={}".format(result.lux))


def test_gas_sensor():
    print("Testing gas sensor")

    sensor = gas_sensor.GasSensor()
    is_gas_detected = sensor.update()

    print("LVL:{0}, {1}".format(
        is_gas_detected.current_value,
        is_gas_detected.is_gas_detected))


print("Starting sensor tests:")

test_temp_probe()
test_light_sensor()
test_gas_sensor()
