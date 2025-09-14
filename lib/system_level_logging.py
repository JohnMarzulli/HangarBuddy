import logging
import logging.handlers
import os

from configuration import Configuration


class SystemLevelLogger:
    def __init__(self, configuration: Configuration, system_name: str):
        partial_file_name: str = f"{system_name.replace(" ", "")}.log"
        log_dir: str = configuration.get_log_directory()
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        full_log_path: str = os.path.join(log_dir, partial_file_name)
        self.__logger__: logging.Logger = logging.getLogger(system_name)
        self.__logger__.setLevel(logging.INFO)
        self.__handler__: logging.handlers.RotatingFileHandler = logging.handlers.RotatingFileHandler(
            full_log_path,
            maxBytes=1048576,
            backupCount=3,
            encoding="utf-8",
        )
        self.__handler__.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(message)s"))
        self.__logger__.addHandler(self.__handler__)

    def info(self, message: str):
        self.__logger__.info(message)

    def warning(self, message: str):
        self.__logger__.warning(message)

    def error(self, message: str):
        self.__logger__.error(message)

    def debug(self, message: str):
        self.__logger__.debug(message)
