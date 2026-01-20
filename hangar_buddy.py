#!/usr/bin/python

"""
Main entry code for HangarBuddy
"""


# Make sure you run:
# `source /home/pi/src/HangarBuddy/venv/bin/activate`
# before attempting to install packages or run.

#
#
# Inspired by Mari DeGrazia's piWarmer
# http://az4n6.blogspot.com/
# arizona4n6@gmail.com
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You can view the GNU General Public License at <http://www.gnu.org/licenses/>
#
# Written for Python 3.x
# You will need to "pip3 install meshtastic"
#
# Includes provisions for the basic logic to be run
# for development\testing under Windows or Mac
#
# NOTE: To have this start automatically
#
# 1. sudo vim /etc/rc.local
# 2. Add the following line:
#    cd /home/pi/HangarBuddy
# 3. (OPTIONAL) To have the device update its code automatically
#    when connected to wifi, add the following line
#    at the bottom of the file:
#    /bin/sh /home/pi/HangarBuddy/update.sh
# 4. Add the following line at the bottom of the file:
#    NOTE: if this should be below the optional auto-update line
#    python /home/pi/HangarBuddy/hangar_buddy.py &

import sys
from datetime import datetime, timedelta, timezone
from time import sleep

import configuration
from command_processor.command_processor import CommandProcessor
from communication.meshcore_serial import MeshcoreSerial
from communication.meshtastic_serial import MeshtasticSerial
from communication.message_send_request import MessageSendRequest
from communication.received_message import ReceivedMessage
from communication.sim800c_serial import Sim800cSerial
from communication.test_message_device import TestMessagingDevice
from devices.displays.sf_1602_lcd import Sf1602Display
from devices.interfaces.display_device import DisplayDevice
from devices.interfaces.messaging_device import MessagingDevice
from devices.mocks.console_display import ConsoleDisplay
from display.display_manager import DisplayManager
from display.display_message import DisplayMessage
from display.priority import Priority
from lib import local_debug
from lib.system_level_logging import SystemLevelLogger
from lib.time_correction import TIME_CORRECTION
from managers.gas_safety_manager import GasSafetyManager
from managers.light_manager import LightManager
from managers.relay_manager import RelayManager
from managers.sensors_manager import SensorsManager

CONFIGURATION = configuration.Configuration()

DISPLAY_MANAGER: DisplayManager = DisplayManager(ConsoleDisplay() if local_debug.is_debug() else Sf1602Display())

HANGAR_BUDDY_LOGGER: SystemLevelLogger = SystemLevelLogger(CONFIGURATION, "HangarBuddy")
MESSAGE_LOGGER: SystemLevelLogger = SystemLevelLogger(CONFIGURATION, "Messages")
MESSAGING_DEVICE_LOGGER: SystemLevelLogger = SystemLevelLogger(
    CONFIGURATION,
    "MessagingDevice",
)
RELAY_LOGGER: SystemLevelLogger = SystemLevelLogger(CONFIGURATION, "Relay")
SENSORS_LOGGER: SystemLevelLogger = SystemLevelLogger(CONFIGURATION, "Sensors")
SENSORS_MANAGER = SensorsManager(CONFIGURATION, SENSORS_LOGGER)
MESSAGE_HISTORY: list[ReceivedMessage] = []


def __get_messaging_device__(
    config: configuration.Configuration,
) -> MessagingDevice:
    if config.device_type.lower() == "meshtastic":
        MESSAGING_DEVICE_LOGGER.info("Using Meshtastic messaging device")

        return MeshtasticSerial(MESSAGING_DEVICE_LOGGER)
    elif config.device_type.lower() == "meshcore":
        MESSAGING_DEVICE_LOGGER.info("Using Meshcore messaging device")

        return MeshcoreSerial(MESSAGING_DEVICE_LOGGER)
    elif config.device_type.lower() == "sim800c":
        MESSAGING_DEVICE_LOGGER.info("Using SIM800C messaging device")

        return Sim800cSerial(MESSAGING_DEVICE_LOGGER)
    elif config.device_type.lower() == "test":
        MESSAGING_DEVICE_LOGGER.info("Using Loopback/Test messaging device")

        return TestMessagingDevice(MESSAGING_DEVICE_LOGGER)

    raise RuntimeError(f"Unknown device type: {config.device_type}")


MESSAGING: MessagingDevice = __get_messaging_device__(CONFIGURATION)


def __get_time_text__() -> str:
    time = TIME_CORRECTION.get_time()
    return f"{time:%Y-%m-%d %H:%M:%S}UTC"


def log_message_sent(recipient: str, message: str):
    lines = message.split("\n")

    log_message: str = "SENDING\n"
    log_message += f"    TO: {recipient}\n"
    log_message += f"    AT: {__get_time_text__()}\n"
    log_message += "    ```\n"
    for line in lines:
        log_message += f"    {line.strip()}\n"
    log_message += "    ```"

    MESSAGE_LOGGER.info(log_message)


def log_message_received(message: ReceivedMessage):
    lines = message.text.split("\n")

    log_message: str = "RECEIVED\n"
    log_message += f"    FROM: {message.sender}\n"
    log_message += f"    AT: {__get_time_text__()}\n"
    log_message += "    ```\n"
    for line in lines:
        log_message += f"    {line.strip()}\n"
    log_message += "    ```"

    MESSAGE_LOGGER.info(log_message)


def send_mesage(recipient: str, message: str) -> bool:
    """
    Sends an alert message.
    """

    log_message_sent(recipient, message)

    # Here you can add more logic to send the alert, e.g., via email or SMS.
    # For now, it just logs the message.
    try:
        MESSAGING.send(MessageSendRequest(recipient, message))

        return True
    except Exception as ex:
        HANGAR_BUDDY_LOGGER.error(f"Error sending message to {recipient}, EX={ex}")

        return False


