"""Test for programming."""

import asyncio
import json
from pydantic import BaseModel
from fbtools.unofficial.session import Session


class Account(BaseModel):
    """Account model."""

    email: str
    password: str
    twofac: str


with open("account.jsonc", "r") as f:
    data = Account.model_validate(json.load(f))

# if custom user agent
# user_agent = UserAgent(desktop_user_agent="", mobilefb_user_agent="")

session = Session()  # Session(user_agent=user_agent)


async def main():
    """App."""
    await session.login_as_browser(data.email, data.password, data.twofac)

    print("Is logged in?", await session.is_logged_in())


asyncio.run(main())
