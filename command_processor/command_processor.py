import os
import subprocess
import sys

# Ensure the parent directory is in sys.path so 'managers' can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime, timezone

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
        self.__system_start_time__ = datetime.now(timezone.utc)
        self.last_relay_state = False  # Track last relay state to detect changes
        self.__sensors_manager__: SensorsManager = sensor_manager
        self.__relay_manager__: RelayManager = relay_manager
        self.__gas_safety_manager__: GasSafetyManager = gas_safety_manager

    def process(self, message: str) -> tuple[str | None, bool]:
        """
        Process an incoming text message. Returns a tuple (response_text, relay_should_be_on) if a valid command,
        otherwise returns (None, None).
        """
        if not isinstance(message, str):
            return None, None
        msg = message.strip().upper()
        # Only process if the message matches a valid command

        if self.__is_command__(SHUTDOWN_COMMAND, msg):
            __shutdown__()
            self.last_relay_state = False
            return "System shutting down.", False
        elif self.__is_command__(RESTART_COMMAND, msg):
            self.last_relay_state = False
            __restart__()
            return "System restarting.", False
        elif self.__is_command__(HEATER_ON_COMMAND, msg):
            self.__gas_safety_manager__.update()
            if not self.__gas_safety_manager__.can_turn_on_heater():
                self.last_relay_state = False
                return "Cannot turn on heater: Gas detected!", False
            response_message: str = (
                "Heater turning ON."
                if not self.last_relay_state
                else "Heater is already ON."
            )
            self.last_relay_state = True
            return response_message, True
        elif self.__is_command__(HEATER_OFF_COMMAND, msg):
            response_message: str = (
                "Heater turning OFF."
                if self.last_relay_state
                else "Heater is already OFF."
            )
            self.last_relay_state = False
            return response_message, False
        elif self.__is_command__(UPTIME_COMMAND, msg):
            return self.__get_uptime_text__(), self.last_relay_state
        elif self.__is_command__(FULL_STATUS_COMMAND, msg):
            return self.__get_full_status_text__(), self.last_relay_state
        elif self.__is_command__(TEMPERATURE_COMMAND, msg):
            temp = self.__sensors_manager__.current_temperature_sensor_reading
            return f"Temperature: {temp}", self.last_relay_state
        elif self.__is_command__(LIGHTS_COMMAND, msg):
            light = self.__sensors_manager__.current_light_sensor_reading
            return f"Light: {light}", self.last_relay_state
        elif self.__is_command__(HELP_COMMAND, msg):
            return self.__get_help_text__(), self.last_relay_state
        else:
            return (
                f"Command '{message}' received, unable to process it.",
                self.last_relay_state,
            )

    def __is_command__(self, command: str | None, message: str) -> bool:
        if command is None or not command:
            return False

        return False if message is None else command.lower() in message.lower()

    def __get_uptime_text__(self) -> str:
        time_up = datetime.now(timezone.utc) - self.__system_start_time__
        time_text = text_utils.get_time_text(time_up.total_seconds())
        # For demo: just return system uptime in seconds
        return f"Uptime: {time_text}"

    def __get_full_status_text__(self) -> str:
        # Example: return a summary of sensor states
        temp = self.__sensors_manager__.current_temperature_sensor_reading
        gas = self.__sensors_manager__.current_gas_sensor_reading
        light = self.__sensors_manager__.current_light_sensor_reading

        gas_reading = gas.current_value if gas is not None else "Not available"
        temp_reading = str(temp) if temp is not None else "Not available"
        light_reading = (
            f"{light.lux} LUX"
            if light is not None and light.lux is not None
            else "Not available"
        )

        status_message: str = "Status:\n"
        status_message += f"{self.__get_uptime_text__()}\n"
        status_message += f"Relay: {'ON' if self.last_relay_state else 'OFF'}\n"
        status_message += f"Temp: {temp_reading}\n"
        status_message += f"Gas: {gas_reading}\n"
        status_message += f"Light: {light_reading}"

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
    from logging import Logger

    import configuration

    print("Starting tests.")

    doctest.testmod()
    configuration = configuration.Configuration()
    logger: Logger = Logger("CommandProcessorTest")
    sensors_manager: SensorsManager = SensorsManager(configuration)
    relay_manager: RelayManager = RelayManager(configuration, logger, __send_message__)
    gas_safety_manager: GasSafetyManager = GasSafetyManager(
        sensors_manager, relay_manager, __send_message__
    )
    command_processor: CommandProcessor = CommandProcessor(
        sensors_manager, relay_manager, gas_safety_manager
    )

    assert command_processor is not None, "CommandProcessor should be initialized."

    response: str | None = ""
    is_relay_on: bool = False

    sensors_manager.update()  # Ensure sensors are initialized

    (response, is_relay_on) = command_processor.process("ON")
    assert response == "Heater turning ON.", "Heater should turn ON."
    assert is_relay_on, "Relay should be ON."

    (response, is_relay_on) = command_processor.process("OFF")
    assert response == "Heater turning OFF.", "Heater should turn OFF."
    assert not is_relay_on, "Relay should be OFF."

    (response, is_relay_on) = command_processor.process("STATUS")
    assert response.startswith("Status:"), "Should return full status."  # type: ignore
    assert not is_relay_on, "Relay should be OFF."

    (response, is_relay_on) = command_processor.process("ON")
    assert response == "Heater turning ON.", "Heater should turn ON."
    assert is_relay_on, "Relay should be ON."

    (response, is_relay_on) = command_processor.process("STATUS")
    assert response.startswith("Status:"), "Should return full status."  # type: ignore
    assert is_relay_on, "Relay should be ON."

    (response, is_relay_on) = command_processor.process("HELP")
    assert response.startswith("Valid commands:"), "Should return help text."  # type: ignore

    (response, is_relay_on) = command_processor.process("TEMPERATURE")
    assert response.startswith("Temperature:"), "Should return temperature."  # type: ignore

    (response, is_relay_on) = command_processor.process("LIGHTS")
    assert response.startswith("Light:"), "Should return light level."  # type: ignore

    (response, is_relay_on) = command_processor.process("RESTART")
    assert response == "System restarting.", "Expected 'System restarting.'"

    (response, is_relay_on) = command_processor.process("SHUTDOWN")
    assert response == "System shutting down.", "Expected shutdown message."

    exit()
