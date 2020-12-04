"""
Module to help with tha AdaFruit Fona modules
"""
import datetime
import threading
import time
from multiprocessing import Queue as MPQueue

import serial

from lib import local_debug, utilities
from lib.hangar_buddy_logger import HangarBuddyLogger

if not local_debug.is_debug():
    import RPi.GPIO as GPIO

SECONDS_TO_WAIT_AFTER_SEND = 5
BATTERY_CRITICAL = 40
BATTERY_WARNING = 60
DEFAULT_RESPONSE_READ_TIMEOUT = 5

DEFAULT_RING_INDICATOR_PIN = 18  # (Physical... GPIO24)
DEFAULT_POWER_STATUS_PIN = 16  # (Physical ..GPIO23)
TIMEZONE_OFFSET = 8


class BatteryCondition(object):
    """
    Class to keep the battery state.
    """

    def get_percent_battery(
        self
    ) -> float:
        """
        Returns the remaining percentage of battery.
        """
        return self.battery_percent

    def get_voltage(
        self
    ) -> float:
        """
        Returns the voltage of the battery.
        """
        return self.battery_voltage

    def is_battery_ok(
        self
    ) -> bool:
        """
        Is the battery OK?
        """
        if self.error_state:
            return False

        return self.battery_percent > BATTERY_CRITICAL

    def __init__(
        self,
        command_result: str
    ):
        """
        Initialize.
        """
        self.error_state = False
        results = None

        if command_result is None or len(command_result) < 1:
            self.error_state = True
        else:
            tokens = command_result.split(':')

            if tokens is None or len(tokens) <= 1:
                self.error_state = True
            else:
                results = tokens[1].split(',')

                if results is None or len(results) <= 2:
                    self.error_state = True

        if not self.error_state and results is not None and len(results) > 0:
            self.charge_state = float(results[0])
            self.battery_percent = float(results[1])
            self.battery_voltage = float(results[2]) / 10.0
        else:
            self.charge_state = 0
            self.battery_percent = 0
            self.battery_voltage = 0


class SignalStrength(object):
    """
    Class to hold the signal strength.
    """

    def get_signal_strength(
        self
    ) -> int:
        """
        Returns the signal strength.
        """
        return self.recieved_signal_strength

    def get_bit_error_rate(
        self
    ) -> int:
        """
        Returns the bit error rate from the Fona.
        """
        return self.bit_error_rate

    def classify_strength(
        self
    ) -> str:
        """
        Gets a human meaning to the rssi.
        """
        if self.recieved_signal_strength is None:
            return "Unknown"

        comparisons = [[0, "None"], [4, "Poor"], [
            9, "Marginal"], [14, "OK"], [19, "Good"]]

        for comparison in comparisons:
            if self.recieved_signal_strength <= comparison[0]:
                return comparison[1]

        return "Excellent"

    def __init__(
        self,
        command_result: str
    ):
        """
        Parses the command result.
        """

        self.recieved_signal_strength = 0
        self.bit_error_rate = 0

        try:
            if command_result is not None:
                tokens = command_result.split(':')
                tokens = tokens[1].split(',')
                self.recieved_signal_strength = int(tokens[0])
                self.bit_error_rate = int(tokens[1])
        except:
            self.recieved_signal_strength = 0
            self.bit_error_rate = 0


