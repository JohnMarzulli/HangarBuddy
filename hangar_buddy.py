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

import logging
import logging.handlers
import sys
from datetime import datetime, timezone
from time import sleep

import configuration
from command_processor.command_processor import CommandProcessor
from communication.meshcore_serial import MeshcoreSerial
from communication.meshtastic_serial import MeshtasticSerial
from communication.message_send_request import MessageSendRequest
from communication.recieved_message import RecievedMessage
from devices.interfaces.messaging_device import MessagingDevice
from displays.sf_1602_lcd import Sf1602Display
from lib import local_debug
from managers.gas_safety_manager import GasSafetyManager
from managers.light_manager import LightManager
from managers.relay_manager import RelayManager
from managers.sensors_manager import SensorsManager

LOGGER = logging.getLogger("heater")
LOGGER.setLevel(logging.INFO)


def __get_messaging_device__(
    config: configuration.Configuration,
) -> MessagingDevice:
    if config.device_type.lower() == "meshtastic":
        return MeshtasticSerial()
    elif config.device_type.lower() == "meshcore":
        return MeshcoreSerial()

    raise RuntimeError(f"Unknown device type: {config.device_type}")


CONFIGURATION = configuration.Configuration()
MESSAGING: MessagingDevice = __get_messaging_device__(CONFIGURATION)
SENSORS_MANAGER = SensorsManager(CONFIGURATION)
HANDLER = logging.handlers.RotatingFileHandler(
    CONFIGURATION.log_filename, maxBytes=1048576, backupCount=3, encoding="utf-8"
)
HANDLER.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(message)s"))
LOGGER.addHandler(HANDLER)


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

    LOGGER.info(log_message)


def log_message_recieved(message: RecievedMessage):
    lines = message.text.split("\n")

    log_message: str = "RECIEVED\n"
    log_message += f"    FROM: {message.sender}\n"
    log_message += f"    AT: {__get_time_text__()}\n"
    log_message += "    ```\n"
    for line in lines:
        log_message += f"    {line.strip()}\n"
    log_message += "    ```"

    LOGGER.info(log_message)


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
            LOGGER.error(f"Error sending message to {recipient}, EX={ex}")

    if not is_one_message_sent:
        LOGGER.error("ERROR trying to send message to any authorized recievers")

    return is_one_message_sent


def is_radio_connected() -> bool:
    """
    Checks if the radio is connected.
    """

    try:
        return MESSAGING.__is_connected__()
    except Exception as e:
        LOGGER.error(f"Error checking radio connection: {e}")
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
        LOGGER.error("Error decoding message payload")

        return ""


def process_messages(command_processor: CommandProcessor):
    messages = MESSAGING.get_incoming_messages()

    for message in messages:
        if not is_for_this_node(message.recipient):
            continue

        if not is_from_known_sender(message.sender):
            known_senders_text: str = ",".join(CONFIGURATION.allowed_senders)
            unknown_sender_message: str = (
                f"Unknown sender `{message.sender}`, known: {known_senders_text}"
            )

            send_message(unknown_sender_message)

            continue

        log_message_recieved(message)
        response = command_processor.process(message.text)

        if response is not None and len(response) > 0:
            send_message(response)
            LOGGER.info(f"Response sent: {response}")


def prevent_pc_from_sleeping():
    if sys.platform == "win32":
        import ctypes

        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED
        )


def __get_display__() -> Sf1602Display | None:
    if local_debug.is_debug():
        return None

    try:
        return Sf1602Display()
    except Exception:
        return None


def __update_display__(
    display: Sf1602Display | None,
    command_processor: CommandProcessor,
):
    if display is None:
        return

    status: list[str] = command_processor.get_short_status_text()

    display.write(0, 0, status[0])
    display.write(0, 1, status[1])


# TODO: Make display event & message driven
# TODO: Send messages to cycle display
# TODO: Make temp result have both F & C
# TODO: See if there is a way to improve the accuracy of the temp sensor
# TODO: Log the right things... validate logging
# TODO: Command to return hop count & route


async def __connect_messaging_device__():
    while not MESSAGING.__is_connected__():
        sleep(1)
        print("Connecting to device...")
        await MESSAGING.service()


async def main():
    prevent_pc_from_sleeping()

    await __connect_messaging_device__()

    display = __get_display__()
    heater = RelayManager(CONFIGURATION, LOGGER, send_message)
    light_manager: LightManager = LightManager("Hangar", SENSORS_MANAGER, send_message)
    gas_safety_manager: GasSafetyManager = GasSafetyManager(
        SENSORS_MANAGER, heater, send_message
    )
    command_processor = CommandProcessor(SENSORS_MANAGER, heater, gas_safety_manager)

    LOGGER.info("Starting HangarBuddy...")
    LOGGER.info(f"IP:{local_debug.get_ip_address()}")

    send_message("Starting HangarBuddy...")
    send_message(command_processor.get_full_status_text())

    LOGGER.info(f"Connected to {MESSAGING.device_name}/{MESSAGING.device_id}")

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
