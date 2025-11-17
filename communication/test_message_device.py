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

from meshcore import MeshCore

from communication.message_send_request import MessageSendRequest
from devices.interfaces.messaging_device import MessagingDevice
from lib.system_level_logging import SystemLevelLogger


class TestMessagingDevice(MessagingDevice):
    def __init__(self, logger: SystemLevelLogger):
        super().__init__(logger)

        self.contacts: list[dict] = []
        self.__meshcore_interface__: MeshCore | None = None

    def __is_device_allocated__(self) -> bool:
        return True

    async def __receive_message__(self) -> bool:
        return False

    async def __send_single_message__(self, message_to_send: MessageSendRequest) -> bool:
        return True

    def __is_connected__(self) -> bool:
        return True

    async def __reconnect__(self):
        pass


if __name__ == "__main__":
    import asyncio

    from configuration import Configuration
    from devices.interfaces.messaging_device import test_loop

    test_device: TestMessagingDevice = TestMessagingDevice(SystemLevelLogger(Configuration(), "TestMessagingDevice"))
    asyncio.run(test_loop(test_device, "👑Crown Hill"))
