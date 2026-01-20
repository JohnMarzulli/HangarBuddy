class MessageSendRequest:
    """
    A message that we will attempt to send.
    """

    def __init__(self, recipient: str, text: str, retries_remaining: int = 3):
        """
        Set the message that we want to send.

        Args:
            recipient (str): The recipient (as the device wants it) to send the message to.
            text (str): The text of the message.
            retries_remaining (int, optional): The number of attempts remaining in case the send fails. Defaults to 3.
        """
        self.recipient = recipient
        self.text = text
        self.retries_remaining = retries_remaining

    def is_sendable(self) -> bool:
        """
        Does this message have any retry attempts remaining.

        Returns:
            bool: True if we can attempt to send the messages.
        """
        return self.retries_remaining > 0

    def decrement_retries(self):
        """
        Remove a send attempt.
        """
        self.retries_remaining -= 1
