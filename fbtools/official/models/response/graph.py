"""Response objects for Facebook Graph API."""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, model_validator


# ==============================================================================
class SuccessResponse(BaseModel):
    """Success response from Facebook Graph API."""

    success: bool


# ==============================================================================
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


# ==============================================================================
VIDEOSTATUSTYPE = Literal["complete", "error", "not_started", "in_progress"]


class VideoUploadStatus(BaseModel):
    """Upload status of a video.

    Use by Video and Reels.


    Docs:
        https://developers.facebook.com/docs/video-api/guides/reels-publishing

    """

    status: "VideoStatus"


class VideoStatus(BaseModel):
    """Status of a video upload."""

    video_status: Literal[
        "error",
        "expired",
        "processing",
        "ready",
        "uploading",
        "upload_failed",
        "upload_complete",
    ]
    processing_progress: int | None = None
    uploading_phase: "VideoUploadingStatus"
    processing_phase: "VideoProcessingStatus"
    publishing_phase: "VideoPublishingStatus"
    error: "VideoUploadError | None" = None

    @model_validator(mode="before")
    def _check_errors(
        cls,
        values: dict[
            str,
            "int | str | dict[str, str | dict[str, str]] | VideoUploadError",
        ],
    ):
        error_message = None

        # get the related errors from one of the phase and put it at the main error
        for _key, value in values.items():
            if (
                not isinstance(value, str)
                and not isinstance(value, int)
                and not isinstance(value, VideoUploadError)
            ):
                if "error" in value and isinstance(value["error"], dict):
                    error_message = value["error"]["message"]

        if error_message is not None:
            values["error"] = VideoUploadError.model_validate(
                {"message": error_message}
            )
        return values


class VideoUploadingStatus(BaseModel):
    """Uploading status of a video."""

    status: VIDEOSTATUSTYPE
    bytes_transfered: int | None = None
    source_file_size: int | None = None
    error: "VideoUploadError | None" = None


class VideoProcessingStatus(BaseModel):
    """Processing status of a video."""

    status: VIDEOSTATUSTYPE
    error: "VideoUploadError | None" = None


class VideoPublishingStatus(BaseModel):
    """Publishing status of a video."""

    status: VIDEOSTATUSTYPE
    publish_status: Literal["draft", "error", "published", "scheduled"] | None = None
    publishing_time: datetime | None = None
    error: "VideoUploadError | None" = None


class VideoUploadError(BaseModel):
    """Error of a video upload."""

    message: str
