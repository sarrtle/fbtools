"""Model for video upload status.

Upload status of a video. Use by Video and Reels.
Shameless copy from old fbtools-backup

Docs:
    https://developers.facebook.com/docs/video-api/guides/reels-publishing


"""

from typing import Literal
from pydantic import BaseModel, model_validator
from datetime import datetime

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
    errors: list["ErrorData"] | None = None


class VideoProcessingStatus(BaseModel):
    """Processing status of a video."""

    status: VIDEOSTATUSTYPE
    error: "VideoUploadError | None" = None

    # separate error for reels
    errors: list["ErrorData"] | None = None


class VideoPublishingStatus(BaseModel):
    """Publishing status of a video."""

    status: VIDEOSTATUSTYPE
    publish_status: Literal["draft", "error", "published", "scheduled"] | None = None
    publishing_time: datetime | None = None
    error: "VideoUploadError | None" = None

    # separate error for reels
    errors: list["ErrorData"] | None = None


class VideoUploadError(BaseModel):
    """Error of a video upload."""

    message: str


class ErrorData(BaseModel):
    """Error of a video upload."""

    code: int
    message: str
