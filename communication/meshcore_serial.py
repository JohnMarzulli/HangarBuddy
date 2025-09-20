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
from lib.system_level_logging import SystemLevelLogger


class MeshcoreSerial(MessagingDevice):
    def __init__(self, logger: SystemLevelLogger):
        super().__init__(logger)

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
                if result is None or result.payload is None:
                    self.__logger__.warning("Received message event without payload.")

                    return False

                public_key_prefix: str = result.payload.get("pubkey_prefix", "")
                message_text: str = result.payload.get("text", "")
                message_type = result.payload.get("type", "")
                recipient: str = self.device_id if message_type == "PRIV" else "ALL"

                if message_type != "PRIV":
                    self.__logger__.warning(
                        f"Received message event with unsupported type: {message_type}, TEXT='{message_text}'."
                    )

                    return False

                if not public_key_prefix:
                    self.__logger__.warning("Received message event without public key prefix.")

                    return False

                sender: str = self.__get_matching_contact_by_partial_key__(public_key_prefix)
                incoming_message: ReceivedMessage = ReceivedMessage(sender, recipient, message_text)
                self.__receiving_queue__.append(incoming_message)
        except Exception as e:
            self.__logger__.error(f"Error while receiving messages: {e}")

        return is_received

    def __get_ascii_only__(self, name: str) -> str:
        return "".join(char for char in name if char.isascii())

    def __get_key_by_contact_name__(self, contact_name: str) -> str:
        ascii_safe_name = self.__get_ascii_only__(contact_name).strip().lower()

        print(f"Searching for:{ascii_safe_name}")

        for contact in self.contacts:
            if contact is None:
                continue

            if not "public_key" in contact:
                continue

            if not "adv_name" in contact:
                continue

            print(f'Trying to match contact to {contact["adv_name"]}')

            name_to_try = contact.get("adv_name", "")
            safe_comparison = self.__get_ascii_only__(name_to_try).strip().lower()

            print(f"Trying to match {ascii_safe_name} to CLEANED:{safe_comparison}")

            if ascii_safe_name == safe_comparison:
                return contact["adv_name"]

        return ""

    def __get_matching_contact_by_partial_key__(self, pubkey_prefix: str) -> str:
        return next(
            (
                contact.get("adv_name", "Unknown")
                for contact in self.contacts
                if contact.get("public_key", "").startswith(pubkey_prefix)
            ),
            "Unknown",
        )

    async def __send_single_message__(self, message_to_send: MessageSendRequest) -> bool:
        if not self.__meshcore_interface__:
            return False

        is_successful: bool = False

        try:
            if public_key := self.__get_key_by_contact_name__(message_to_send.recipient):
                recipient = {
                    "public_key": public_key,
                    "adv_name": message_to_send.recipient,
                }
                result = await self.__meshcore_interface__.commands.send_msg(recipient, message_to_send.text)

                is_successful = (result is not None) and (result.type == EventType.MSG_SENT)
            else:
                self.__logger__.error(f"Cannot send message, no contact found with name '{message_to_send.recipient}'.")

                is_successful = False
        except Exception as e:
            self.__logger__.error(f"Error while sending message: {e}")
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
            self.__logger__.info(f"Trying to connect to Meshcore device on {port}...")

            try:
                potential_meshcore_interface: MeshCore = await MeshCore.create_serial(port)

                if potential_meshcore_interface is None:
                    continue

                result = await potential_meshcore_interface.commands.get_contacts()

                if result is None:
                    continue

                if result.type == EventType.ERROR:
                    continue

                self.__logger__.info(f"CONNECTED to Meshcore device on {port}...")

                return potential_meshcore_interface
            except Exception as ex:
                self.__logger__.error(f"While attempting connection to Meshcore on {port}, EX={ex}")
                continue
        raise ConnectionError("No Meshcore device found on any serial port, or all the devices is already connected.")


if __name__ == "__main__":
    import asyncio

    from configuration import Configuration
    from devices.interfaces.messaging_device import test_loop

    meshcore_device: MeshcoreSerial = MeshcoreSerial(SystemLevelLogger(Configuration(), "MeshcoreSerialTester"))
    asyncio.run(test_loop(meshcore_device, "👑Crown Hill"))
