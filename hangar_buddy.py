# !python

"""
Main entry code for HangarBuddy
"""


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

import command_processor.command_processor as command_processor
import configuration
import sys
from communication.meshtastic_serial import MeshtasticSerial
from managers.gas_safety_manager import GasSafetyManager
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


def send_message(message: str) -> bool:
    """
    Sends an alert message.
    """

    is_one_message_sent: bool = False

    for recipient in CONFIGURATION.allowed_senders:
        print(f"SENDING: {recipient}: `{message}`") #LOGGER.info
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


if __name__ == "__main__":
    heater = RelayManager(CONFIGURATION, LOGGER, send_message)
    gas_safety_manager: GasSafetyManager = GasSafetyManager(
        SENSORS_MANAGER, heater, send_message
    )
    command_processor = command_processor.CommandProcessor(
        SENSORS_MANAGER, heater, gas_safety_manager
    )

    send_message("Starting HangarBuddy...")

    print(f"Connected to {MESSAGING.long_name}/{MESSAGING.device_id}")

    while True:
        SENSORS_MANAGER.update()
        MESSAGING.service()
        gas_safety_manager.update()
        messages = MESSAGING.get_message_queue()

        for message in messages:
            LOGGER.info(f"Received message: {message}")

            message_to:str = message["toId"] 
            message_from:str = message["fromId"]
            message_from = message_from.lstrip('!')

            if message_to != MESSAGING.device_id:
                LOGGER.warning(
                    f"Message not intended for this device: {message_to} != {MESSAGING.device_id}"
                )
                continue

            is_from_known_sender = message_from in CONFIGURATION.allowed_senders

            if not is_from_known_sender:
                known_senders_text: str = ",".join(CONFIGURATION.allowed_senders)
                send_message(f"Unknown sender `{message_from}`, known: {known_senders_text}")

                continue

            message_text = (
                message.get("decoded", {}).get("payload", b"").decode("utf-8")
            )
            (response, is_relay_on) = command_processor.process(message_text)

            is_relay_on &= not gas_safety_manager.is_gas_detected()

            if is_relay_on is None:
                LOGGER.warning(
                    "Value of `is_relay_on` is None. Probable bug, skipping heater control."
                )
            elif is_relay_on:
                heater.turn_on()
                LOGGER.info("Heater turned ON.")
            else:
                heater.turn_off()
                LOGGER.info("Heater turned OFF.")

            if response is not None and len(response) > 0:
                send_message(response)
                LOGGER.info(f"Response sent: {response}")
