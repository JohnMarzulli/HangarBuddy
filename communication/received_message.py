from datetime import datetime

from lib.time_correction import TIME_CORRECTION


class ReceivedMessage:
    """
    DTO for a message received by a device.
    """

    def __init__(self, time_recieved: datetime, sender: str, recipient: str, text: str):
        self.sender = sender
        self.recipient = recipient
        self.text = text
        self.received_at: datetime = time_recieved

        TIME_CORRECTION.add_report(time_recieved)
