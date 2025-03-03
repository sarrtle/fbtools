"""Will not work on.

Why:
    Will complicate the current Message models.
    It doesn't have a sender field.

Solution:
    Possible implement your own warning model for
    your own app while you send this form as a message.

    fbtools listen event will not recieve this webhook
    to notify you that you sent this message.

Sample Data:
{
    "object": "page",
    "entry": [
        {
            "time": 1741013802312,
            "id": "0",
            "messaging": [
                {
                    "recipient": {
                        "id": "23245"
                    },
                    "timestamp": "1527459824",
                    "policy_enforcement": {
                        "action": "warning",
                        "reason": "Warning reason
                    }
                }
            ]
        }
    ]
}
"""
