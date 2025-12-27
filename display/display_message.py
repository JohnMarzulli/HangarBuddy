from datetime import datetime, timedelta, timezone

from display.priority import Priority

DEFAULT_TTL = timedelta(seconds=5)
DEFAULT_MIN_DISPLAY_TIME = timedelta(seconds=1.5)


class DisplayMessage:
    def __init__(
        self,
        text: str,
        priority: Priority = Priority.NORMAL,
        ttl: timedelta = DEFAULT_TTL,
        min_display_time: timedelta = DEFAULT_MIN_DISPLAY_TIME,
    ):
        self.created = datetime.now(timezone.utc)

        self.text = text
        self.priority = priority
        self.ttl = ttl
        self.min_display_time = min_display_time

    def is_expired(self, now: datetime) -> bool:
        expiration_date: datetime = self.created + self.ttl
        is_expired = now > expiration_date

        if is_expired:
            print(
                f"Message '{self.text}' expired. Created at {self.created}, "
                f"TTL {self.ttl}, expired at {expiration_date}, now is {now}"
            )

        return is_expired
