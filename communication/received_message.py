from datetime import datetime, timezone

class ReceivedMessage:
    """
    DTO for a message received by a device.
    """
    def __init__(self, sender: str, recipient: str, text: str):
        self.sender = sender
        self.recipient = recipient
        self.text = text
        self.received_at: datetime = datetime.now(timezone.utc)
