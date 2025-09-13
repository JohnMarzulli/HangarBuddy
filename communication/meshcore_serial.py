import time

import serial.tools.list_ports

# https://github.com/meshcore-dev/meshcore_py
# https://pypi.org/project/meshcore/

# Current version of Meshcore (2.0) requires firmware 1.7.4
# Any newer version of the meshcore firmware will not work


if __name__ == "__main__":
    import os
    import sys

    # Ensure the parent directory is in sys.path so 'managers' can be imported
    # This is only needed if running the unit tests directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from meshcore import EventType, MeshCore

from communication.message_send_request import MessageSendRequest
from communication.received_message import ReceivedMessage
from devices.interfaces.messaging_device import MessagingDevice


class MeshcoreSerial(MessagingDevice):
    def __init__(self):
        super().__init__()

        self.contacts: list[dict] = []
        self.__meshcore_interface__: MeshCore | None = None

    def __is_device_allocated__(self) -> bool:
        return self.__meshcore_interface__ is not None

    async def __receive_message__(self) -> bool:
        if not self.__meshcore_interface__:
            return False

        is_received: bool = False

        try:
            result = await self.__meshcore_interface__.commands.get_msg(0.5)
            is_received = result is not None and result.type in [
                EventType.CONTACT_MSG_RECV,
                EventType.CHANNEL_MSG_RECV,
            ]

            if is_received:
                sender: str = self.__get_matching_contact_by_partial_key__(
                    result.payload["pubkey_prefix"]
                )
                recipient: str = (
                    self.device_id if result.payload["type"] == "PRIV" else "ALL"
                )
                incoming_message: ReceivedMessage = ReceivedMessage(
                    sender, recipient, result.payload["text"]
                )
                self.__receiving_queue__.append(incoming_message)
        except Exception as e:
            print(f"Error while receiving messages: {e}")

        return is_received

    def __get_key_by_contact_name__(self, contact_name: str) -> str:
        return next(
            (
                contact.get("public_key", "")
                for contact in self.contacts
                if contact.get("adv_name", "").lower() == contact_name.lower()
            ),
            "",
        )

    def __get_matching_contact_by_partial_key__(self, pubkey_prefix: str) -> str:
        return next(
            (
                contact.get("adv_name", "Unknown")
                for contact in self.contacts
                if contact.get("public_key", "").startswith(pubkey_prefix)
            ),
            "Unknown",
        )

    async def __send_single_message__(
        self, message_to_send: MessageSendRequest
    ) -> bool:
        if not self.__meshcore_interface__:
            return False

        is_successful: bool = False

        try:
            public_key: str = self.__get_key_by_contact_name__(
                message_to_send.recipient
            )
            recipient = {
                "public_key": public_key,
                "adv_name": message_to_send.recipient,
            }
            result = await self.__meshcore_interface__.commands.send_msg(
                recipient, message_to_send.text
            )

            is_successful = (result is not None) and (result.type == EventType.MSG_SENT)
        except Exception as e:
            is_successful = False

        return is_successful

    def __is_connected__(self) -> bool:
        """
        Check if the Meshtastic device is connected.
        """

        if self.__meshcore_interface__ is None:
            return False

        return self.__meshcore_interface__.connection_manager.is_connected

    async def __reconnect__(self):
        """
        Close the connection to the Meshtastic device.
        """
        self.__meshcore_interface__ = await self.__connect_to_device__()
        self.contacts = await self.__get_contacts__()

        self.device_name = str(self.__meshcore_interface__.self_info["name"])
        self.device_id = self.device_name

    async def __get_contacts__(self):
        if not self.__meshcore_interface__:
            raise ConnectionError("Not connected to a Meshtastic device.")

        result = await self.__meshcore_interface__.commands.get_contacts()

        if result is None or result.type == EventType.ERROR:
            raise ConnectionError("Failed to retrieve contacts from the device.")

        contacts = result.payload

        return list(contacts.values()) if contacts else []

    async def __connect_to_device__(self) -> MeshCore:
        all_ports = serial.tools.list_ports.comports()
        ports = [port.device for port in all_ports]

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


if __name__ == "__main__":
    import asyncio

    from devices.interfaces.messaging_device import test_loop

    meshcore_device: MeshcoreSerial = MeshcoreSerial()
    asyncio.run(test_loop(meshcore_device, "👑Crown Hill"))
