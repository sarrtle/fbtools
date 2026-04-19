"""Page node of Facebook Graph API."""

import asyncio
from collections.abc import Coroutine
from pathlib import Path
from typing import Callable, Literal
from fbtools.api.post import FacebookPost
from fbtools.models.page.feed_id_response import FeedIdResponse
from fbtools.models.page.feed_post_upload import AttachedMedia, FeedPostUploadData
from fbtools.models.page.id_response import IdResponse
from fbtools.models.page.page_data_item import PageDataItem
from httpx import AsyncClient

from fbtools.models.page.video_start_phase_response import VideoStartPhaseResponse
from fbtools.models.page.video_upload_status import VideoUploadStatus
from fbtools.models.page.video_uploading_local_file_response import (
    VideoUploadingLocalFileResponse,
)
from fbtools.utilities.common import create_base_url, is_url_valid
from fbtools.utilities.core import create_photo_id

from aiofiles import open as aopen


class Page:
    """Page node of Facebook Graph API."""

    def __init__(self, page_data: PageDataItem, session: AsyncClient):
        """Initialize page."""
        # public attributes
        self.category: str = page_data.category
        self.name: str = page_data.name

        # private attributes
        self._id: str = page_data.id
        self._access_token: str = page_data.access_token
        self._session: AsyncClient = session

    @classmethod
    async def from_access_token(
        cls,
        page_access_token: str,
        user_id: str | Literal["me"] = "me",
        session: AsyncClient | None = None,
    ) -> "Page":
        """Initialize page from access token."""
        # request page data from official api
        params = {
            "access_token": page_access_token,
            "fields": "id,name,category,access_token",
        }

        if session is None:
            session = AsyncClient(base_url=create_base_url(), timeout=60)

        response = await session.get(user_id, params=params)

        # validate data
        page_data = PageDataItem.model_validate(response.json())

        # add data to page
        return cls(page_data=page_data, session=session)

    async def create_feed_post(
        self,
        message: str,
        images: str | list[str] | None = None,
        user_id: str | Literal["me"] = "me",
    ) -> FacebookPost:
        """Create a feed post.

        You can create a text post and an image post.

        Notes:
            You can only create this kind of post on this endpoint. Video post are
            separated and has a different process.

            You can upload multiple images here too.

        Args:
            message: The message written in the post.
            images: If you wished to add images to the post.
            user_id: User ID or "me". The "me" is used on dev mode.

        Returns:
            The FacebookPost object.

        """
        url_path = f"{user_id}/feed"
        data = FeedPostUploadData(message=message)
        params = {"access_token": self._access_token}

        if images:
            if isinstance(images, str):
                images = [images]

            # TODO: Needs further optimization if many attachment images
            #       will be uploaded.
            data.attached_media = []
            for attachment in images:
                photo_id = await create_photo_id(
                    attachment, self._access_token, self._session
                )
                data.attached_media.append(AttachedMedia(media_fbid=photo_id))

        response = await self._session.post(
            url_path, json=data.model_dump(), params=params
        )

        id_response = IdResponse.model_validate(response.json())

        return FacebookPost(
            post_id=id_response.id,
            access_token=self._access_token,
            session=self._session,
        )

    async def create_video_post(
        self,
        filepath_or_url: str,
        title: str,
        description: str,
        user_id: str | Literal["me"] = "me",
        progress_callback: (
            Callable[
                [
                    float,
                    float,
                    float,
                    Literal["uploading", "publishing", "finished"],
                ],
                Coroutine[None, None, None],
            ]
            | None
        ) = None,
        wait_published: bool = True,
    ) -> FacebookPost:
        """Create a video post.

        You can't upload multiple videos at once, you can't mix
        photos and videos either by using graph api.

        Notes:
            Seems like all videos uploaded to facebook are converted into reels.
            There is an additional api for uploading reels, I don't know if I should
            create it too but for the meantime since this api has more freedom, no
            duration limit too and possibly no limit on how many videos you can upload
            for 24 hours, I will be using this method for now.

        Docs:
            https://developers.facebook.com/docs/video-api/guides/publishing
            https://developers.facebook.com/docs/video-api/guides/reels-publishing

        Args:
            filepath_or_url: The video file path or url.
            title: The title of the video.
            description: The description of the video.
            user_id: User ID or "me". The "me" is used on dev mode.
            progress_callback: The progress callback method, refer to docs how to create callback.
            wait_published: Wait for the video to be published for url videos. Default is True.

        Returns:
            The post object.

        """
        url_path = f"{user_id}/videos"

        # for url video
        if is_url_valid(filepath_or_url):
            params = {
                "access_token": self._access_token,
                "file_url": filepath_or_url,
                "title": title,
                "description": description,
            }

            response = await self._session.post(url_path, params=params, timeout=300)

            video_id = IdResponse.model_validate(response.json()).id

            if progress_callback is not None:
                await progress_callback(100.0, 100.0, 100.0, "finished")

            params = {"access_token": self._access_token, "fields": "status"}

            # wait for the video to be published
            while True and wait_published:
                response = await self._session.get(video_id, params=params)
                video_upload_status = VideoUploadStatus.model_validate(response.json())

                if video_upload_status.status.video_status == "ready":
                    break

                if video_upload_status.status.error is not None:
                    raise ValueError(video_upload_status.status.error.message)

                await asyncio.sleep(1)

            params["fields"] = "post_id"
            response = await self._session.get(video_id, params=params)

            feed_id = FeedIdResponse.model_validate(response.json()).post_id

            return FacebookPost(
                post_id=feed_id,
                access_token=self._access_token,
                session=self._session,
            )

        else:

            # check if file exists
            if not Path(filepath_or_url).exists():
                raise FileNotFoundError(f"File {filepath_or_url} does not exist.")

            # get file size
            file_size = Path(filepath_or_url).stat().st_size

            # for callback
            total_mb = file_size / (1024 * 1024)  # convert to mb
            uploaded_bytes = 0
            uploaded_mb = 0
            percentage = 0.0
            progress_callback_tasks: list[asyncio.Task[None]] = []

            # get upload session id
            params = {
                "upload_phase": "start",
                "file_size": file_size,
                "access_token": self._access_token,
            }

            response = await self._session.post(url_path, params=params)

            vsp = VideoStartPhaseResponse.model_validate(response.json())

            async with aopen(filepath_or_url, "rb") as video_file:
                while vsp.start_offset != vsp.end_offset:
                    # seek the current start offset and read the chunk
                    await video_file.seek(
                        vsp.start_offset
                    )  # pyright: ignore[reportUnusedCallResult]
                    chunk_size = vsp.end_offset - vsp.start_offset
                    chunk_data = await video_file.read(chunk_size)

                    # upload the chunk
                    transfer_payload = {
                        "upload_phase": "transfer",
                        "upload_session_id": vsp.upload_session_id,
                        "start_offset": vsp.start_offset,
                        "access_token": self._access_token,
                    }

                    files = {
                        "video_file_chunk": (
                            "chunk",
                            chunk_data,
                            "application/octet-stream",
                        )
                    }

                    response = await self._session.post(
                        url=url_path, data=transfer_payload, files=files, timeout=30
                    )

                    response_data = VideoUploadingLocalFileResponse.model_validate(
                        response.json()
                    )

                    vsp.start_offset = response_data.start_offset
                    vsp.end_offset = response_data.end_offset

                    # calculate progress
                    uploaded_bytes += chunk_size
                    uploaded_mb = uploaded_bytes / (1024 * 1024)
                    percentage = (uploaded_bytes / file_size) * 100

                    if progress_callback is not None:
                        progress_callback_tasks.append(
                            asyncio.create_task(
                                progress_callback(
                                    uploaded_mb, total_mb, percentage, "uploading"
                                )
                            )
                        )

                    else:
                        progress_bar = f"[{'█' * int(percentage // 2)}{' ' * (50 - int(percentage // 2))}]"
                        print(
                            f"\rUploading: {progress_bar} {uploaded_mb:.2f}MB / {total_mb:.2f}MB ({percentage:.2f}%)",
                            end="",
                        )

            # finish the upload session
            # and publish video post
            finish_payload = {
                "upload_phase": "finish",
                "upload_session_id": vsp.upload_session_id,
                "access_token": self._access_token,
                "title": title,
                "description": description,
            }

            response = await self._session.post(
                url_path, data=finish_payload, timeout=300
            )

            # wait until all progress callbacks are finished
            if progress_callback is not None:
                progress_callback_tasks.append(
                    asyncio.create_task(
                        progress_callback(uploaded_mb, total_mb, percentage, "finished")
                    )
                )

                await asyncio.gather(
                    *progress_callback_tasks
                )  # pyright: ignore[reportUnusedCallResult]

            print()  # will move cursor to the next line

            # get post id
            params = {"access_token": self._access_token, "fields": "status"}

            # wait for the video to be published
            while True and wait_published:
                response = await self._session.get(vsp.video_id, params=params)

                video_upload_status = VideoUploadStatus.model_validate(response.json())

                bytes_transferred = (
                    video_upload_status.status.uploading_phase.bytes_transfered
                )

                total_size = video_upload_status.status.uploading_phase.source_file_size

                if (
                    bytes_transferred is not None
                    and total_size is not None
                    and bytes_transferred > 0
                    and total_size > 0
                ):
                    _percentage = (bytes_transferred / total_size) * 100
                    # TODO add callback algorithm here
                    print(f"Video upload progress: {_percentage:.2f}%")

                if video_upload_status.status.video_status == "error":
                    # check who got errors
                    errors: list[str] = []

                    if video_upload_status.status.uploading_phase.errors is not None:
                        for error in video_upload_status.status.uploading_phase.errors:
                            errors.append(error.message + " code: " + str(error.code))

                    elif video_upload_status.status.processing_phase.errors is not None:
                        for error in video_upload_status.status.processing_phase.errors:
                            errors.append(error.message + " code: " + str(error.code))

                    raise Exception("Failed to upload video.\n" + ", ".join(errors))

                if video_upload_status.status.video_status == "ready":
                    # stop the loop
                    break

                if video_upload_status.status.error is not None:
                    raise Exception(
                        "Failed to upload video. "
                        + video_upload_status.status.error.message
                    )

                # avoid fast loop
                await asyncio.sleep(1)

            params["fields"] = "post_id"
            response = await self._session.get(vsp.video_id, params=params)

            response_data = FeedIdResponse.model_validate(response.json())

            return FacebookPost(
                post_id=response_data.post_id,
                access_token=self._access_token,
                session=self._session,
            )

    # ===============================================================
    # PROPERTIES
    # ===============================================================

    @property
    def id(self) -> str:
        """Page ID."""
        return self._id
