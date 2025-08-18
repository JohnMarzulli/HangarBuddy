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
# You will need to "pip install pyserial"
#
# Includes provisions for the basic logic to be run
# for development\testing under Windows or Mac
#
# NOTE: To have this start automatically
#
# 1. sudo vim /etc/rc.local
# 2. Add the following line:
#    cd /home/pi/piWarmer
# 3. (OPTIONAL) To have the device update its code automatically
#    when connected to wifi, add the following line
#    at the bottom of the file:
#    /bin/sh /home/pi/piWarmer/update.sh
# 4. Add the following line at the bottom of the file:
#    NOTE: if this should be below the optional auto-update line
#    python /home/pi/piWarmer/hangar_buddy.py &

import logging
import logging.handlers

import command_processor.command_processor as command_processor
import configuration
from communication.meshtastic_serial import MeshtasticSerial
from managers.gas_safety_manager import GasSafetyManager
from managers.relay_manager import RelayManager
from managers.sensors_manager import SensorsManager

CONFIGURATION = configuration.Configuration()

LOGGER = logging.getLogger("heater")
LOGGER.setLevel(logging.INFO)
MODEM = MeshtasticSerial()
SENSORS_MANAGER = SensorsManager(CONFIGURATION)
HANDLER = logging.handlers.RotatingFileHandler(
    CONFIGURATION.log_filename, maxBytes=1048576, backupCount=3
)
HANDLER.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(message)s"))
LOGGER.addHandler(HANDLER)


def send_message(message: str):
    """
    Sends an alert message.
    """

    for recipient in CONFIGURATION.allowed_phone_numbers:
        LOGGER.warning(f"{recipient}: `{message}`")
        # Here you can add more logic to send the alert, e.g., via email or SMS.
        # For now, it just logs the message.
        MODEM.send(recipient, message)


if __name__ == "__main__":
    heater = RelayManager(CONFIGURATION, LOGGER, send_message)
    gas_safety_manager: GasSafetyManager = GasSafetyManager(
        SENSORS_MANAGER, heater, send_message
    )
    command_processor = command_processor.CommandProcessor(
        SENSORS_MANAGER, heater, gas_safety_manager
    )

    send_message("Starting HangarBuddy...")

    while True:
        SENSORS_MANAGER.update()
        messages = MODEM.get_message_queue()
        for message in messages:
            LOGGER.info(f"Received message: {message}")
            response, is_relay_on = command_processor.process(message)

            is_relay_on &= not gas_safety_manager.is_gas_present()

            if is_relay_on is None:
                LOGGER.info("No relay action required.")
            elif is_relay_on:
                heater.turn_on()
                LOGGER.info("Heater turned ON.")
            else:
                heater.turn_off()
                LOGGER.info("Heater turned OFF.")