def send_message_to_all(message: str) -> bool:
    """
    Sends an alert message.
    """

    DISPLAY_MANAGER.show(
        DisplayMessage(
            message,
            priority=Priority.HIGH,
            ttl=timedelta(seconds=60),
            min_display_time=timedelta(seconds=15),
        )
    )

    is_one_message_sent: bool = False

    for recipient in CONFIGURATION.allowed_senders:
        is_sent: bool = send_mesage(recipient, message)
        is_one_message_sent = is_one_message_sent or is_sent

    if not is_one_message_sent:
        HANGAR_BUDDY_LOGGER.error("ERROR trying to send message to any authorized receivers")

    return is_one_message_sent


def is_for_this_node(recipient: str) -> bool:
    message_to = recipient.strip()

    return message_to == MESSAGING.device_id


def is_from_known_sender(sender: str) -> bool:
    return sender in CONFIGURATION.allowed_senders


def get_message_text(message: dict) -> str:
    try:
        return message["decoded"]["payload"].decode("utf-8")
    except Exception:
        HANGAR_BUDDY_LOGGER.error("Error decoding message payload")

        return ""


def __get_ascii_only__(text: str) -> str:
    return "".join(char for char in text if char.isascii())


def process_messages(command_processor: CommandProcessor, display_manager: DisplayManager):
    messages = MESSAGING.get_incoming_messages()

    for message in messages:
        if not is_for_this_node(message.recipient):
            continue

        if not is_from_known_sender(message.sender):
            send_mesage(message.sender, "BLOCKED")

            display_manager.show(
                DisplayMessage(
                    f"UNAUTH MSG FROM:\n{__get_ascii_only__(message.sender)}",
                    priority=Priority.HIGH,
                    ttl=timedelta(seconds=60),
                    min_display_time=timedelta(seconds=15),
                )
            )

            known_senders_text: str = ",".join(CONFIGURATION.allowed_senders)
            unknown_sender_message: str = f"Unknown sender `{message.sender}`, known: {known_senders_text}"

            send_message_to_all(unknown_sender_message)

            continue

        display_manager.show(
            DisplayMessage(
                f"{__get_ascii_only__(message.sender)}\n{__get_ascii_only__(message.text)}",
                priority=Priority.HIGH,
                ttl=timedelta(seconds=60),
                min_display_time=timedelta(seconds=15),
            )
        )

        MESSAGE_HISTORY.append(message)
        log_message_received(message)
        response = command_processor.process(message.text, MESSAGE_HISTORY)

        if response is not None and len(response) > 0:
            send_message_to_all(response)
            HANGAR_BUDDY_LOGGER.info(f"Response sent: {response}")


def prevent_pc_from_sleeping():
    if sys.platform == "win32":
        import ctypes

        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)


def __update_display__(
    display_manager: DisplayManager,
    command_processor: CommandProcessor,
):
    status: list[str] = command_processor.get_short_status_text()
    display_text = f"{status[0]}\n{status[1]}"
    info_request: DisplayMessage = DisplayMessage(
        display_text,
        priority=Priority.LOW,
        ttl=timedelta(seconds=5),
        min_display_time=timedelta(seconds=0.5),
    )

    display_manager.show(info_request)


# TODO: See if there is a way to improve the accuracy of the temp sensor
# TODO: Command to return hop count & route


async def __connect_messaging_device__() -> bool:
    # This is intentionally not using the time correction system
    # since it is only used for relative timekeeping
    # and not anything user facing
    start_time = datetime.now(timezone.utc)
    end_time = start_time + timedelta(minutes=5)

    while datetime.now(timezone.utc) < end_time:
        if MESSAGING.__is_connected__():
            return True

        sleep(5)
        HANGAR_BUDDY_LOGGER.info("Connecting to device...")
        await MESSAGING.service()

    return False


async def main():
    prevent_pc_from_sleeping()

    DISPLAY_MANAGER.show_now("Starting...")

    is_connected: bool = await __connect_messaging_device__()

    if not is_connected:
        HANGAR_BUDDY_LOGGER.error("Unable to connect to messaging device")
        DISPLAY_MANAGER.show_now("ERROR:\nNo Msg Device")

        return

    heater = RelayManager(CONFIGURATION, RELAY_LOGGER, send_message_to_all)
    light_manager: LightManager = LightManager("Hangar", SENSORS_MANAGER, send_message_to_all)
    gas_safety_manager: GasSafetyManager = GasSafetyManager(SENSORS_MANAGER, heater, send_message_to_all)
    command_processor = CommandProcessor(SENSORS_MANAGER, heater, gas_safety_manager)

    DISPLAY_MANAGER.show_now("Initializing...")

    HANGAR_BUDDY_LOGGER.info("Starting HangarBuddy...")
    HANGAR_BUDDY_LOGGER.info(f"IP:{local_debug.get_ip_address()}")

    send_message_to_all("Starting HangarBuddy...")
    send_message_to_all(command_processor.get_full_status_text())

    HANGAR_BUDDY_LOGGER.info(f"Connected to {MESSAGING.device_name}/{MESSAGING.device_id}")

    while True:
        SENSORS_MANAGER.update()
        await MESSAGING.service()
        light_manager.update()
        gas_safety_manager.update()
        heater.update()
        process_messages(command_processor, DISPLAY_MANAGER)
        __update_display__(DISPLAY_MANAGER, command_processor)
        DISPLAY_MANAGER.update()

        sleep(0.5)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
