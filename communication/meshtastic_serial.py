import time

import meshtastic
import meshtastic.serial_interface
import serial.tools.list_ports
from pubsub import pub


class MeshtasticSerial:
    def __init__(self):
        self._message_queue = []
        self.id: int = 0
        self.short_name: str = "Unknown"
        self.long_name: str = "Unknown"
        self.device_id: str = "Unknown"
        self.__meshastic_interface__: meshtastic.serial_interface.SerialInterface = (
            self.__reconnect__()
        )

    def service(self):
        """
        Process incoming messages and handle them.
        """
        while not self.__is_connected__():
            print(f"Lost connection to `{self.long_name}`. Reconnecting...")

            try:
                self.__reconnect__()
            except Exception:
                print("Failed to reconnect. Retrying in 5 seconds...")
                time.sleep(5)
                continue

    def send(self, recipient, text):
        if not self.__meshastic_interface__:
            raise ConnectionError("Not connected to a Meshtastic device.")
        try:
            self.__meshastic_interface__.sendText(text, destinationId=recipient)
        except Exception as e:
            raise ConnectionError(f"Failed to send message: {e}") from e

    def get_message_queue(self):
        messages = self._message_queue.copy()
        self._message_queue.clear()
        return messages

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
        self.short_name = str(self.__meshastic_interface__.getShortName())
        self.long_name = str(self.__meshastic_interface__.getLongName())
        self.device_id = f"!{hex(self.__meshastic_interface__.myInfo.my_node_num).replace('0x', '')}"  # type: ignore
        self.id = (
            self.__meshastic_interface__.configId
            if self.__meshastic_interface__.configId is not None
            else 0
        )
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
                self._message_queue.append(packet)
        except KeyError as e:
            print(f"Error processing packet: {e}")


if __name__ == "__main__":
    try:
        recipient: str = "db2b5a40"
        meshtastic_device: MeshtasticSerial = MeshtasticSerial()
        print(
            f"Connected to {meshtastic_device.short_name}/{meshtastic_device.long_name}/{meshtastic_device.device_id}."
        )

        # Example usage
        meshtastic_device.send(recipient, "Test Message!")
        print("Message sent successfully.")

        while True:
            messages = meshtastic_device.get_message_queue()
            for msg in messages:
                print(f"Received message: {msg}")
            time.sleep(1)
    except ConnectionError as e:
        print(f"Error: {e}")
