from collections import deque
from datetime import datetime
from typing import Deque

from display.display_message import DisplayMessage
from display.priority import Priority


class DisplayQueue:
    """
    Internally uses name-mangling for all private internals.
    """

    def __init__(self) -> None:
        self.__high_priority_messages__: Deque[DisplayMessage] = deque()
        self.__normal_priority_messages__: Deque[DisplayMessage] = deque()
        self.__low_priority_messages__: Deque[DisplayMessage] = deque()

    def is_unique(self, queue: Deque[DisplayMessage], message: DisplayMessage) -> bool:
        for msg in queue:
            if msg.text == message.text:
                return False

        return True

    def enqueue(self, message: DisplayMessage) -> None:
        if message.priority == Priority.HIGH and self.is_unique(self.__high_priority_messages__, message):
            self.__high_priority_messages__.append(message)
        elif message.priority == Priority.LOW and self.is_unique(self.__low_priority_messages__, message):
            self.__low_priority_messages__.append(message)
        elif self.is_unique(self.__normal_priority_messages__, message):
            self.__normal_priority_messages__.append(message)

    def __get_only_valid_queue_entries__(self, now: datetime, queue: deque) -> deque:
        filtered_queue: deque = deque()

        while queue:
            msg: DisplayMessage = queue.popleft()

            if msg and not msg.is_expired(now):
                filtered_queue.append(msg)

        return filtered_queue

    def purge_expired(self, now: datetime) -> None:
        self.__high_priority_messages__ = self.__get_only_valid_queue_entries__(now, self.__high_priority_messages__)
        self.__normal_priority_messages__ = self.__get_only_valid_queue_entries__(
            now, self.__normal_priority_messages__
        )
        self.__low_priority_messages__ = self.__get_only_valid_queue_entries__(now, self.__low_priority_messages__)

    def pop_next(self, current_message_priority: Priority) -> DisplayMessage | None:
        if current_message_priority <= Priority.HIGH and self.__high_priority_messages__:
            return self.__high_priority_messages__.popleft()

        if current_message_priority <= Priority.NORMAL and self.__normal_priority_messages__:
            return self.__normal_priority_messages__.popleft()

        return self.__low_priority_messages__.popleft() if self.__low_priority_messages__ else None

    def is_empty(self) -> bool:
        high_count: int = len(self.__high_priority_messages__)
        med_count: int = len(self.__normal_priority_messages__)
        low_count: int = len(self.__low_priority_messages__)
        total_message_count: int = high_count + med_count + low_count

        return total_message_count == 0
