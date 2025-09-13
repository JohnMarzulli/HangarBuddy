import time

import meshtastic
import meshtastic.serial_interface
import serial.tools.list_ports
from pubsub import pub

if __name__ == "__main__":
    import os
    import sys

    # Ensure the parent directory is in sys.path so 'managers' can be imported
    # This is only needed if running the unit tests directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from communication.received_message import ReceivedMessage
from devices.interfaces.messaging_device import MessagingDevice

if __name__ == "__main__":
    import os
    import sys

    # Ensure the parent directory is in sys.path so 'managers' can be imported
    # This is only needed if running the unit tests directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from communication.message_send_request import MessageSendRequest


class MeshtasticSerial(MessagingDevice):
    def __init__(self):
        super().__init__()
        self.__meshastic_interface__: meshtastic.serial_interface.SerialInterface = (
            self.__reconnect__()
        )

    def __is_device_allocated__(self) -> bool:
        return self.__meshastic_interface__ is not None

    async def __receive_message__(self) -> bool:
        return False

    async def __send_single_message__(self, request: MessageSendRequest):
        if not self.__meshastic_interface__:
            return False
        try:
            self.__meshastic_interface__.sendText(
                request.text, destinationId=request.recipient
            )

            return True
        except Exception as e:
            return False

    def __is_connected__(self) -> bool:
        """
        Check if the Meshtastic device is connected.
        """
        is_interface_present: bool = self.__meshastic_interface__ is not None
        is_connected: bool = (
            is_interface_present and self.__meshastic_interface__.isConnected.is_set()
        )

        return is_connected

    def __reconnect__(self) -> meshtastic.serial_interface.SerialInterface:
        """
        Close the connection to the Meshtastic device.
        """
        if (
            hasattr(self, "meshastic_interface")
            and self.__meshastic_interface__ is not None
        ):
            self.__meshastic_interface__.close()

        self.__meshastic_interface__: meshtastic.serial_interface.SerialInterface = (
            self.__connect_to_device__()
        )
        self.device_name = str(self.__meshastic_interface__.getShortName())
        self.device_id = f"!{hex(self.__meshastic_interface__.myInfo.my_node_num).replace('0x', '')}"  # type: ignore
        pub.subscribe(self.__on_receive__, "meshtastic.receive")

        return self.__meshastic_interface__

    def __connect_to_device__(self) -> meshtastic.serial_interface.SerialInterface:
        all_ports = serial.tools.list_ports.comports()
        ports = [port.device for port in all_ports]

        for port in ports:
            print(f"Trying to connect to Meshtastic device on {port}...")

            try:
                potential_meshastic_interface = (
                    meshtastic.serial_interface.SerialInterface(devPath=port)
                )
                # Wait for node info to confirm connection
                time.sleep(2)
                if potential_meshastic_interface.myInfo:
                    print(f"Connected to Meshtastic device on {port}.")

                    return potential_meshastic_interface
            except Exception as ex:
                print(f"While attempting connection to Meshtastic on {port}, EX={ex}")
                continue
        raise ConnectionError(
            "No Meshtastic device found on any serial port, or all the devices is already connected."
        )

    def __on_receive__(self, packet, interface):
        try:
            # Only queue messages intended for this device
            if (
                packet is not None
                and "decoded" in packet
                and packet["decoded"]["portnum"] == "TEXT_MESSAGE_APP"
            ):
                sender: str = packet["fromId"]
                recipient: str = packet["toId"]
                test: str = packet["decoded"]["payload"].decode("utf-8")
                incoming_message: ReceivedMessage = ReceivedMessage(
                    sender, recipient, test
                )
                self.__receiving_queue__.append(incoming_message)
        except KeyError as e:
            print(f"Error processing packet: {e}")


if __name__ == "__main__":
    import asyncio

    from devices.interfaces.messaging_device import test_loop

    meshtastic_device: MeshtasticSerial = MeshtasticSerial()
    recipient = "!ba66ffe4"

    asyncio.run(test_loop(meshtastic_device, recipient))
