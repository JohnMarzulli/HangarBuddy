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
from communication.meshtastic_serial import MeshtasticSerial
from displays.sf_1602_lcd import Sf1602Display
from lib import local_debug
from managers.gas_safety_manager import GasSafetyManager
from managers.light_manager import LightManager
from managers.relay_manager import RelayManager
from managers.sensors_manager import SensorsManager

CONFIGURATION = configuration.Configuration()

LOGGER = logging.getLogger("heater")
LOGGER.setLevel(logging.INFO)
MESSAGING: MeshtasticSerial = MeshtasticSerial()
SENSORS_MANAGER = SensorsManager(CONFIGURATION)
HANDLER = logging.handlers.RotatingFileHandler(
    CONFIGURATION.log_filename, maxBytes=1048576, backupCount=3
)
HANDLER.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(message)s"))
LOGGER.addHandler(HANDLER)


def log_message_sent(recipient: str, message: str):
    lines = message.split("\n")

    print("SENDING")
    print(f"    TO: {recipient}")
    print(f"    AT: {datetime.now(timezone.utc)}")
    print("    ```")
    for line in lines:
        print(f"    {line.strip()}")
    print("    ```")


def log_message_recieved(sender: str, message: str):
    lines = message.split("\n")

    print("RECIEVED")
    print(f"    FROM: {sender.lstrip('!')}")
    print(f"    AT: {datetime.now(timezone.utc)}")
    print("    ```")
    for line in lines:
        print(f"    {line.strip()}")
    print("    ```")


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
            MESSAGING.send(recipient, message)
            is_one_message_sent = True
        except Exception as ex:
            print(f"While sending to {recipient}, EX={ex}")

    if not is_one_message_sent:
        print("ERROR trying to send message to any authorized recievers")

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


def is_for_this_node(message: dict) -> bool:
    message_to: str = message["toId"]
    message_to = message_to.strip()

    return message_to == MESSAGING.device_id


def is_from_known_sender(message: dict) -> bool:
    message_from: str = message["fromId"]
    message_from = message_from.lstrip("!")

    return message_from in CONFIGURATION.allowed_senders


def get_message_text(message: dict) -> str:
    try:
        return message["decoded"]["payload"].decode("utf-8")
    except Exception:
        print("Error decoding message payload")
        return ""


def process_messages(command_processor: CommandProcessor):
    messages = MESSAGING.get_message_queue()

    for message in messages:
        sender: str = message["fromId"]

        if not is_for_this_node(message):
            continue

        if not is_from_known_sender(message):
            known_senders_text: str = ",".join(CONFIGURATION.allowed_senders)
            unknown_sender_message: str = (
                f"Unknown sender `{sender}`, known: {known_senders_text}"
            )

            send_message(unknown_sender_message)

            continue

        message_text = get_message_text(message)
        log_message_recieved(sender, message_text)
        response = command_processor.process(message_text)

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


if __name__ == "__main__":
    prevent_pc_from_sleeping()

    display = __get_display__()
    heater = RelayManager(CONFIGURATION, LOGGER, send_message)
    light_manager: LightManager = LightManager(SENSORS_MANAGER, send_message)
    gas_safety_manager: GasSafetyManager = GasSafetyManager(
        SENSORS_MANAGER, heater, send_message
    )
    command_processor = CommandProcessor(SENSORS_MANAGER, heater, gas_safety_manager)

    send_message("Starting HangarBuddy...")
    send_message(command_processor.get_full_status_text())

    print(f"Connected to {MESSAGING.long_name}/{MESSAGING.device_id}")

    while True:
        SENSORS_MANAGER.update()
        MESSAGING.service()
        light_manager.update()
        gas_safety_manager.update()
        heater.update()
        process_messages(command_processor)
        __update_display__(display, command_processor)

        sleep(1)
