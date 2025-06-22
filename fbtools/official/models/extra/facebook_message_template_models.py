"""Typedict models for facebook message templates."""

from typing import Literal, NotRequired, TypedDict


class QuickReplies_Dict(TypedDict):
    """Types for quick replies.

    Keys:
        content_type:
            Required. Must be one of the following
                - text: Sends a text button
                - user_phone_number: Sends a button allowing recipient to send the phone number associated with their account.
                - user_email: Sends a button allowing recipient to send the email associated with their account.

        title:
            Required. If content_type is 'text'. The text to display on the quick reply button is 20 character limit.

        payload:
            Required. if content_type is 'text'. Custom data that will be sent back to you via the messaging_postbacks webhook event.
            1000 character limit.

        image_url:
            Optional. URL of image to display on the quick reply button for text quick replies.
            Image should be a minimum of 24px x 24px. Larger images will be automatically cropped and resized.

    """

    content_type: Literal["text", "user_phone_number", "user_email"]
    title: str
    payload: str
    image_url: NotRequired[str | None]


class _GenericTemplateDefaultAction_Dict(TypedDict):
    """Types for generic templates."""

    type: Literal["web_url"]
    url: str
    webview_height_ratio: NotRequired[Literal["tall", "compact", "full"]]


class GenericTemplate_Dict(TypedDict):
    """Types for generic templates.

    Keys:
        title:
            Required. Text to display in the template.
        image_url:
            Required. URL of the image to display in the template.
        subtitle:
            Required. Text to display in the template.
        default_action:
            Optional. Default action to take when a user taps on the template.

    Notes:
        See reference:
        https://developers.facebook.com/docs/messenger-platform/reference/templates#available_templates

    """

    title: str
    image_url: str
    subtitle: str
    default_action: NotRequired[_GenericTemplateDefaultAction_Dict]
    buttons: list["ButtonTemplatePostBack_Dict | ButtonTemplateWeb_Dict"]


class ButtonTemplateWeb_Dict(TypedDict):
    """Types for button templates.

    Keys:
        type:
            Always 'web_url'
        url:
            Required. URL of the link to open when the button is clicked.
        title:
            Required. Text to display on the button.
        webview_height_ratio:
            Optional. One of 'tall', 'compact' or 'full'. Default is 'full'.

    Notes:
        Other keys might not be important but see the reference for more information:
        https://developers.facebook.com/docs/messenger-platform/reference/buttons

    """

    type: Literal["web_url"]
    url: str
    title: str

    # default is full
    webview_height_ratio: NotRequired[Literal["tall", "compact", "full"]]

    # Probably not important for now
    # messenger_extensions: NotRequired[bool]
    # fallback_url: NotRequired[str]
    # webview_share_button: NotRequired[Literal["hide"]]


class ButtonTemplatePostBack_Dict(TypedDict):
    """Types for button templates."""

    type: Literal["postback"]
    title: str
    payload: str
