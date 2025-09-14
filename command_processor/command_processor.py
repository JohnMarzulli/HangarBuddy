import os
import subprocess
import sys

if __name__ == "__main__":
    # Ensure the parent directory is in sys.path so 'managers' can be imported
    # This is only needed if running the unit tests directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime, timezone

from devices.results.temperature_result import TemperatureResult
from lib import local_debug, text_utils
from managers.gas_safety_manager import GasSafetyManager
from managers.relay_manager import RelayManager
from managers.sensors_manager import SensorsManager

# Commands
HEATER_ON_COMMAND = "ON"
HEATER_OFF_COMMAND = "OFF"
SHUTDOWN_COMMAND = "SHUTDOWN"
RESTART_COMMAND = "RESTART"
FULL_STATUS_COMMAND = "STATUS"
HELP_COMMAND = "HELP"
QUIT_COMMAND = "QUIT"
LIGHTS_COMMAND = "LIGHTS"
TEMPERATURE_COMMAND = "TEMP"
UPTIME_COMMAND = "UPTIME"
GAS_COMMAND = "GAS"
HEATER_COMMAND = "HEATER"

VALID_COMMANDS = {
    FULL_STATUS_COMMAND,
    HELP_COMMAND,
    LIGHTS_COMMAND,
    TEMPERATURE_COMMAND,
    UPTIME_COMMAND,
    HEATER_OFF_COMMAND,
    HEATER_ON_COMMAND,
    SHUTDOWN_COMMAND,
    RESTART_COMMAND,
}


def __restart__():
    """
    Restarts down the Pi.
    """

    if not local_debug.is_debug():
        subprocess.Popen(
            ["sudo shutdown -r 30"],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )


def __shutdown__():
    """
    Shuts down the Pi.
    """

    if not local_debug.is_debug():
        subprocess.Popen(
            ["sudo shutdown -h 30"],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )


# CommandProcessor class: handles incoming text commands, returns response only for valid commands and relay state changes
class CommandProcessor:
    """
    Processes incoming text commands.
    If the command is valid, attempts to execute the command.

    Returns any text (or None) to return back to the sender along with what the state of the relay should be.
    """

    def __init__(
        self,
        sensor_manager: SensorsManager,
        relay_manager: RelayManager,
        gas_safety_manager: GasSafetyManager,
    ):
        """
        Initializes the command processor. This takes authenticated and authorized
        incoming messages and then turns them into actions.

        Args:
            sensor_manager (SensorsManager): The code managing sensor reading.
            relay_manager (RelayManager): The code that manages the electrical relay.
            gas_safety_manager (GasSafetyManager): The code that manages alerts from the gas sensor.
        """
        self.__system_start_time__ = datetime.now(timezone.utc)
        self.__sensors_manager__: SensorsManager = sensor_manager
        self.__relay_manager__: RelayManager = relay_manager
        self.__gas_safety_manager__: GasSafetyManager = gas_safety_manager

    def process(self, message: str) -> str | None:
        """
        Process an incoming text message. Returns a tuple (response_text, relay_should_be_on) if a valid command,
        otherwise returns (None, None).
        """
        if not isinstance(message, str):
            return None
        msg = message.strip().upper()
        # Only process if the message matches a valid command

        if self.__is_command__(SHUTDOWN_COMMAND, msg):
            self.__relay_manager__.turn_off()
            __shutdown__()
            return "System shutting down."
        elif self.__is_command__(RESTART_COMMAND, msg):
            self.__relay_manager__.turn_off()
            __restart__()
            return "System restarting."
        elif self.__is_command__(HEATER_ON_COMMAND, msg):
            if not self.__gas_safety_manager__.can_turn_on_relay():
                return "Cannot turn on heater: Gas detected!"
            response_message: str = (
                "Heater turning ON."
                if not self.__relay_manager__.is_relay_on()
                else f"Heater is already ON. {self.__relay_manager__.get_time_remaining()}"
            )
            self.__relay_manager__.turn_on()
            return response_message
        elif self.__is_command__(HEATER_OFF_COMMAND, msg):
            response_message: str = (
                f"Heater turning OFF with {self.__relay_manager__.get_time_remaining()}"
                if self.__relay_manager__.is_relay_on()
                else "Heater is already OFF."
            )
            self.__relay_manager__.turn_off()
            return response_message
        elif self.__is_command__("IP", msg) or self.__is_command__("ADDRESS", msg):
            return local_debug.get_ip_address()
        elif self.__is_command__(UPTIME_COMMAND, msg):
            return self.__get_uptime_text__()
        elif self.__is_command__(FULL_STATUS_COMMAND, msg):
            return self.get_full_status_text()
        elif self.__is_command__(TEMPERATURE_COMMAND, msg):
            temp = self.__sensors_manager__.current_temperature_sensor_reading
            return f"Temperature: {temp.get_fahrenheit() if temp is not None else 'UNKNOWN'}"
        elif self.__is_command__(LIGHTS_COMMAND, msg):
            light = self.__sensors_manager__.current_light_sensor_reading
            light_text = "UNAVAILABLE" if light is None else light.get_light_level().name
            return f"Light: {light_text}"
        elif self.__is_command__(HELP_COMMAND, msg):
            return self.__get_help_text__()
        else:
            return f"Command '{message}' received, unable to process it."

    def __is_command__(self, command: str | None, message: str) -> bool:
        if command is None or not command:
            return False

        return False if message is None else command.lower() in message.lower()

    def __get_uptime_text__(self) -> str:
        time_up = datetime.now(timezone.utc) - self.__system_start_time__
        return text_utils.get_time_text(time_up.total_seconds())

    def get_short_status_text(self) -> list[str]:
        """
        Returns a short form version of the status.

        Returns:
            list[str]: A set of lines of status.
        """
        status_text: list[str] = ["", ""]

        is_relay_on: bool = self.__relay_manager__.is_relay_on()

        if is_relay_on:
            status_text[0] = "HEATER ON"
            status_text[1] = self.__relay_manager__.get_time_remaining()

            return status_text

        if (
            self.__sensors_manager__.__temperature_sensor__.enabled
            and self.__sensors_manager__.current_temperature_sensor_reading is not None
        ):
            status_text[0] = f"TEMP: {self.__sensors_manager__.current_temperature_sensor_reading.get_fahrenheit()}"
        else:
            status_text[0] = "TEMP: UNAVAILABLE"

        status_text[1] = f"UP: {self.__get_uptime_text__()}"

        return status_text

    def get_full_status_text(self) -> str:
        """
        Returns the full status as a single string.

        Returns:
            str: The current status, as a single string.
        """
        # Example: return a summary of sensor states
        is_relay_on: bool = self.__relay_manager__.is_relay_on()

        time = datetime.now(timezone.utc)
        time_text: str = f"{time:%Y-%m-%d %H:%M:%S}UTC"

        status_message: str = "-= Status =-\n"
        status_message += f"Time: {time_text}\n"
        status_message += f"Relay: {'ON w/' if is_relay_on else 'OFF'} {self.__relay_manager__.get_time_remaining() if is_relay_on else ''}\n"
        status_message = self.__add_temperature_status__(status_message)
        status_message = self.__add_gas_status__(status_message)
        status_message = self.__add_light_status__(status_message)
        status_message += f"Uptime: {self.__get_uptime_text__()}"

        return status_message

    def __add_temperature_status__(self, status_message: str) -> str:
        temp: TemperatureResult | None = self.__sensors_manager__.current_temperature_sensor_reading

        if temp is None:
            return status_message

        temp_reading = f"{str(temp.get_fahrenheit())}" if temp is not None else "UNK"

        status_message += f"Temp: {temp_reading}\n"

        return status_message

    def __add_gas_status__(self, status_message: str) -> str:
        gas = self.__sensors_manager__.current_gas_sensor_reading

        if gas is None:
            return status_message

        status_message += f"Gas: {gas.get_status_text()}\n"

        return status_message

    def __add_light_status__(self, status_message: str) -> str:
        light = self.__sensors_manager__.current_light_sensor_reading

        if light is None:
            return status_message

        light_reading = light.get_light_level().name if light is not None and light.full_spectrum is not None else "UNK"
        status_message += f"Light: {light_reading}\n"

        return status_message

    def __get_help_text__(self) -> str:
        return "Valid commands: " + ", ".join(sorted(VALID_COMMANDS))


