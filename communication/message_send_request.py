class MessageSendRequest:
    def __init__(self, recipient: str, text: str, retries_remaining: int = 3):
        self.recipient = recipient
        self.text = text
        self.retries_remaining = retries_remaining

    def is_sendable(self) -> bool:
        return self.retries_remaining > 0

    def decrement_retries(self):
        self.retries_remaining -= 1
