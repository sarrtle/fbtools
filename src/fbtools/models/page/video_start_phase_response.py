"""Video start phase response model."""

from pydantic import BaseModel, model_validator


class VideoStartPhaseResponse(BaseModel):
    """Response from starting a video upload session."""

    video_id: str
    start_offset: int
    end_offset: int
    upload_session_id: str

    @model_validator(mode="before")
    def _convert_to_int(cls, values: dict[str, str | int]):
        values["start_offset"] = int(values["start_offset"])
        values["end_offset"] = int(values["end_offset"])
        return values