#############
# SELF TEST #
#############

if __name__ == "__main__":

    def __send_message__(message: str):
        """
        Sends an alert message.
        """

        # This is a placeholder for the actual send logic.
        # In a real application, this would send the message via SMS, email, etc.
        print(f"Alert: {message}")

    import doctest

    import configuration
    from lib.system_level_logging import SystemLevelLogger

    print("Starting tests.")

    doctest.testmod()
    configuration = configuration.Configuration()
    logger: SystemLevelLogger = SystemLevelLogger(configuration, "CommandProcessorTest")
    sensors_manager: SensorsManager = SensorsManager(configuration, logger)
    relay_manager: RelayManager = RelayManager(configuration, logger, __send_message__)
    gas_safety_manager: GasSafetyManager = GasSafetyManager(sensors_manager, relay_manager, __send_message__)
    command_processor: CommandProcessor = CommandProcessor(sensors_manager, relay_manager, gas_safety_manager)

    assert command_processor is not None, "CommandProcessor should be initialized."

    response: str | None = ""

    sensors_manager.update()  # Ensure sensors are initialized

    response = command_processor.process("ON")
    assert response == "Heater turning ON.", "Heater should turn ON."

    response = command_processor.process("OFF")
    assert response == "Heater is already OFF.", "Heater should turn OFF."

    response = command_processor.process("STATUS")
    assert response.startswith("-= Status =-"), "Should return full status."  # type: ignore

    response = command_processor.process("ON")
    assert response == "Heater turning ON.", "Heater should turn ON."

    response = command_processor.process("STATUS")
    assert response.startswith("-= Status =-"), "Should return full status."  # type: ignore

    response = command_processor.process("HELP")
    assert response.startswith("Valid commands:"), "Should return help text."  # type: ignore

    response = command_processor.process("TEMPERATURE")
    assert response.startswith("Temperature:"), "Should return temperature."  # type: ignore

    response = command_processor.process("LIGHTS")
    assert response.startswith("Light:"), "Should return light level."  # type: ignore

    response = command_processor.process("RESTART")
    assert response == "System restarting.", "Expected 'System restarting.'"

    response = command_processor.process("SHUTDOWN")
    assert response == "System shutting down.", "Expected shutdown message."

    exit()
