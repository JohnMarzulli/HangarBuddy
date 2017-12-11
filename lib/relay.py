"""
Module to handle sending commands to the power relay.
"""
import time
import local_debug

if not local_debug.is_debug():
    import RPi.GPIO as GPIO

DEFAULT_RELAY_TYPE = "always_off"
DEFAULT_PIN = 22


class PowerRelay(object):
    """
    Class that controls an AC/DC control relay

    Attributes:
    name: Relay name (IE - Heater, Light, etc.
    GPIO_PIN: (BOARD) GPIO PIN on rasperry pi that
    the AC/D control relay is plugged into
    """

    def __init__(self, name, GPIO_PIN, relay_type=DEFAULT_RELAY_TYPE):
        """
        Creates a relay controller.
        """
        self.name = name
        self.gpio_pin = GPIO_PIN
        self.type = relay_type
        self.expected_status = 0

        # setup GPIO Pins

        if not local_debug.is_debug():
            print "Setting " + str(GPIO_PIN) + " to BOARD/OUT"
            self.expected_status = GPIO.LOW
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(GPIO_PIN, GPIO.OUT)

    def switch_high(self):
        """
        Sets the GPIO pin to HIGH
        """

        if local_debug.is_debug():
            self.expected_status = 1
            return True

        try:
            print "Setting to OUT/HIGH"
            self.expected_status = GPIO.HIGH
            GPIO.output(self.gpio_pin, GPIO.HIGH)
            time.sleep(3)
        except:
            return False
        return True

    def switch_low(self):
        """
        Sets the GPIO pin to LOW
        """

        if local_debug.is_debug():
            self.expected_status = 0
            return True

        try:
            print "Setting to OUT/LOW"
            self.expected_status = GPIO.LOW
            GPIO.output(self.gpio_pin, GPIO.LOW)
            time.sleep(3)
        except:
            return False

        return True

    def get_io_pin_status(self):
        """
        return current status of switch, 0 or 1
        """

        if local_debug.is_debug():
            return self.expected_status

        try:
            return GPIO.input(self.gpio_pin)
        except:
            return 0


##############
# UNIT TESTS #
##############


def test_default():
    '''
    Test that the default is off.
    '''
    power_relay = PowerRelay("Heater", DEFAULT_PIN)
    assert power_relay.get_io_pin_status == 0


def test_on():
    '''
    Test that it can be turned on.
    '''
    power_relay = PowerRelay("Heater", DEFAULT_PIN)
    power_relay.switch_high()
    assert power_relay.get_io_pin_status() == 1


def test_off():
    '''
    Test that it can be turned off.
    '''
    power_relay = PowerRelay("Heater", DEFAULT_PIN)
    power_relay.switch_high()
    power_relay.switch_low()
    assert power_relay.get_io_pin_status() == 1


if __name__ == '__main__':
    import doctest

    print "Starting tests."

    doctest.testmod()

    print "Tests finished"

    TEST_RELAY = PowerRelay("Heater", DEFAULT_PIN)
    TEST_RELAY.switch_high()
    print str(TEST_RELAY.get_io_pin_status())
    time.sleep(10)
    TEST_RELAY.switch_low()
    print str(TEST_RELAY.get_io_pin_status())
