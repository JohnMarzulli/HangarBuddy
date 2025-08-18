import time

import meshtastic
import meshtastic.serial_interface
import serial.tools.list_ports
from pubsub import pub


class MeshtasticSerial:
    def __init__(self):
        self._message_queue = []
        self.meshastic_interface: meshtastic.serial_interface.SerialInterface = (
            self._connect_to_device()
        )
        self.meshastic_interface.onReceive = self._on_receive
        self.short_name = self.meshastic_interface.getShortName()
        self.long_name = self.meshastic_interface.getLongName()
        self.device_id = self.meshastic_interface.myInfo.device_id
        pub.subscribe(self._on_receive, "meshtastic.receive")

    def _connect_to_device(self) -> meshtastic.serial_interface.SerialInterface:
        ports = [port.device for port in serial.tools.list_ports.comports()]
        for port in ports:
            print(f"Trying to connect to Meshtastic device on {port}...")

            try:
                potential_meshastic_interface = (
                    meshtastic.serial_interface.SerialInterface(devPath=port)
                )
                # Wait for node info to confirm connection
                time.sleep(2)
                if potential_meshastic_interface.myInfo:
                    return potential_meshastic_interface
            except Exception:
                continue
        raise ConnectionError(
            "No Meshtastic device found on any serial port, or all the devices is already connected."
        )

    def _on_receive(self, packet, interface):
        try:
            # Only queue messages intended for this device
            if (
                "decoded" in packet
                and packet["decoded"]["portnum"] == "TEXT_MESSAGE_APP"
            ):
                message_bytes = packet["decoded"]["payload"]
                message_string = message_bytes.decode("utf-8")
                print(f"{message_string} \n> ", end="", flush=True)

                self._message_queue.append(packet)
        except KeyError as e:
            print(f"Error processing packet: {e}")

    def send(self, recipient, text):
        if not self.meshastic_interface:
            raise ConnectionError("Not connected to a Meshtastic device.")
        try:
            self.meshastic_interface.sendText(text, destinationId=recipient)
        except Exception as e:
            raise ConnectionError(f"Failed to send message: {e}") from e

    def get_message_queue(self):
        messages = self._message_queue.copy()
        self._message_queue.clear()
        return messages


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
