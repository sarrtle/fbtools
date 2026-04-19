"""Id response model."""

from pydantic import BaseModel


class IdResponse(BaseModel):
    """Id response model."""

    id: str