class SmsMessage(object):
    """
    Class to abstract a text message.
    """

    def get_sender_number(
        self
    ) -> str:
        """
        Gets the sender's number.
        """
        if self.is_message_ok():
            return utilities.get_cleaned_phone_number(self.sender_number)

        return None

    def is_message_ok(
        self
    ) -> bool:
        """
        Is the message valid?
        """
        return not self.error_state

    def minutes_waiting(
        self
    ) -> float:
        """
        How many hours between being sent
        and received.
        """

        return (self.received_time
                - (self.sent_time + datetime.timedelta(hours=TIMEZONE_OFFSET))).days * 24 * 60

    def message_sent_time_utc(
        self
    ) -> datetime:
        """
        When was the message sent in UTC time?
        The SIM card returns time as Local...
        """

        return (self.sent_time + datetime.timedelta(hours=TIMEZONE_OFFSET))

    def __init__(
        self,
        message_header: str,
        message_text: str
    ):
        """
        Create the object.
        """
        self.message_id = None
        self.sender_number = None
        self.message_status = None
        self.message_text = None
        self.received_time = datetime.datetime.now()
        self.sent_time = None

        try:
            metadata_list = message_header.split(",")
            message_id = metadata_list[0]
            message_id = message_id.rpartition(":")[2].strip()
            message_status = metadata_list[1].replace('"', "")
            sender_number = metadata_list[2].replace('"', "")
            message_date = metadata_list[4].replace('"', '')
            date_tokens = message_date.split('/')
            message_time = metadata_list[5].split('-')[0]
            time_tokens = message_time.split(':')

            self.message_id = message_id
            self.sent_time = datetime.datetime.combine(
                datetime.datetime(
                    int("20" + date_tokens[0]), int(date_tokens[1]), int(date_tokens[2])),
                datetime.time(
                    int(time_tokens[0]), int(time_tokens[1]), int(time_tokens[2])))
            self.sender_number = sender_number
            self.message_status = message_status
            self.message_text = message_text
            self.error_state = False
        except:
            self.error_state = True


