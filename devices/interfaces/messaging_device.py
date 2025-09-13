import time
from multiprocessing import Queue

# https://github.com/meshcore-dev/meshcore_py


from communication.message_send_request import MessageSendRequest
from communication.recieved_message import RecievedMessage

# https://pypi.org/project/meshcore/


class MessagingDevice:
    def __init__(self):
        self.id: int = 0
        self.device_name: str = "Unknown"
        self.device_id: str = "Unknown"
        self.contacts = []
        self.__recieving_queue__: list[RecievedMessage] = []
        self.__sending_queue__: Queue = Queue()

    async def service(self):
        """
        Process incoming messages and handle them.
        """
        while not self.__is_connected__():
            print(f"Lost connection to `{self.device_name}`. Reconnecting...")

            try:
                await self.__reconnect__()
            except Exception:
                print("Failed to reconnect. Retrying in 5 seconds...")
                time.sleep(5)
                continue

        await self.__service_recieving_messages__()
        await self.__service_send_messages__()

    def send(self, request: MessageSendRequest):
        if not self.__is_device_allocated__():
            raise ConnectionError("Not connected to a Meshtastic device.")

        self.__sending_queue__.put(request)

    def get_incoming_messages(self) -> list[RecievedMessage]:
        messages:list[RecievedMessage] = self.__recieving_queue__.copy()
        self.__recieving_queue__.clear()

        return messages

    async def __service_recieving_messages__(self):
        while await self.__recieve_message__():
            pass

    def __is_device_allocated__(self) -> bool:
        raise NotImplementedError("This method should be implemented by subclasses.")

    async def __recieve_message__(self) -> bool:
        raise NotImplementedError("This method should be implemented by subclasses.")

    async def __send_single_message__(
        self, message_to_send: MessageSendRequest
    ) -> bool:
        raise NotImplementedError("This method should be implemented by subclasses.")

    async def __service_send_messages__(self):

        if not self.__is_device_allocated__():
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
                is_successful = await self.__send_single_message__(message_to_send)
            except Exception as e:
                is_successful = False

            if not is_successful:
                message_to_send.decrement_retries()
                self.__sending_queue__.put(message_to_send)

    def __is_connected__(self) -> bool:
        """
        Check if the device is connected.
        """

        raise NotImplementedError("This method should be implemented by subclasses.")

    async def __reconnect__(self):
        """
        Close the connection to the Meshtastic device.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")


async def test_loop(device: MessagingDevice, recipient):
    try:
        while not device.__is_connected__():
            time.sleep(1)
            print("Connecting to device...")
            await device.service()

        print(f"Connected to {device.device_name}")

        # Example usage
        device.send(MessageSendRequest(recipient, "Test Message!"))
        print("Message sent successfully.")

        while True:
            await device.service()
            messages = device.get_incoming_messages()
            for msg in messages:
                print(f"Received message:\n\tTO:{msg.recipient}\n\tFROM:{msg.sender}\n\tTEXT:{msg.text}")
            time.sleep(1)
    except ConnectionError as e:
        print(f"Error: {e}")
