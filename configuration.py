""" Module to abstract and hide configuration. """

# encoding: UTF-8

import os
from configparser import ConfigParser
from pathlib import Path

import lib.local_debug as local_debug

# read in configuration settings


def __get_resolved_filepath__(
    filename: str
) -> str:
    """
    Try to resolve a filename to the proper full path.
    Used to help resolve relative path issues and issues with the working path when started from crontab.

    Arguments:
        filename {str} -- The filename (optionally with a partial path) to resolve to a fully qualified file path.

    Returns:
        str -- The fully resolved filepath
    """

    print("Attempting to resolve '{}'".format(filename))
    print("__file__='{}'".format(__file__))

    try:
        raw_path = filename

        if './' in filename:
            raw_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                filename.replace("./", ""))
        else:
            print("Attempting to expand user pathing.")
            raw_path = Path(os.path.expanduser(filename))

            raw_path = str(raw_path)

        print("Before normalization path='{}'".format(raw_path))

        normalized_path = os.path.normpath(raw_path)

        print("Normalized path='{}'".format(raw_path))

        return normalized_path
    except Exception as ex:
        print(
            "__get_resolved_filepath__:Attempted to resolve. got EX={}".format(ex))
        return None


def get_config_file_location():
    """
    Get the location of the configuration file.

    >>> get_config_file_location()
    './HangarBuddy.config'
    """

    return __get_resolved_filepath__('./HangarBuddy.config')


class Configuration(object):
    """
    Object to handle configuration of the HangarBuddy.
    """

    def get_log_directory(self):
        """ returns the location of the logfile to use. """

        if local_debug.is_debug():
            return self.__config_parser__.get('SETTINGS', 'DEBUGGING_LOGFILE_DIRECTORY')

        return self.__config_parser__.get('SETTINGS', 'LOGFILE_DIRECTORY')

    def __init__(self):
        print("SETTINGS{}".format(get_config_file_location()))

        self.__config_parser__ = ConfigParser()
        self.__config_parser__.read(get_config_file_location())
        self.cell_serial_port = self.__config_parser__.get(
            'SETTINGS',
            'SERIAL_PORT')
        self.cell_baud_rate = self.__config_parser__.get(
            'SETTINGS',
            'BAUDRATE')
        self.cell_ring_indicator_pin = self.__config_parser__.getint(
            'SETTINGS',
            'RING_INDICATOR_PIN')
        self.cell_power_status_pin = self.__config_parser__.getint(
            'SETTINGS',
            'POWER_STATUS_PIN')
        self.heater_pin = self.__config_parser__.getint(
            'SETTINGS',
            'HEATER_PIN')
        self.is_mq2_enabled = self.__config_parser__.getboolean(
            'SETTINGS',
            'MQ2')
        self.is_temp_probe_enabled = self.__config_parser__.getboolean(
            'SETTINGS',
            'TEMP')
        self.is_light_sensor_enabled = self.__config_parser__.getboolean(
            'SETTINGS',
            'LIGHT_SENSOR')
        self.hangar_dark = self.__config_parser__.getint(
            'SETTINGS',
            'HANGAR_DARK')
        self.hangar_dim = self.__config_parser__.getint(
            'SETTINGS',
            'HANGAR_DIM')
        self.hangar_lit = self.__config_parser__.getint(
            'SETTINGS',
            'HANGAR_LIT')
        self.allowed_phone_numbers = self.__config_parser__.get(
            'SETTINGS',
            'ALLOWED_PHONE_NUMBERS')
        self.allowed_phone_numbers = self.allowed_phone_numbers.split(',')
        self.max_minutes_to_run = self.__config_parser__.getint(
            'SETTINGS',
            'MAX_HEATER_TIME')
        self.log_filename = self.get_log_directory() + "hangar_buddy.log"
        self.oldest_message = self.__config_parser__.getint(
            'SETTINGS',
            'OLDEST_MESSAGE_TO_PROCESS')
        self.utc_offset = self.__config_parser__.getint(
            'SETTINGS',
            'UTC_OFFSET')

        try:
            self.test_mode = self.__config_parser__.getboolean(
                'SETTINGS',
                'TEST_MODE')
        except:
            self.test_mode = False


##################
### UNIT TESTS ###
##################

def test_configuration():
    """ Test that the configuration is valid. """
    config = Configuration()

    assert config.allowed_phone_numbers is not None
    assert config.allowed_phone_numbers.count > 0
    assert config.cell_baud_rate == '9600'
    assert config.cell_serial_port is not None
    assert config.heater_pin is not None
    assert config.heater_pin >= 1
    assert config.heater_pin < 32
    assert config.is_mq2_enabled is not None
    assert config.is_temp_probe_enabled is not None
    assert config.log_filename is not None
    assert config.max_minutes_to_run == 60


if __name__ == '__main__':
    import doctest

    print("Starting tests.")

    doctest.testmod()

    print("Tests finished")