class Fona(object):
    """
    Class that send messages with an Adafruit Fona
    SERIAL_PORT, BAUDRATE, timeout=.1, rtscts=0
    Attributes:
    unauthorize numbers
    """

    def is_power_on(
        self
    ) -> bool:
        """
        Returns TRUE if the power is on.
        """

        if local_debug.is_debug():
            return True

        if self.__use_gpio_pins__():
            pin_value = GPIO.input(self.power_status_pin)
            self.__logger__.log_info_message(
                "Power... PIN=" + str(self.power_status_pin) + ", VAL=" + str(pin_value))
            return GPIO.input(self.power_status_pin) == GPIO.HIGH

        # If we are not using the power pins
        # then use the existance of the serial
        # modem connection
        return self.serial_connection is not None

    def is_message_waiting(
        self
    ) -> bool:
        """
        Uses the GPIO pin to see if a message is waiting.
        """

        return not self.__message_waiting_queue__.empty()

    def get_carrier(
        self
    ) -> str:
        """
        Returns the carrier.
        """
        return self.__send_command__("AT+COPS?")[:1]

    def get_signal_strength(
        self
    ) -> SignalStrength:
        """
        Returns an object representing the signal strength.
        """
        command_result = self.__send_command__("AT+CSQ")
        if command_result is None or len(command_result) < 2:
            command_result = None
        else:
            command_result = command_result[1]

        return SignalStrength(command_result)

    def get_current_battery_condition(
        self
    ) -> BatteryCondition:
        """
        Returns an object representing the current battery state.
        """
        self.__logger__.log_info_message("Sending CBC command")
        time.sleep(5)
        command_result = self.__send_command__("AT+CBC")

        for result in command_result:
            if "CBC:" in result:
                return BatteryCondition(result)

        return BatteryCondition(None)

    def get_module_name(
        self
    ) -> str:
        """
        Returns the name of the GSM module.
        """
        return self.__send_command__("ATI")[:1]

    def get_sim_card_number(
        self
    ) -> str:
        """
        Returns the id of the sim card.
        """
        return self.__send_command__("AT+CCID")[:1]

    def send_message(
        self,
        message_num: str,
        text: str
    ) -> bool:
        """
        Sends a message to the specified phone numbers.
        """

        cleaned_number = utilities.get_cleaned_phone_number(message_num)

        if cleaned_number is None or text is None:
            return

        self.__logger__.log_info_message("Setting receiving number...")
        self.__set_sms_mode__()
        self.__write_to_fona__('\r\r\n')
        self.__logger__.log_info_message("Wait for resp:")
        if self.__wait_for_command_response__:
            self.__logger__.log_info_message(self.__read_from_fona__(5))
        self.__write_to_fona__('AT+CMGS="' + cleaned_number + '"')
        self.__logger__.log_info_message("Wait for resp 2:")
        self.__wait_for_command_response__()
        self.__logger__.log_info_message(self.__read_from_fona__(5))
        self.__write_to_fona__('\r')
        self.__wait_for_command_response__()
        self.__logger__.log_info_message(self.__read_from_fona__(5))
        self.__logger__.log_info_message(self.__write_to_fona__(text + '\x1a'))
        self.__wait_for_command_response__()

        self.__logger__.log_info_message(self.__read_from_fona__(2))
        self.__logger__.log_info_message("Check phone")

        return True

    def get_messages(
        self
    ) -> list:
        """
        Reads text messages on the SIM card and returns
        a list of messages with three fields: id, num, message.
        """

        self.__logger__.log_info_message("get_messages()")

        if self.serial_connection is None:
            return []

        # put into SMS mode

        self.__set_sms_mode__()
        # get all text messages currently on SIM Card
        responses = self.__send_command__('AT+CMGL="ALL"')

        for resp in responses:
            self.__logger__.log_info_message("Get RESP:{}".format(resp))

        messages = []
        for index in range(0, len(responses)):
            message_header = responses[index]

            if "+CMGL:" in message_header:
                message_text = responses[index + 1]

                self.__logger__.log_info_message(
                    "get_messages:\n\tHEAD={}\n\tTEXT={}".format(
                        message_header,
                        message_text))

                new_message = SmsMessage(
                    message_header,
                    message_text)
                messages.append(new_message)
                index += 1

        self.__clear_messages_waiting_queue__()

        return messages

    def delete_message(
        self,
        message_to_delete: SmsMessage
    ):
        """
        Deletes a message with the given Id.
        """
        self.__send_command__("AT+CMGD=" + str(message_to_delete.message_id))

    def delete_messages(
        self
    ) -> int:
        """ Deletes any messages. """
        messages = self.get_messages()
        messages_deleted = 0
        for message_to_delete in messages:
            messages_deleted += 1
            self.delete_message(message_to_delete)

        if local_debug.is_debug():
            self.__clear_messages_waiting_queue__()

        return messages_deleted

    def simple_terminal(
        self
    ):
        """
        Simple interactive terminal to play with the Fona.
        """

        while True:
            try:
                command = str(input("READY:"))

                if command is None or len(command) == 0:
                    continue

                if command == "quit":
                    return

                response = self.__send_command__(command)

                if response is not None and len(response) > 0:
                    for line in response:
                        self.__logger__.log_info_message(line)
                else:
                    self.__logger__.log_warning_message("No response.")

            except Exception as ex:
                self.__logger__.log_warning_message(
                    "Terminal EX={}".format(ex))

    def __init__(
        self,
        logger: HangarBuddyLogger,
        serial_connection: serial.Serial,
        power_status_pin: int,
        ring_indicator_pin: int
    ):

        self.__logger__ = logger
        self.__modem_access_lock__ = threading.Lock()
        self.serial_connection = serial_connection
        self.power_status_pin = power_status_pin
        self.ring_indicator_pin = ring_indicator_pin

        if self.serial_connection is not None:
            self.serial_connection.flushInput()
            self.serial_connection.flushOutput()

        self.__send_command__("AT")
        # self.send_command("AE0")
        self.__disable_verbose_errors__()
        self.__set_sms_mode__()

        self.__read_from_fona__(10)

        self.__message_waiting_queue__ = MPQueue()
        self.__initialize_gpio_pins__()
        self.__poll_for_messages__()

    def __use_gpio_pins__(
        self
    ) -> bool:
        """
        Returns true if we should use the GPIO pins
        to tell status.
        """

        power_status_available = self.power_status_pin is not None
        ring_indicator_available = self.ring_indicator_pin is not None

        return power_status_available and ring_indicator_available

    def __initialize_gpio_pins__(
        self
    ) -> bool:
        """
        Gets the Fona ready to be interacted with by the GPIO board.
        """

        if not self.__use_gpio_pins__():
            self.__logger__.log_info_message("Skipping GPIO init.")
            return False

        self.__logger__.log_info_message("Setting GPIO input modes")

        # Set the RI pin to pulse low when
        # a text message is received
        self.__send_command__("AT+CFGRI=1")

        if not local_debug.is_debug():
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(self.ring_indicator_pin, GPIO.IN)
            GPIO.setup(self.power_status_pin, GPIO.IN)
            GPIO.add_event_detect(
                self.ring_indicator_pin,
                GPIO.RISING,
                self.__ring_indicator_pulsed__)

        return True

    def __poll_for_messages__(
        self
    ):
        """
        Check for messages every 60 seconds.
        """
        self.__message_waiting_queue__.put("POLL")
        threading.Timer(60, self.__poll_for_messages__).start()

    def __ring_indicator_pulsed__(
        self,
        io_pin: int
    ):
        """
        The RI went from LOW to HIGH.
        That means a message.
        """
        self.__message_waiting_queue__.put("RI:" + str(io_pin))

    def __write_to_fona__(
        self,
        text: str
    ) -> int:
        """
        Write text to the Fona in a safe manner.
        """
        self.__logger__.log_info_message("Checking connection")
        if self.serial_connection is None:
            return "NO CON"

        self.__logger__.log_info_message("Writing to serial")
        num_bytes_written = self.serial_connection.write(str.encode(text))
        self.serial_connection.flush()

        self.__logger__.log_info_message("Checking return")
        self.__logger__.log_info_message(
            "Wrote {}, expected {}".format(
                num_bytes_written,
                len(text)))

        self.__wait_for_command_response__()

        self.__logger__.log_info_message(
            "Done with wait_for_command_repsonse()")

        return num_bytes_written

    def __read_from_fona__(
        self,
        response_timeout=2
    ):
        """
        Read back from the Fona in a safe manner.
        """
        read_buffer = []
        start_time = time.time()

        if self.serial_connection is None:
            return "NOCON"

        self.__logger__.log_info_message("   starting read")
        while self.serial_connection.inWaiting() > 0:
            read_buffer += self.serial_connection.read(1)
            time_elapsed = time.time() - start_time
            if time_elapsed > response_timeout:
                self.__logger__.log_warning_message("TIMEOUT")
                break

        response = ''
        for char in read_buffer:
            response += chr(char)

        self.__logger__.log_info_message("   done")
        self.__logger__.log_info_message("BUFFER:{}".format(response))

        return response

    def __send_command__(
        self,
        com: str
    ) -> list:
        """ send a command to the modem """
        self.__modem_access_lock__.acquire(True)
        modem_reponses = []

        try:
            command = '${}\r\n'.format(com)

            if self.serial_connection is not None:
                self.__logger__.log_info_message("CMD: {}".format(command))
                self.serial_connection.write(str.encode(command))
                time.sleep(2)

            # "Starting read/wait"
            while self.serial_connection is not None and self.serial_connection.inWaiting() > 0:
                raw_response = self.serial_connection.readline().decode()
                self.__logger__.log_info_message(
                    "RSP: {}".format(raw_response))
                modem_reponses.append(raw_response)

            self.__modem_access_lock__.release()

            return [msg.strip().replace("\r\r\n", "") for msg in modem_reponses][1:]
        except Exception as ex:
            self.__logger__.log_info_message("COMMAND EX={}".format(ex))
            self.__modem_access_lock__.release()

        return []

    def __disable_verbose_errors__(
        self
    ):
        """
        Disables verbose errors.
        Required for AT+CMGS to work.
        """
        return self.__send_command__("AT+CMEE=0")

    def __enable_verbose_errors__(
        self
    ):
        """
        Enables trouble shooting errors.
        """
        return self.__send_command__("AT+CMEE=2")

    def __set_sms_mode__(
        self
    ):
        """
        Puts the card into SMS mode.
        """
        return self.__send_command__("AT+CMGF=1")

    def __read_until_text__(
        self,
        text
    ):
        """
        Reads from the fona until the text is found.
        """

        read_text = ""
        start_time = time.time()

        while text not in read_text:
            self.__wait_for_command_response__()
            read_text += self.__read_from_fona__(2)
            elapsed_time = time.time() - start_time

            if elapsed_time > 10:
                self.__logger__.log_warning_message("TIMEOUT")
                break

        return read_text

    def __wait_for_command_response__(
        self
    ):
        """
        Waits until the command has a response
        """

        if self.serial_connection is None:
            return False

        start_time = time.time()
        while time.time() - start_time < 2 and self.serial_connection.inWaiting() < 1:
            time.sleep(0.5)

        return self.serial_connection.inWaiting() > 0

    def __clear_messages_waiting_queue__(
        self
    ):
        """
        Clears the queue that tells us if we should check for
        messages.
        """

        events_cleared = 0
        while not self.__message_waiting_queue__.empty():
            self.__logger__.log_info_message("Clearing queue.")
            event = self.__message_waiting_queue__.get()
            events_cleared += 1
            self.__logger__.log_info_message("Q:" + event)

        return events_cleared
