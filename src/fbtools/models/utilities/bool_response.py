"""Bool response model."""

from pydantic import BaseModel


class BoolResponse(BaseModel):
    """Return bool response."""

    success: bool
