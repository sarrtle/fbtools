"""Page object of Facebook node."""

from typing import Literal, override
from httpx import AsyncClient

from fbtools.official.exceptions import PageValidationError
from fbtools.official.models.extra.attachments import Attachment
from fbtools.official.models.page.post import FacebookPost
from fbtools.official.models.response.facebook_post_response import FacebookPostResponse
from fbtools.official.models.validation.page_response import PageDataItem


from fbtools.official.utilities.common import create_url_format
from fbtools.official.utilities.graph_util import create_page_photo_id


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

        # objects
        self.session: AsyncClient = self.create_session()
        self._headers: dict[str, str] = {"Content-Type": "application/json"}

    @classmethod
    def create_session(cls):
        """Create httpx async session of this node."""
        return AsyncClient(base_url="https://graph.facebook.com/")

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

        if response.status_code != 200:
            raise PageValidationError(response.text)

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

    async def create_photo_id(
        self, photo_url_or_path: str, user_id: str | Literal["me"] = "me"
    ):
        """Upload photo to Facebook and get their photo id.

        Args:
            photo_url_or_path: The photo url or local path.
            user_id: The user id or "me". The "me" is used on dev/solo mode.

        Raises:
            FileNotFoundError: If file does not exist.
            Exception: If something went wrong when `id` was not found.

        """
        return await create_page_photo_id(
            photo_url_or_path=photo_url_or_path,
            access_token=self.access_token,
            session=self.session,
            user_id=user_id,
        )

    async def get_post_object(self, post_id: str) -> FacebookPost:
        """Get post data and return as an object.

        Args:
            post_id: The id of the post.

        Returns:
            The FacebookPost object.

        Raises:
            ValidationError: If something went wrong during validation of api response.

        """
        url = create_url_format(post_id)
        fields = [
            "id",
            "message",
            "status_type",
            "story",
            "created_time",
            "target",
            "attachments.limit(10){media,description,type,title,subattachments,unshimmed_url,target}",
        ]
        params = {
            "access_token": self.access_token,
            "fields": ",".join(fields),
        }
        response = await self.session.get(url, params=params, headers=self._headers)

        response_object = FacebookPostResponse.model_validate(response.json())

        # check if the post is a bio
        is_bio = False

        # process attachments
        attachments: list[Attachment] = []
        if response_object.attachments:
            attachment_data = response_object.attachments.data[0]

            # for many multiple attachments
            if attachment_data.subattachments:
                for subattachments in attachment_data.subattachments.data:
                    # what I need
                    # attachment_id
                    attachment_id = subattachments.target.id
                    # src
                    # multiple videos and images has similar
                    # media properties `subattachment.media.image`

                    # if video
                    media_type = "video"
                    if (
                        subattachments.type == "video"
                        and subattachments.media.source != None
                    ):
                        src = subattachments.media.source

                    # if image
                    elif subattachments.type == "photo":
                        media_type = "image"
                        src = subattachments.media.image.src

                    else:
                        raise Exception(f"Unknown media type: {subattachments.type}")

                    # thumbnail_src
                    # since image doesn't have a thumbnail, the src
                    # is their real image but the video uses this as
                    # their thumbnail image
                    thumbnail_src = subattachments.media.image.src

                    # facebook_url
                    # The URL to facebook post that views the attachment.
                    facebook_url = subattachments.target.url

                    # description
                    description = subattachments.description

                    # height
                    subattachments.media.image.height
                    # width
                    subattachments.media.image.width

                    attachments.append(
                        Attachment(
                            attachment_id=attachment_id,
                            src=src,
                            thumbnail_src=thumbnail_src,
                            facebook_url=facebook_url,
                            description=description,
                            height=subattachments.media.image.height,
                            width=subattachments.media.image.width,
                            media_type=media_type,
                        )
                    )

            # if bio
            # bio uses attachments too
            elif attachment_data.type == "native_templates":
                is_bio = True
                # since bio don't have a message, it will use the
                # attachment description
                response_object.message = attachment_data.description

            # if single attachment
            else:

                assert (
                    attachment_data.media is not None
                ), "Attachment media is None on single attachment."

                attachment_id = attachment_data.target.id

                # if video
                media_type = "video"
                if (
                    attachment_data.type == "video_inline"
                    and attachment_data.media.source != None
                ):
                    src = attachment_data.media.source

                # if image
                elif attachment_data.type in ["photo", "album", "profile_media"]:
                    media_type = "image"
                    src = attachment_data.media.image.src
                else:
                    raise Exception(f"Unknown Attachment type {attachment_data.type}.")

                # if image_profile
                if attachment_data.type == "profile_media":
                    media_type = "image_profile"
                    response_object.status_type = "added_profile_photo"

                # if video reel
                if "reel" in attachment_data.target.url:
                    media_type = "video_reel"
                    response_object.status_type = "added_reel"

                # thumbnail_src
                # since image doesn't have a thumbnail, the src
                # is their real image but the video uses this as
                # their thumbnail image
                thumbnail_src = attachment_data.media.image.src

                # facebook_url
                # The URL to facebook post that views the attachment.
                facebook_url = attachment_data.target.url

                # description
                description = attachment_data.description

                attachments.append(
                    Attachment(
                        attachment_id=attachment_id,
                        src=src,
                        thumbnail_src=thumbnail_src,
                        facebook_url=facebook_url,
                        description=description,
                        height=attachment_data.media.image.height,
                        width=attachment_data.media.image.width,
                        media_type=media_type,
                    )
                )

        if is_bio:
            response_object.status_type = "bio_status_update"

        return FacebookPost(
            post_id=response_object.id,
            message=response_object.message,
            status_type=response_object.status_type,
            story=response_object.story,
            created_time=response_object.created_time,
            attachments=attachments or None,
            access_token=self.access_token,
            session=self.session,
        )

    @override
    def __repr__(self):
        return f"Page(name={self.name}, category={self.category}, access_token={self.access_token[:5]}...)"
