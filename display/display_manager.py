from datetime import datetime, timedelta, timezone

from display.display_queue import DisplayQueue

if __name__ == "__main__":
    import os
    import sys

    # Ensure the parent directory is in sys.path so 'managers' can be imported
    # This is only needed if running the unit tests directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from devices.interfaces.display_device import DisplayDevice
from display.display_message import DisplayMessage
from display.priority import Priority


class DisplayManager:
    def __init__(self, display: DisplayDevice):
        self.__display__: DisplayDevice = display
        self.__queue__: DisplayQueue = DisplayQueue()

        self.__current_page_index__: int = 0
        self.__last_page_render_time__: datetime = datetime.now(timezone.utc) - timedelta(seconds=100)

        # Active message tracking
        self.__active_message__: DisplayMessage | None = None
        self.__active_message_started_at__: datetime | None = None

        display.clear()

    def show_now(self, text: str) -> bool:
        msg = DisplayMessage(text=text, priority=Priority.HIGH)
        self.__display__.write_text(msg.text)
        self.__active_message__ = msg
        self.__active_message_started_at__ = datetime.now(timezone.utc)

        return True

    def show(self, request: DisplayMessage) -> bool:
        text = request.text

        msg = DisplayMessage(
            text=text,
            priority=request.priority,
            ttl=request.ttl,
            min_display_time=request.min_display_time,
        )

        self.__queue__.enqueue(msg)

        return True

    def update(self) -> None:
        now: datetime = datetime.now(timezone.utc)

        self.__queue__.purge_expired(now)

        # Clear any messages past their expiration
        if self.__active_message__ is not None and self.__active_message_started_at__ is not None:
            message_expiration_time = self.__active_message__.created + self.__active_message__.ttl

            if now >= message_expiration_time:
                self.__active_message__ = None
                self.__active_message_started_at__ = None

        # If an active message is still within minimum display time, keep showing it
        if self.__active_message__ is not None and self.__active_message_started_at__ is not None:
            new_message_eligiable_at = self.__active_message_started_at__ + self.__active_message__.min_display_time

            if now < new_message_eligiable_at:
                return

        current_message_priority: Priority = (
            self.__active_message__.priority if self.__active_message__ is not None else Priority.LOW
        )
        # Try to pop from queue
        msg: DisplayMessage | None = self.__queue__.pop_next(current_message_priority)

        self.__display__.clear()

        if msg is not None:
            self.__display__.write_text(msg.text)
            self.__active_message__ = msg
            self.__active_message_started_at__ = now
