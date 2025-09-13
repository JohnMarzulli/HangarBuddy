class ReceivedMessage:
    def __init__(self, sender: str, recipient: str, text: str):
        self.sender = sender
        self.recipient = recipient
        self.text = text
