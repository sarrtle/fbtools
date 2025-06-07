"""Page object of Facebook node."""

import asyncio
from asyncio.tasks import Task
from mimetypes import guess_type
from os.path import basename, exists, getsize
from typing import Callable, Literal, override
from collections.abc import Coroutine
from aiofiles import open as aopen
from httpx import AsyncClient

from fbtools.official.models.page.post import FacebookPost
from fbtools.official.models.response.graph import (
    VideoStartPhaseResponse,
    VideoUploadStatus,
)
from fbtools.official.models.validation.page_response import PageDataItem


from fbtools.official.utilities.common import create_url_format, raise_for_status
from fbtools.official.utilities.graph_util import create_photo_id


class Page:
    """Page object of Facebook node.

    Attributes:
        name: The page name.
        category: The page category.
        tasks: The page tasks.
        access_token: The page access token.
        session: httpx async session of this node.

    """

    def __init__(self, page_data_item: PageDataItem):
        """Initialize Page.

        Args:
            page_data_item: The page data item from response.

        """
        # attributes
        self.name: str = page_data_item.name
        self.category: str = page_data_item.category
        self.access_token: str = page_data_item.access_token
        self.page_id: str = page_data_item.id

        # objects
        self.session: AsyncClient = self.create_session()
        self._headers: dict[str, str] = {"Content-Type": "application/json"}

    @classmethod
    def create_session(cls):
        """Create httpx async session of this node."""
        return AsyncClient(base_url="https://graph.facebook.com/", timeout=60)

    @classmethod
    async def from_access_token(
        cls, page_access_token: str, user_id: str | Literal["me"] = "me"
    ) -> "Page":
        """Create a page node from access token.

        Since the orignal initial setup requires page data item
        from the page response of getting the page data. An
        access token will request the page data and create the
        page data item.

        Args:
            page_access_token: The page access token.
            user_id: The user id or "me". The "me" is used on dev mode.

        Returns:
            The page node.

        Raises:
            ValidationError: If something went wrong during validation of api response.

        """
        # request page data from official api with access token
        params = {
            "access_token": page_access_token,
            "fields": "id,name,category, access_token",
        }
        response = await cls.create_session().get(f"{user_id}", params=params)

        # validate data
        page_data_item = PageDataItem.model_validate(response.json())

        # add data to Page node
        return Page(page_data_item=page_data_item)

    # validate page access token
    async def validate_access_token(self):
        """Will check if page access token is valid.

        Raises:
            PageValidationError: If page access token is invalid.

        """
        # global_brand_page_name name is for the page only
        params = {
            "access_token": self.access_token,
            "fields": "global_brand_page_name",
        }
        response = await self.session.get("me", params=params)
        raise_for_status(response)

    def save_page_access_token(
        self, page_access_token: str, filepath: str = "page_token.txt"
    ):
        """Save page access token.

        Args:
            page_access_token: The page access token.
            filepath: The file path to save the access token.

        """
        with open(filepath, "w") as f:
            f.write(page_access_token)

    # ========== USEFUL METHODS ==========

    # ===== Create attachment id for photos =====
    async def create_photo_id(
        self,
        photo_url_or_path: str,
        user_id: str | Literal["me"] = "me",
    ) -> str:
        """Upload photo to Facebook and get their photo id.

        Args:
            photo_url_or_path: The photo url or local path.
            user_id: The user id or "me". The "me" is used on dev/solo mode.
            attachmend_id_only: Whether to return the attachment id only without publishing.

        Raises:
            FileNotFoundError: If file does not exist.
            Exception: If something went wrong when `id` was not found.

        """
        return await create_photo_id(
            photo_url_or_path=photo_url_or_path,
            access_token=self.access_token,
            session=self.session,
            user_id=user_id,
        )

    # ===== Upload a local file to facebook =====
    async def upload_local_file(
        self, filepath: str, app_id: str, upload_id: str | None = None
    ) -> str:
        """Upload a local file to facebook.

        This is use for uploading a file to facebook.

        Notes:
            This was primarily used for uploading a video to facebook but
            when it was not working for me so I will just put this here
            just in case this is needed in the future.

        Args:
            filepath: The local file path of the video.
            app_id: The App ID of the facebook app.
            upload_id: The url link of previous upload session to resume upload.

        """
        # initialize the upload
        file_name = basename(filepath)
        file_size = getsize(filepath)
        file_type = guess_type(filepath)[0]

        url = create_url_format(f"{app_id}/uploads")
        params = {
            "file_name": file_name,
            "file_size": file_size,
            "file_type": file_type,
            "access_token": self.access_token,
        }

        if upload_id == None:
            response = await self.session.post(
                url=url, params=params, headers=self._headers
            )
            initialize_data: dict[str, str] = response.json()

            if "id" not in initialize_data:
                raise Exception("Failed to upload file." + response.text)

            upload_id = initialize_data["id"]

        # check if resume upload and and get the offset
        url = create_url_format(upload_id)
        headers: dict[str, str] = {"Authorization": f"OAuth {self.access_token}"}

        response = await self.session.get(url=url, headers=headers)
        offset_data: dict[str, int] = response.json()
        if "file_offset" not in offset_data:
            raise Exception("Failed to get file offset." + response.text)
        offset = offset_data.get("file_offset", 0)
        print("Resuming on this offset:", offset)

        # start the upload
        url = create_url_format(upload_id)
        headers["file_offset"] = str(offset)
        response_data: dict[str, str] = {}
        print("Uploading on this upload id:", upload_id)

        # async for chunk in read_file_in_chunks(filepath=filepath, start_offset=offset):
        from aiofiles import open as aopen

        async with aopen(filepath, "rb") as file:
            response = await self.session.post(
                url=url, headers=headers, content=await file.read()
            )
            response_data = response.json()

        if "h" not in response_data:
            raise Exception("Failed to get file header." + response.text)

        file_header = response_data["h"]

        return file_header

    # ===== Create a post to the feed =====
    async def create_post(
        self,
        message: str,
        images: list[str] | None = None,
        user_id: str | Literal["me"] = "me",
    ) -> FacebookPost:
        """Create a post.

        You can create a text post and an image post.

        Notes:
            You can only create this kind of post on this
            endpoint. Video post are separated and has a
            different process.

            You can upload multiple images in here too.

        Args:
            message: The message written in the post.
            images: If you wish to add images/videos to the post.
            user_id: The user id or "me". The "me" is used on dev/solo mode.

        """
        url = create_url_format(f"{user_id}/feed")
        data: dict[str, str | bool | list[dict[str, str]]] = {
            "message": message,
            "published": True,
            # schedule
            # schedule: "unix_timestamp_of_future_date"
        }
        params = {"access_token": self.access_token}

        if images:
            attached_media: list[dict[str, str]] = []

            for attachment in images:
                photo_id = await create_photo_id(
                    photo_url_or_path=attachment,
                    access_token=self.access_token,
                    session=self.session,
                )
                attached_media.append({"media_fbid": photo_id})

            data["attached_media"] = attached_media

        response = await self.session.post(
            url=url, json=data, params=params, headers=self._headers, timeout=30
        )

        response_data: dict[str, str] = response.json()

        if "id" not in response_data:
            raise Exception("Post was not created. " + str(response.text))

        post_id = response_data["id"]

        return FacebookPost(
            post_id=post_id, access_token=self.access_token, session=self.session
        )

    # ===== Upload video =====
    async def create_video_post(
        self,
        filepath_or_url: str,
        title: str,
        description: str,
        user_id: str | Literal["me"] = "me",
        progress_callback: (
            Callable[
                [float, float, float, Literal["uploading", "publishing", "finished"]],
                Coroutine[None, None, None],
            ]
            | None
        ) = None,
    ) -> FacebookPost:
        """Create a video post.

        You can't upload multiple videos at once, you can't
        mix photos and videos either by using the graph api.

        Args:
            filepath_or_url: The local path of the video or the url.
            title: The title of the video.
            description: The description of the video.
            user_id: The user id or "me". The "me" is used on dev/solo mode.
            progress_callback: The callable function for custom progress indicator.

        """
        # the base url for video uploads
        # Notes: The docs says the standard base url is now the
        #       graph.facebook.com not graph-video.facebook.com
        #       https://developers.facebook.com/docs/video-api/overview/
        url = create_url_format(f"{user_id}/videos")

        # for url video:
        if filepath_or_url.startswith("http"):
            params = {
                "access_token": self.access_token,
                "file_url": filepath_or_url,
                "title": title,
                "description": description,
            }
            response = await self.session.post(url=url, params=params, timeout=300)

            video_response: dict[str, str] = response.json()

            if "id" not in video_response:
                raise Exception("Video was not created. " + str(response.text))

            video_id = video_response["id"]
            post_id = f"{self.page_id}_{video_id}"

            if progress_callback is not None:
                await progress_callback(100.0, 100.0, 100.0, "finished")

            url = create_url_format(video_id)
            params = {"access_token": self.access_token, "fields": "status"}

            # wait for the video to be published
            while True:
                response = await self.session.get(url=url, params=params)
                video_upload_status = VideoUploadStatus.model_validate(response.json())

                if video_upload_status.status.video_status == "ready":
                    break

                if video_upload_status.status.error is not None:
                    raise Exception(video_upload_status.status.error.message)

                await asyncio.sleep(1)

            params["fields"] = "post_id"
            response = await self.session.get(url=url, params=params)
            response_data = response.json()

            if "post_id" not in response_data:
                raise Exception(
                    "Can't find post id after uploading the video. "
                    + str(response.text)
                )

            post_id = response_data["post_id"]

            return FacebookPost(
                post_id=post_id, access_token=self.access_token, session=self.session
            )

        # for local video
        else:

            # check if file exists
            if not exists(filepath_or_url):
                raise FileNotFoundError(f"File {filepath_or_url} does not exist.")

            # get file size
            file_size = getsize(filepath_or_url)

            # for callback
            total_mb = file_size / (1024 * 1024)  # conver to mb
            uploaded_bytes = 0  # track uploaded bytes
            uploaded_mb = 0  # track uploaded mb
            percentage = 0  # track percentage
            progress_callback_tasks: list[Task[None]] = []

            # get upload session id
            params = {
                "upload_phase": "start",
                "file_size": file_size,
                "access_token": self.access_token,
            }

            response = await self.session.post(url=url, params=params)
            vsp = VideoStartPhaseResponse.model_validate(response.json())

            # start upload by chunk
            async with aopen(filepath_or_url, "rb") as video_file:
                while vsp.start_offset != vsp.end_offset:
                    # seek the current start offset and read the chunk
                    await video_file.seek(vsp.start_offset)
                    chunk_size = vsp.end_offset - vsp.start_offset
                    chunk_data = await video_file.read(chunk_size)

                    # upload the chunk
                    transfer_payload = {
                        "upload_phase": "transfer",
                        "upload_session_id": vsp.upload_session_id,
                        "start_offset": vsp.start_offset,
                        "access_token": self.access_token,
                    }

                    files = {
                        "video_file_chunk": (
                            "chunk",
                            chunk_data,
                            "application/octet-stream",
                        ),
                    }

                    response = await self.session.post(
                        url=url, data=transfer_payload, files=files, timeout=30
                    )

                    response_data: dict[str, str] = response.json()

                    if "error" in response_data:
                        raise Exception(
                            "Failed to upload video chunk. " + response_data["error"]
                        )

                    vsp.start_offset = int(response_data["start_offset"])
                    vsp.end_offset = int(response_data["end_offset"])

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
            # and publish the video post
            finish_payload = {
                "upload_phase": "finish",
                "upload_session_id": vsp.upload_session_id,
                "access_token": self.access_token,
                "title": title,
                "description": description,
            }

            response = await self.session.post(url, data=finish_payload, timeout=300)

            # wait until all progress callbacks are done
            if progress_callback is not None:
                progress_callback_tasks.append(
                    asyncio.create_task(
                        progress_callback(uploaded_mb, total_mb, percentage, "finished")
                    )
                )
                await asyncio.gather(*progress_callback_tasks)

            print()  # will move the cursor to the next line

            # get post id
            url = create_url_format(vsp.video_id)
            params = {"access_token": self.access_token, "fields": "status"}

            # wait for the video to be published
            while True:
                response = await self.session.get(url=url, params=params)
                video_upload_status = VideoUploadStatus.model_validate(response.json())

                if video_upload_status.status.video_status == "ready":
                    break

                if video_upload_status.status.error is not None:
                    raise Exception(
                        "Failed to upload video. "
                        + video_upload_status.status.error.message
                    )

                await asyncio.sleep(1)

            params["fields"] = "post_id"
            response = await self.session.get(url=url, params=params)
            response_data = response.json()

            if "post_id" not in response_data:
                raise Exception(
                    "Can't find post id after uploading the video. "
                    + str(response.text)
                )

            post_id = f"{self.page_id}_{response_data['post_id']}"

            return FacebookPost(
                post_id=post_id,
                access_token=self.access_token,
                session=self.session,
            )

    @override
    def __repr__(self):
        return f"Page(name={self.name}, category={self.category}, access_token={self.access_token[:5]}...)"
