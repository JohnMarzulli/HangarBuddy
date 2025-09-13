import time
from multiprocessing import Queue

from communication.message_send_request import MessageSendRequest
from communication.received_message import ReceivedMessage


class MessagingDevice:
    """
    Interface for a messaging device. This could be a Meshcore, Meshtastic, or cell modem.

    Should not be created directly.
    """

    def __init__(self):
        """
        Initialize the core service queues.
        """
        self.id: int = 0
        self.device_name: str = "Unknown"
        self.device_id: str = "Unknown"
        self.contacts = []
        self.__receiving_queue__: list[ReceivedMessage] = []
        self.__sending_queue__: Queue = Queue()

    async def service(self):
        """
        Process incoming messages and handle them.
        Processes the outgoing message queue to handle sending them and any associated retries.
        """
        while not self.__is_connected__():
            print(f"Lost connection to `{self.device_name}`. Reconnecting...")

            try:
                await self.__reconnect__()
            except Exception:
                print("Failed to reconnect. Retrying in 5 seconds...")
                time.sleep(5)
                continue

        await self.__service_receiving_messages__()
        await self.__service_send_messages__()

    def send(self, request: MessageSendRequest):
        """
        Add a message to the sending queue. Does not immediately send the message.

        Args:
            request (MessageSendRequest): The message to send.

        Raises:
            ConnectionError: Raised if no device is connected.
        """
        if not self.__is_device_allocated__():
            raise ConnectionError("Not connected to a messaging device.")

        self.__sending_queue__.put(request)

    def get_incoming_messages(self) -> list[ReceivedMessage]:
        """
        Returns a list of the incoming messages. Clears the reception queue.
        Once these messages are captured, they need to be handled by the calling code
        or they are lost.

        Returns:
            list[ReceivedMessage]: The set of incoming messages.
        """
        messages: list[ReceivedMessage] = self.__receiving_queue__.copy()
        self.__receiving_queue__.clear()

        return messages

    async def __service_receiving_messages__(self):
        while await self.__receive_message__():
            pass

    def __is_device_allocated__(self) -> bool:
        raise NotImplementedError("This method should be implemented by subclasses.")

    async def __receive_message__(self) -> bool:
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
    """
    Provides a way to test a messaging device by using the interface.
    Useful for testing connectivity or debugging with spinning up the entire HangarBuddy

    Args:
        device (MessagingDevice): The device to send and receive messages with.
        recipient (_type_): The recipient of any test messages that are sent.
    """
    try:
        while not device.__is_connected__():
            time.sleep(1)
            print("Connecting to device...")
            await device.service()

        print(f"Connected to {device.device_name}")

        device.send(MessageSendRequest(recipient, "Test Message!"))
        print("Message sent successfully.")

        while True:
            await device.service()
            messages = device.get_incoming_messages()
            for msg in messages:
                print(
                    f"Received message:\n\tTO:{msg.recipient}\n\tFROM:{msg.sender}\n\tTEXT:{msg.text}"
                )
            time.sleep(1)
    except ConnectionError as e:
        print(f"Error: {e}")
