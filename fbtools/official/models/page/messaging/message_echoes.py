"""Message echo webhook.

A notification is sent when your page sent a message and
can show you if the message was sent by a bot or a human.

Sample Data:
{
    "object": "page",
    "entry": [
        {
            "time": 1740916107728,
            "id": "0",
            "messaging": [
                {
                    "sender": {
                        "id": "12334"
                    },
                    "recipient": {
                        "id": "23245"
                    },
                    "timestamp": "1527459824",
                    "message": { # MessageEchoes starts here
                        "is_echo": true,
                        "mid": "test_message_id",
                        "text": "test_message"
                    }
                }
            ]
        }
    ]
}

"""

from pydantic import BaseModel


class MessageEchoContent(BaseModel):
    """Message echo content.

    Attributes:
        is_echo: If true, then the message was sent by a bot.
        mid: The message id.
        text: The content of the message.

    """

    is_echo: bool
    mid: str
    text: str
