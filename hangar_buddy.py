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
from datetime import datetime, timezone
from time import sleep

import configuration
from command_processor.command_processor import CommandProcessor
from communication.meshcore_serial import MeshcoreSerial
from communication.meshtastic_serial import MeshtasticSerial
from communication.message_send_request import MessageSendRequest
from communication.received_message import ReceivedMessage
from communication.sim800c_serial import Sim800cSerial
from devices.interfaces.messaging_device import MessagingDevice
from displays.console_display import ConsoleDisplay
from displays.display_device import DisplayDevice
from displays.sf_1602_lcd import Sf1602Display
from lib import local_debug
from lib.system_level_logging import SystemLevelLogger
from managers.gas_safety_manager import GasSafetyManager
from managers.light_manager import LightManager
from managers.relay_manager import RelayManager
from managers.sensors_manager import SensorsManager

CONFIGURATION = configuration.Configuration()

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
        return MeshtasticSerial(MESSAGING_DEVICE_LOGGER)
    elif config.device_type.lower() == "meshcore":
        return MeshcoreSerial(MESSAGING_DEVICE_LOGGER)
    elif config.device_type.lower() == "sim800c":
        return Sim800cSerial(MESSAGING_DEVICE_LOGGER)

    raise RuntimeError(f"Unknown device type: {config.device_type}")


MESSAGING: MessagingDevice = __get_messaging_device__(CONFIGURATION)


def __get_time_text__() -> str:
    time = datetime.now(timezone.utc)
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


def send_message(message: str) -> bool:
    """
    Sends an alert message.
    """

    is_one_message_sent: bool = False

    for recipient in CONFIGURATION.allowed_senders:
        log_message_sent(recipient, message)
        # Here you can add more logic to send the alert, e.g., via email or SMS.
        # For now, it just logs the message.
        try:
            MESSAGING.send(MessageSendRequest(recipient, message))
            is_one_message_sent = True
        except Exception as ex:
            HANGAR_BUDDY_LOGGER.error(f"Error sending message to {recipient}, EX={ex}")

    if not is_one_message_sent:
        HANGAR_BUDDY_LOGGER.error("ERROR trying to send message to any authorized receivers")

    return is_one_message_sent


def is_radio_connected() -> bool:
    """
    Checks if the radio is connected.
    """

    try:
        return MESSAGING.__is_connected__()
    except Exception as e:
        HANGAR_BUDDY_LOGGER.error(f"Error checking radio connection: {e}")
        return False


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


def process_messages(command_processor: CommandProcessor):
    messages = MESSAGING.get_incoming_messages()

    for message in messages:
        if not is_for_this_node(message.recipient):
            continue

        if not is_from_known_sender(message.sender):
            known_senders_text: str = ",".join(CONFIGURATION.allowed_senders)
            unknown_sender_message: str = f"Unknown sender `{message.sender}`, known: {known_senders_text}"

            send_message(unknown_sender_message)

            continue

        MESSAGE_HISTORY.append(message)
        log_message_received(message)
        response = command_processor.process(message.text, MESSAGE_HISTORY)

        if response is not None and len(response) > 0:
            send_message(response)
            HANGAR_BUDDY_LOGGER.info(f"Response sent: {response}")


def prevent_pc_from_sleeping():
    if sys.platform == "win32":
        import ctypes

        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)


def __get_display__() -> DisplayDevice | None:
    if local_debug.is_debug():
        return ConsoleDisplay()

    try:
        return Sf1602Display()
    except Exception:
        return None


def __update_display__(
    display: DisplayDevice | None,
    command_processor: CommandProcessor,
):
    if display is None:
        return

    status: list[str] = command_processor.get_short_status_text()

    display.write(0, 0, status[0])
    display.write(0, 1, status[1])


# TODO: Make display event & message driven
# TODO: Send messages to cycle display
# TODO: See if there is a way to improve the accuracy of the temp sensor
# TODO: Command to return hop count & route


async def __connect_messaging_device__():
    while not MESSAGING.__is_connected__():
        sleep(1)
        HANGAR_BUDDY_LOGGER.info("Connecting to device...")
        await MESSAGING.service()


async def main():
    prevent_pc_from_sleeping()

    await __connect_messaging_device__()

    display = __get_display__()
    heater = RelayManager(CONFIGURATION, RELAY_LOGGER, send_message)
    light_manager: LightManager = LightManager("Hangar", SENSORS_MANAGER, send_message)
    gas_safety_manager: GasSafetyManager = GasSafetyManager(SENSORS_MANAGER, heater, send_message)
    command_processor = CommandProcessor(SENSORS_MANAGER, heater, gas_safety_manager)

    HANGAR_BUDDY_LOGGER.info("Starting HangarBuddy...")
    HANGAR_BUDDY_LOGGER.info(f"IP:{local_debug.get_ip_address()}")

    send_message("Starting HangarBuddy...")
    send_message(command_processor.get_full_status_text())

    HANGAR_BUDDY_LOGGER.info(f"Connected to {MESSAGING.device_name}/{MESSAGING.device_id}")

    while True:
        SENSORS_MANAGER.update()
        await MESSAGING.service()
        light_manager.update()
        gas_safety_manager.update()
        heater.update()
        process_messages(command_processor)
        __update_display__(display, command_processor)

        sleep(1)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
