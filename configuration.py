"""Module to abstract and hide configuration."""

# encoding: UTF-8

import os.path

from configparser import ConfigParser

import lib.local_debug as local_debug

# read in configuration settings


def get_config_file_location():
    """
    Get the location of the configuration file.

    >>> get_config_file_location()
    './HangarBuddy.config'
    """

    paths = ["./HangarBuddy.config", "../HangarBuddy.config", "../../HangarBuddy.config"]

    for path in paths:
        if os.path.exists(path):
            return path

    raise RuntimeError("Unable to find configuration file")


class Configuration(object):
    """
    Object to handle configuration of the HangarBuddy.
    """

    def get_log_directory(self):
        """returns the location of the logfile to use."""

        return self.__config_parser__.get("SETTINGS", "LOGFILE_DIRECTORY")

    def __init__(self):
        file_path = get_config_file_location()
        print(f"SETTINGS:{file_path}")

        self.__config_parser__: ConfigParser = ConfigParser()
        self.__config_parser__.read(file_path, encoding="utf-8")

        self.device_type: str = self.__config_parser__.get("SETTINGS", "DEVICE_TYPE")
        self.relay_pin: int = self.__config_parser__.getint("SETTINGS", "HEATER_PIN")
        self.is_mq2_enabled: bool = self.__config_parser__.getboolean("SETTINGS", "MQ2")
        self.is_temp_probe_enabled: bool = self.__config_parser__.getboolean("SETTINGS", "TEMP")
        self.is_light_sensor_enabled: bool = self.__config_parser__.getboolean("SETTINGS", "LIGHT_SENSOR")
        self.hangar_dark: int = self.__config_parser__.getint("SETTINGS", "HANGAR_DARK")
        self.hangar_dim: int = self.__config_parser__.getint("SETTINGS", "HANGAR_DIM")
        self.hangar_lit: int = self.__config_parser__.getint("SETTINGS", "HANGAR_LIT")
        raw_senders_entry: str = self.__config_parser__.get("SETTINGS", "ALLOWED_SENDERS")
        raw_senders_list: list[str] = raw_senders_entry.split(",")
        self.allowed_senders: list[str] = [sender.strip() for sender in raw_senders_list if sender.strip()]
        self.max_minutes_to_run: int = self.__config_parser__.getint("SETTINGS", "MAX_HEATER_TIME")
        self.log_filename: str = f"{self.get_log_directory()}hangar_buddy.log"
        self.max_message_age: int = self.__config_parser__.getint("SETTINGS", "OLDEST_MESSAGE_TO_PROCESS")
        self.utc_offset = self.__config_parser__.getint("SETTINGS", "UTC_OFFSET")

        try:
            self.test_mode: bool = self.__config_parser__.getboolean("SETTINGS", "TEST_MODE")
        except:
            self.test_mode: bool = False


##################
### UNIT TESTS ###
##################


def test_configuration():
    """Test that the configuration is valid."""
    config = Configuration()

    assert config.allowed_senders is not None
    assert len(config.allowed_senders) > 0
    assert config.relay_pin is not None
    assert config.relay_pin >= 1
    assert config.relay_pin < 32
    assert config.is_mq2_enabled is not None
    assert config.is_temp_probe_enabled is not None
    assert config.log_filename is not None
    assert config.max_minutes_to_run == 60


if __name__ == "__main__":
    import doctest

    print("Starting tests.")

    doctest.testmod()

    print("Tests finished")
