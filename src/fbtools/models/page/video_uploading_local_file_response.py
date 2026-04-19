"""Video uploading local file response model."""

from pydantic import BaseModel, model_validator


class VideoUploadingLocalFileResponse(BaseModel):
    """Video uploading local file response model."""

    start_offset: int
    end_offset: int
    error: str | None = None  # temporarily since i dont know what data I am receiving

    @model_validator(mode="before")
    def _convert_to_int(cls, values: dict[str, str | int]):
        values["start_offset"] = int(values["start_offset"])
        values["end_offset"] = int(values["end_offset"])

        if "error" in values:
            values["error"] = str(values["error"])

        return values
