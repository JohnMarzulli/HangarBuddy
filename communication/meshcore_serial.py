import time
from multiprocessing import Queue

# Current version of Meshcore (2.0) requires firmware 1.7.4
# Any newer version of the meshcore firmware will not work

import serial.tools.list_ports

if __name__ == "__main__":
    import os
    import sys

    # Ensure the parent directory is in sys.path so 'managers' can be imported
    # This is only needed if running the unit tests directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio

from meshcore import EventType, MeshCore

from communication.MessageSendRequest import MessageSendRequest

# https://pypi.org/project/meshcore/


class MeshcoreSerial:
    def __init__(self):
        self.id: int = 0
        self.short_name: str = "Unknown"
        self.long_name: str = "Unknown"
        self.device_id: str = "Unknown"
        self.contacts = []
        self.__recieving_queue__ = []
        self.__meshcore_interface__: MeshCore | None = None
        self.__sending_queue__: Queue = Queue()

    async def service(self):
        """
        Process incoming messages and handle them.
        """
        while not self.__is_connected__():
            print(f"Lost connection to `{self.long_name}`. Reconnecting...")

            try:
                await self.__reconnect__()
            except Exception:
                print("Failed to reconnect. Retrying in 5 seconds...")
                time.sleep(5)
                continue

        await self.__service_recieving_messages__()
        await self.__service_send_messages__()

    def send(self, request: MessageSendRequest):
        if not self.__meshcore_interface__:
            raise ConnectionError("Not connected to a Meshtastic device.")

        self.__sending_queue__.put(request)

    def get_incoming_messages(self):
        messages = self.__recieving_queue__.copy()
        self.__recieving_queue__.clear()
        return messages

    async def __service_recieving_messages__(self):
        while await self.__recieve_message__():
            pass

    async def __recieve_message__(self) -> bool:
        is_received: bool = False

        if not self.__meshcore_interface__:
            return False

        try:
            result = await self.__meshcore_interface__.commands.get_msg(0.5)
            is_received = result is not None and result.type in [
                EventType.CONTACT_MSG_RECV,
                EventType.CHANNEL_MSG_RECV,
            ]

            if is_received:
                self.__recieving_queue__.append(result.payload)
        except Exception as e:
            print(f"Error while receiving messages: {e}")

        return is_received

    async def __service_send_messages__(self):

        if not self.__meshcore_interface__:
            return

        messages_to_attempt: list[MessageSendRequest] = []

        while not self.__sending_queue__.empty():
            messages_to_attempt.append(self.__sending_queue__.get())

        while messages_to_attempt:
            message_to_send: MessageSendRequest = messages_to_attempt.pop(0)

            if not message_to_send.is_sendable():
                continue

            is_successful: bool = False

            try:
                result = await self.__meshcore_interface__.commands.send_msg(
                    message_to_send.recipient, message_to_send.text
                )

                is_successful = (result is not None) and (
                    result.type == EventType.MSG_SENT
                )
            except Exception as e:
                is_successful = False

            if not is_successful:
                message_to_send.decrement_retries()
                self.__sending_queue__.put(message_to_send)

    def __is_connected__(self) -> bool:
        """
        Check if the Meshtastic device is connected.
        """

        if self.__meshcore_interface__ is None:
            return False

        return self.__meshcore_interface__.connection_manager.is_connected

    async def __reconnect__(self) -> MeshCore:
        """
        Close the connection to the Meshtastic device.
        """
        self.__meshcore_interface__ = await self.__connect_to_device__()
        self.contacts = await self.__get_contacts__()

        self.short_name = str(self.__meshcore_interface__.self_info["name"])
        self.long_name = str(self.__meshcore_interface__.self_info["name"])
        self.device_id = str(self.__meshcore_interface__.self_info["name"])

        return self.__meshcore_interface__

    async def __get_contacts__(self):
        if not self.__meshcore_interface__:
            raise ConnectionError("Not connected to a Meshtastic device.")

        result = await self.__meshcore_interface__.commands.get_contacts()

        if result is None or result.type == EventType.ERROR:
            raise ConnectionError("Failed to retrieve contacts from the device.")

        contacts = result.payload

        return list(contacts.values()) if contacts else []

    def __get_available_serial_ports__(self) -> list[str]:
        all_ports = serial.tools.list_ports.comports()
        return [port.device for port in all_ports]

    async def __connect_to_device__(self) -> MeshCore:
        ports = self.__get_available_serial_ports__()
        for port in ports:
            print(f"Trying to connect to Meshcore device on {port}...")

            try:
                potential_meshcore_interface: MeshCore = await MeshCore.create_serial(
                    port
                )

                if potential_meshcore_interface is None:
                    continue

                result = await potential_meshcore_interface.commands.get_contacts()

                if result is None:
                    continue

                if result.type == EventType.ERROR:
                    continue

                return potential_meshcore_interface
            except Exception as ex:
                print(f"While attempting connection to Meshcore on {port}, EX={ex}")
                continue
        raise ConnectionError(
            "No Meshcore device found on any serial port, or all the devices is already connected."
        )


async def main():
    try:
        meshcore_device: MeshcoreSerial = MeshcoreSerial()

        while not meshcore_device.__is_connected__():
            time.sleep(1)
            print("Connecting to Meshcore device...")
            await meshcore_device.service()

        print(f"Connected to {meshcore_device.short_name}")

        # Example usage
        meshcore_device.send(
            MessageSendRequest(meshcore_device.contacts[0], "Test Message!")
        )
        print("Message sent successfully.")

        while True:
            await meshcore_device.service()
            messages = meshcore_device.get_incoming_messages()
            for msg in messages:
                print(f"Received message: {msg}")
            time.sleep(1)
    except ConnectionError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
