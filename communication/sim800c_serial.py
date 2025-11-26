import time
from datetime import datetime, timedelta

import serial
import serial.tools.list_ports

if __name__ == "__main__":
    import os
    import sys

    # Ensure the parent directory is in sys.path so 'managers' can be imported
    # This is only needed if running the unit tests directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from communication.message_send_request import MessageSendRequest
from communication.received_message import ReceivedMessage
from devices.interfaces.messaging_device import MessagingDevice
from lib.system_level_logging import SystemLevelLogger

# https://www.elecrow.com/wiki/image/2/20/SIM800_Series_AT_Command_Manual_V1.09.pdf?srsltid=AfmBOorZohmwcixSI37rtmu4aL2oasNb9AZt0CuhKHM0dHmVATGFX2oW


def wait_for_response(connection: serial.Serial, max_wait_seconds: float = 4.0) -> bool:
    start_time: datetime = datetime.now()
    time_to_end: datetime = start_time + timedelta(seconds=max_wait_seconds)

    is_time_remaining: bool = True
    is_input_waiting: bool = False

    while is_time_remaining and not is_input_waiting:

        time.sleep(0.1)
        is_input_waiting = connection.in_waiting > 0
        is_time_remaining = datetime.now() < time_to_end

    time_stopped: datetime = datetime.now()

    print(f"Started:{start_time}")
    print(f"Desired:{time_to_end}")
    print(f"Actual:{ time_stopped}")
    print(f"is_input_waiting:{is_input_waiting}")

    return is_input_waiting


def get_command_response(connection: serial.Serial, command: str) -> str:
    response_lines: list[str] = []
    print(f"COMMAND:\"{command}\"".replace("\r", "\\r").replace("\n", "\\n"))
    connection.reset_input_buffer()
    connection.write(command.encode("ascii"))
    connection.flush()

    while wait_for_response(connection):
        read = connection.readline()
        print(f"READ:{read}")
        response = ""
        if read is not None:
            response = read.decode().strip()
        response_lines.append(response)

    return "\n".join(response_lines)


def get_modem_connection() -> serial.Serial | None:
    """
    Close the connection to the Meshtastic device.
    """
    all_ports = serial.tools.list_ports.comports()
    ports = [port.device for port in all_ports]

    for port in ports:
        try:
            connection: serial.Serial = serial.Serial(
                port=port,
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1,
            )
            command_response: str = get_command_response(connection, "ATE0\r\n")
            if "AT" in command_response or "800" in command_response or "OK" in command_response:
                return connection

        except Exception as ex:
            print(f"Attempted to connect to {port}, got EX={ex}")

    raise ConnectionError("Unable to connect to a USB/Cell Modem")


class Sim800cSerial(MessagingDevice):
    def __init__(self, logger: SystemLevelLogger):
        super().__init__(logger)

        self.__connection__: serial.Serial | None = None

    def __is_device_allocated__(self) -> bool:
        return self.__connection__ is not None

    async def __receive_message__(self) -> bool:
        if self.__connection__ is None:
            return False

        # put into SMS mode

        self.__set_sms_mode__()
        # get all text messages currently on SIM Card
        response: str = self.__send_command__('AT+CMGL="ALL"')

        messages: list[str] = response.split("+CMGL")[1:]

        for message in messages:
            # TODO - split up message bodies
            incoming_message: ReceivedMessage = ReceivedMessage(message, message, message)
            self.__receiving_queue__.append(incoming_message)

        return len(messages) > 0

    async def __send_single_message__(self, message_to_send: MessageSendRequest) -> bool:
        if self.__connection__ is None:
            return False

        self.__set_sms_mode__()
        self.__logger__.info(self.__send_exact_command__("\r\n"))
        self.__logger__.info(self.__send_command__(f'AT+CMGS="{message_to_send.recipient}"'))
        self.__logger__.info(self.__send_exact_command__("\r"))
        self.__logger__.info(self.__send_command__(f"{message_to_send.text}\x1a"))

        return True

    def __is_connected__(self) -> bool:
        """
        Check if the device is connected.
        """

        return self.__is_device_allocated__()

    async def __reconnect__(self):
        """
        Close the connection to the Meshtastic device.
        """
        self.__connection__ = get_modem_connection()
        self.device_name: str = self.__send_command__("ATI").splitlines()[1].strip()
        self.device_id: str = self.__send_command__("AT+CGSN").splitlines()[1].strip()
        self.__logger__.info(f"Connected to: {self.device_name}/{self.device_id}")

    def get_carrier(self):
        """
        Returns the carrier.
        """
        return self.__send_command__("AT+COPS?")

    def __set_sms_mode__(self):
        """
        Puts the card into SMS mode.
        """
        return self.__send_command__("AT+CMGF=1")

    def __send_exact_command__(self, command: str) -> str:
        """send a command to the modem"""

        if self.__connection__ is None:
            return ""

        return get_command_response(self.__connection__, command)

    def __send_command__(self, command: str, add_eol: bool = True) -> str:
        """send a command to the modem"""

        if self.__connection__ is None:
            return ""

        command_to_send: str = command.strip()

        if add_eol:
            command_to_send += "\r\n"

        return get_command_response(self.__connection__, command_to_send)

    def __wait_for_command_response__(self):
        """
        Waits until the command has a response
        """

        if self.__connection__ is None:
            return False

        start_time = time.time()
        while time.time() - start_time < 2 and self.__connection__.in_waiting < 1:
            time.sleep(0.5)

        return self.__connection__.in_waiting > 0


if __name__ == "__main__":
    import asyncio

    from configuration import Configuration
    from devices.interfaces.messaging_device import test_loop

    logger: SystemLevelLogger = SystemLevelLogger(Configuration(), "CellPhoneModemTester")

    cellphone_device: Sim800cSerial = Sim800cSerial(logger)
    # Make sure that we get a connection
    asyncio.run(cellphone_device.service())
    carrier_response: str = cellphone_device.get_carrier()
    for resp in carrier_response:
        logger.info(resp)
    asyncio.run(test_loop(cellphone_device, "206-679-5094"))
