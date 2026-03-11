"""Async Python client for the Wago WhatsApp API (MultiDevice)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Type, TypeVar, Union

import aiohttp
from aiohttp import BasicAuth, FormData

from .exceptions import (
    WagoBadRequestError,
    WagoConflictError,
    WagoConnectionError,
    WagoError,
    WagoInternalServerError,
    WagoNotFoundError,
    WagoUnauthorizedError,
)
from .models import (
    ArchiveChatResponse,
    AppStatusResponse,
    BusinessProfileResponse,
    ChatListResponse,
    ChatMessagesResponse,
    ChatwootSyncResponse,
    ChatwootSyncStatusResponse,
    CreateGroupResponse,
    DeviceAddResponse,
    DeviceInfoResponse,
    DeviceListResponse,
    DeviceResponse,
    DeviceStatusResponse,
    DownloadMediaResponse,
    GenericResponse,
    GetGroupInviteLinkResponse,
    GroupInfoFromLinkResponse,
    GroupInfoResponse,
    GroupParticipantRequestListResponse,
    GroupParticipantsResponse,
    LabelChatResponse,
    LoginResponse,
    LoginWithCodeResponse,
    ManageParticipantResponse,
    MyListContactsResponse,
    NewsletterResponse,
    PinChatResponse,
    SendResponse,
    SetDisappearingTimerResponse,
    SetGroupPhotoResponse,
    UserAvatarResponse,
    UserCheckResponse,
    UserGroupResponse,
    UserInfoResponse,
    UserPrivacyResponse,
)

T = TypeVar("T")
logger = logging.getLogger("py_wago")

_STATUS_ERRORS: Dict[int, Type[WagoError]] = {
    400: WagoBadRequestError,
    401: WagoUnauthorizedError,
    404: WagoNotFoundError,
    409: WagoConflictError,
    500: WagoInternalServerError,
}


class WagoClient:
    """Async client for the Wago WhatsApp API.

    Args:
        base_url: Base URL of the Wago API server (e.g. ``https://wago.example.com``).
        username: Username for HTTP Basic authentication.
        password: Password for HTTP Basic authentication.
        device_id: Default device ID sent via ``X-Device-Id`` header.
            Can be overridden per-call.
        timeout: Default request timeout in seconds.
        session: Optional pre-existing :class:`aiohttp.ClientSession`.
            When provided the caller is responsible for closing it.
        custom_headers: Optional dictionary of extra HTTP headers to include
            in every request (e.g. Cloudflare Access service-auth headers).
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        *,
        device_id: Optional[str] = None,
        timeout: float = 30.0,
        session: Optional[aiohttp.ClientSession] = None,
        custom_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._auth = BasicAuth(username, password)
        self._device_id = device_id
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._external_session = session is not None
        self._session = session
        self._custom_headers: Dict[str, str] = dict(custom_headers) if custom_headers else {}

    # ── lifecycle ─────────────────────────────────────────────────────────

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                auth=self._auth,
                timeout=self._timeout,
            )
        return self._session

    async def close(self) -> None:
        """Close the underlying HTTP session (no-op if externally managed)."""
        if self._session and not self._external_session:
            await self._session.close()

    async def __aenter__(self) -> "WagoClient":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()

    # ── internals ─────────────────────────────────────────────────────────

    def _headers(self, device_id: Optional[str] = None) -> Dict[str, str]:
        headers: Dict[str, str] = dict(self._custom_headers)
        did = device_id or self._device_id
        if did:
            headers["X-Device-Id"] = did
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        *,
        device_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[FormData] = None,
    ) -> Dict[str, Any]:
        session = await self._get_session()
        url = f"{self._base_url}{path}"
        headers = self._headers(device_id)

        # Strip None values from params
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        try:
            async with session.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json,
                data=data,
            ) as resp:
                if resp.content_type == "text/csv":
                    text = await resp.text()
                    return {"code": "SUCCESS", "message": "CSV export", "results": text}

                body = await resp.json()

                if resp.status >= 400:
                    exc_cls = _STATUS_ERRORS.get(resp.status, WagoError)
                    raise exc_cls(
                        message=body.get("message", resp.reason or "Unknown error"),
                        code=body.get("code"),
                        status=resp.status,
                        details=body.get("results"),
                    )
                return body
        except aiohttp.ClientError as exc:
            raise WagoConnectionError(str(exc)) from exc

    # ── helpers ───────────────────────────────────────────────────────────

    def _build_form(
        self,
        fields: Dict[str, Any],
        file_field: Optional[str] = None,
        file: Optional[Union[BinaryIO, bytes, str, Path]] = None,
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> FormData:
        fd = FormData()
        for key, val in fields.items():
            if val is not None:
                fd.add_field(key, str(val))
        if file_field and file is not None:
            if isinstance(file, (str, Path)):
                file = open(file, "rb")  # noqa: SIM115
            fd.add_field(
                file_field,
                file,
                filename=filename or "upload",
                content_type=content_type or "application/octet-stream",
            )
        return fd

    # ══════════════════════════════════════════════════════════════════════
    #  APP
    # ══════════════════════════════════════════════════════════════════════

    async def app_login(self, *, device_id: Optional[str] = None) -> LoginResponse:
        """Login to WhatsApp server (QR code)."""
        data = await self._request("GET", "/app/login", device_id=device_id)
        return LoginResponse(**data)

    async def app_login_with_code(
        self, phone: str, *, device_id: Optional[str] = None
    ) -> LoginWithCodeResponse:
        """Login with pairing code."""
        data = await self._request(
            "GET", "/app/login-with-code", device_id=device_id, params={"phone": phone}
        )
        return LoginWithCodeResponse(**data)

    async def app_logout(self, *, device_id: Optional[str] = None) -> GenericResponse:
        """Remove database and logout."""
        data = await self._request("GET", "/app/logout", device_id=device_id)
        return GenericResponse(**data)

    async def app_reconnect(self, *, device_id: Optional[str] = None) -> GenericResponse:
        """Reconnect to WhatsApp server."""
        data = await self._request("GET", "/app/reconnect", device_id=device_id)
        return GenericResponse(**data)

    async def app_devices(self) -> DeviceResponse:
        """Get list of connected devices."""
        data = await self._request("GET", "/app/devices")
        return DeviceResponse(**data)

    async def app_status(self, *, device_id: Optional[str] = None) -> AppStatusResponse:
        """Get connection status."""
        data = await self._request("GET", "/app/status", device_id=device_id)
        return AppStatusResponse(**data)

    # ══════════════════════════════════════════════════════════════════════
    #  DEVICE MANAGEMENT
    # ══════════════════════════════════════════════════════════════════════

    async def list_devices(self) -> DeviceListResponse:
        """List all registered devices."""
        data = await self._request("GET", "/devices")
        return DeviceListResponse(**data)

    async def add_device(self, device_id: Optional[str] = None) -> DeviceAddResponse:
        """Add a new device slot."""
        body: Dict[str, Any] = {}
        if device_id:
            body["device_id"] = device_id
        data = await self._request("POST", "/devices", json=body)
        return DeviceAddResponse(**data)

    async def get_device(self, device_id: str) -> DeviceInfoResponse:
        """Get device info."""
        data = await self._request("GET", f"/devices/{device_id}")
        return DeviceInfoResponse(**data)

    async def remove_device(self, device_id: str) -> GenericResponse:
        """Remove a device."""
        data = await self._request("DELETE", f"/devices/{device_id}")
        return GenericResponse(**data)

    async def login_device(self, device_id: str) -> LoginResponse:
        """Initiate QR code login for a device."""
        data = await self._request("GET", f"/devices/{device_id}/login")
        return LoginResponse(**data)

    async def login_device_with_code(self, device_id: str, phone: str) -> LoginWithCodeResponse:
        """Initiate pairing code login for a device."""
        data = await self._request(
            "POST", f"/devices/{device_id}/login/code", params={"phone": phone}
        )
        return LoginWithCodeResponse(**data)

    async def logout_device(self, device_id: str) -> GenericResponse:
        """Logout a device from WhatsApp."""
        data = await self._request("POST", f"/devices/{device_id}/logout")
        return GenericResponse(**data)

    async def reconnect_device(self, device_id: str) -> GenericResponse:
        """Reconnect a device to WhatsApp."""
        data = await self._request("POST", f"/devices/{device_id}/reconnect")
        return GenericResponse(**data)

    async def get_device_status(self, device_id: str) -> DeviceStatusResponse:
        """Get device connection status."""
        data = await self._request("GET", f"/devices/{device_id}/status")
        return DeviceStatusResponse(**data)

    # ══════════════════════════════════════════════════════════════════════
    #  USER
    # ══════════════════════════════════════════════════════════════════════

    async def user_info(
        self, phone: str, *, device_id: Optional[str] = None
    ) -> UserInfoResponse:
        """Get user info."""
        data = await self._request(
            "GET", "/user/info", device_id=device_id, params={"phone": phone}
        )
        return UserInfoResponse(**data)

    async def user_avatar(
        self,
        phone: str,
        *,
        is_preview: Optional[bool] = None,
        is_community: Optional[bool] = None,
        device_id: Optional[str] = None,
    ) -> UserAvatarResponse:
        """Get user avatar."""
        data = await self._request(
            "GET",
            "/user/avatar",
            device_id=device_id,
            params={"phone": phone, "is_preview": is_preview, "is_community": is_community},
        )
        return UserAvatarResponse(**data)

    async def user_change_avatar(
        self,
        avatar: Union[BinaryIO, bytes, str, Path],
        *,
        filename: str = "avatar.jpg",
        device_id: Optional[str] = None,
    ) -> GenericResponse:
        """Change user avatar."""
        fd = self._build_form({}, file_field="avatar", file=avatar, filename=filename)
        data = await self._request("POST", "/user/avatar", device_id=device_id, data=fd)
        return GenericResponse(**data)

    async def user_change_push_name(
        self, push_name: str, *, device_id: Optional[str] = None
    ) -> GenericResponse:
        """Change display (push) name."""
        data = await self._request(
            "POST", "/user/pushname", device_id=device_id, json={"push_name": push_name}
        )
        return GenericResponse(**data)

    async def user_my_privacy(self, *, device_id: Optional[str] = None) -> UserPrivacyResponse:
        """Get privacy settings."""
        data = await self._request("GET", "/user/my/privacy", device_id=device_id)
        return UserPrivacyResponse(**data)

    async def user_my_groups(self, *, device_id: Optional[str] = None) -> UserGroupResponse:
        """Get list of joined groups (max 500)."""
        data = await self._request("GET", "/user/my/groups", device_id=device_id)
        return UserGroupResponse(**data)

    async def user_my_newsletters(
        self, *, device_id: Optional[str] = None
    ) -> NewsletterResponse:
        """Get list of newsletters."""
        data = await self._request("GET", "/user/my/newsletters", device_id=device_id)
        return NewsletterResponse(**data)

    async def user_my_contacts(
        self, *, device_id: Optional[str] = None
    ) -> MyListContactsResponse:
        """Get list of contacts."""
        data = await self._request("GET", "/user/my/contacts", device_id=device_id)
        return MyListContactsResponse(**data)

    async def user_check(
        self, phone: str, *, device_id: Optional[str] = None
    ) -> UserCheckResponse:
        """Check if a phone number is on WhatsApp."""
        data = await self._request(
            "GET", "/user/check", device_id=device_id, params={"phone": phone}
        )
        return UserCheckResponse(**data)

    async def user_business_profile(
        self, phone: str, *, device_id: Optional[str] = None
    ) -> BusinessProfileResponse:
        """Get business profile information."""
        data = await self._request(
            "GET", "/user/business-profile", device_id=device_id, params={"phone": phone}
        )
        return BusinessProfileResponse(**data)

    # ══════════════════════════════════════════════════════════════════════
    #  SEND
    # ══════════════════════════════════════════════════════════════════════

    async def send_message(
        self,
        phone: str,
        message: str,
        *,
        reply_message_id: Optional[str] = None,
        is_forwarded: Optional[bool] = None,
        duration: Optional[int] = None,
        mentions: Optional[List[str]] = None,
        device_id: Optional[str] = None,
    ) -> SendResponse:
        """Send a text message."""
        body: Dict[str, Any] = {"phone": phone, "message": message}
        if reply_message_id is not None:
            body["reply_message_id"] = reply_message_id
        if is_forwarded is not None:
            body["is_forwarded"] = is_forwarded
        if duration is not None:
            body["duration"] = duration
        if mentions is not None:
            body["mentions"] = mentions

        data = await self._request("POST", "/send/message", device_id=device_id, json=body)
        return SendResponse(**data)

    async def send_image(
        self,
        phone: str,
        *,
        image: Optional[Union[BinaryIO, bytes, str, Path]] = None,
        image_url: Optional[str] = None,
        caption: Optional[str] = None,
        view_once: Optional[bool] = None,
        compress: Optional[bool] = None,
        is_forwarded: Optional[bool] = None,
        duration: Optional[int] = None,
        filename: str = "image.jpg",
        device_id: Optional[str] = None,
    ) -> SendResponse:
        """Send an image (file or URL)."""
        fields: Dict[str, Any] = {"phone": phone}
        if caption is not None:
            fields["caption"] = caption
        if view_once is not None:
            fields["view_once"] = str(view_once).lower()
        if compress is not None:
            fields["compress"] = str(compress).lower()
        if is_forwarded is not None:
            fields["is_forwarded"] = str(is_forwarded).lower()
        if duration is not None:
            fields["duration"] = duration
        if image_url is not None:
            fields["image_url"] = image_url

        fd = self._build_form(
            fields,
            file_field="image" if image else None,
            file=image,
            filename=filename,
            content_type="image/jpeg",
        )
        data = await self._request("POST", "/send/image", device_id=device_id, data=fd)
        return SendResponse(**data)

    async def send_audio(
        self,
        phone: str,
        *,
        audio: Optional[Union[BinaryIO, bytes, str, Path]] = None,
        audio_url: Optional[str] = None,
        is_forwarded: Optional[bool] = None,
        duration: Optional[int] = None,
        filename: str = "audio.mp3",
        device_id: Optional[str] = None,
    ) -> SendResponse:
        """Send an audio file (file or URL)."""
        fields: Dict[str, Any] = {"phone": phone}
        if audio_url is not None:
            fields["audio_url"] = audio_url
        if is_forwarded is not None:
            fields["is_forwarded"] = str(is_forwarded).lower()
        if duration is not None:
            fields["duration"] = duration

        fd = self._build_form(
            fields,
            file_field="audio" if audio else None,
            file=audio,
            filename=filename,
            content_type="audio/mpeg",
        )
        data = await self._request("POST", "/send/audio", device_id=device_id, data=fd)
        return SendResponse(**data)

    async def send_file(
        self,
        phone: str,
        *,
        file: Optional[Union[BinaryIO, bytes, str, Path]] = None,
        caption: Optional[str] = None,
        is_forwarded: Optional[bool] = None,
        duration: Optional[int] = None,
        filename: str = "document",
        device_id: Optional[str] = None,
    ) -> SendResponse:
        """Send a file/document."""
        fields: Dict[str, Any] = {"phone": phone}
        if caption is not None:
            fields["caption"] = caption
        if is_forwarded is not None:
            fields["is_forwarded"] = str(is_forwarded).lower()
        if duration is not None:
            fields["duration"] = duration

        fd = self._build_form(
            fields,
            file_field="file" if file else None,
            file=file,
            filename=filename,
        )
        data = await self._request("POST", "/send/file", device_id=device_id, data=fd)
        return SendResponse(**data)

    async def send_sticker(
        self,
        phone: str,
        *,
        sticker: Optional[Union[BinaryIO, bytes, str, Path]] = None,
        sticker_url: Optional[str] = None,
        is_forwarded: Optional[bool] = None,
        duration: Optional[int] = None,
        filename: str = "sticker.webp",
        device_id: Optional[str] = None,
    ) -> SendResponse:
        """Send a sticker (auto-converts to WebP)."""
        fields: Dict[str, Any] = {"phone": phone}
        if sticker_url is not None:
            fields["sticker_url"] = sticker_url
        if is_forwarded is not None:
            fields["is_forwarded"] = str(is_forwarded).lower()
        if duration is not None:
            fields["duration"] = duration

        fd = self._build_form(
            fields,
            file_field="sticker" if sticker else None,
            file=sticker,
            filename=filename,
            content_type="image/webp",
        )
        data = await self._request("POST", "/send/sticker", device_id=device_id, data=fd)
        return SendResponse(**data)

    async def send_video(
        self,
        phone: str,
        *,
        video: Optional[Union[BinaryIO, bytes, str, Path]] = None,
        video_url: Optional[str] = None,
        caption: Optional[str] = None,
        view_once: Optional[bool] = None,
        compress: Optional[bool] = None,
        is_forwarded: Optional[bool] = None,
        duration: Optional[int] = None,
        filename: str = "video.mp4",
        device_id: Optional[str] = None,
    ) -> SendResponse:
        """Send a video (file or URL)."""
        fields: Dict[str, Any] = {"phone": phone}
        if caption is not None:
            fields["caption"] = caption
        if view_once is not None:
            fields["view_once"] = str(view_once).lower()
        if compress is not None:
            fields["compress"] = str(compress).lower()
        if video_url is not None:
            fields["video_url"] = video_url
        if is_forwarded is not None:
            fields["is_forwarded"] = str(is_forwarded).lower()
        if duration is not None:
            fields["duration"] = duration

        fd = self._build_form(
            fields,
            file_field="video" if video else None,
            file=video,
            filename=filename,
            content_type="video/mp4",
        )
        data = await self._request("POST", "/send/video", device_id=device_id, data=fd)
        return SendResponse(**data)

    async def send_contact(
        self,
        phone: str,
        contact_name: str,
        contact_phone: str,
        *,
        is_forwarded: Optional[bool] = None,
        duration: Optional[int] = None,
        device_id: Optional[str] = None,
    ) -> SendResponse:
        """Send a contact card."""
        body: Dict[str, Any] = {
            "phone": phone,
            "contact_name": contact_name,
            "contact_phone": contact_phone,
        }
        if is_forwarded is not None:
            body["is_forwarded"] = is_forwarded
        if duration is not None:
            body["duration"] = duration
        data = await self._request("POST", "/send/contact", device_id=device_id, json=body)
        return SendResponse(**data)

    async def send_link(
        self,
        phone: str,
        link: str,
        *,
        caption: Optional[str] = None,
        is_forwarded: Optional[bool] = None,
        duration: Optional[int] = None,
        device_id: Optional[str] = None,
    ) -> SendResponse:
        """Send a link with optional caption."""
        body: Dict[str, Any] = {"phone": phone, "link": link}
        if caption is not None:
            body["caption"] = caption
        if is_forwarded is not None:
            body["is_forwarded"] = is_forwarded
        if duration is not None:
            body["duration"] = duration
        data = await self._request("POST", "/send/link", device_id=device_id, json=body)
        return SendResponse(**data)

    async def send_location(
        self,
        phone: str,
        latitude: str,
        longitude: str,
        *,
        is_forwarded: Optional[bool] = None,
        duration: Optional[int] = None,
        device_id: Optional[str] = None,
    ) -> SendResponse:
        """Send a location pin."""
        body: Dict[str, Any] = {
            "phone": phone,
            "latitude": latitude,
            "longitude": longitude,
        }
        if is_forwarded is not None:
            body["is_forwarded"] = is_forwarded
        if duration is not None:
            body["duration"] = duration
        data = await self._request("POST", "/send/location", device_id=device_id, json=body)
        return SendResponse(**data)

    async def send_poll(
        self,
        phone: str,
        question: str,
        options: List[str],
        max_answer: int,
        *,
        duration: Optional[int] = None,
        device_id: Optional[str] = None,
    ) -> SendResponse:
        """Send a poll."""
        body: Dict[str, Any] = {
            "phone": phone,
            "question": question,
            "options": options,
            "max_answer": max_answer,
        }
        if duration is not None:
            body["duration"] = duration
        data = await self._request("POST", "/send/poll", device_id=device_id, json=body)
        return SendResponse(**data)

    async def send_presence(
        self,
        presence_type: str,
        *,
        device_id: Optional[str] = None,
    ) -> SendResponse:
        """Send presence status (``available`` or ``unavailable``)."""
        data = await self._request(
            "POST", "/send/presence", device_id=device_id, json={"type": presence_type}
        )
        return SendResponse(**data)

    async def send_chat_presence(
        self,
        phone: str,
        action: str,
        *,
        device_id: Optional[str] = None,
    ) -> SendResponse:
        """Send typing indicator (``start`` or ``stop``)."""
        data = await self._request(
            "POST",
            "/send/chat-presence",
            device_id=device_id,
            json={"phone": phone, "action": action},
        )
        return SendResponse(**data)

    # ══════════════════════════════════════════════════════════════════════
    #  MESSAGE
    # ══════════════════════════════════════════════════════════════════════

    async def revoke_message(
        self,
        message_id: str,
        phone: str,
        *,
        device_id: Optional[str] = None,
    ) -> SendResponse:
        """Revoke (unsend) a message."""
        data = await self._request(
            "POST",
            f"/message/{message_id}/revoke",
            device_id=device_id,
            json={"phone": phone},
        )
        return SendResponse(**data)

    async def delete_message(
        self,
        message_id: str,
        phone: str,
        *,
        device_id: Optional[str] = None,
    ) -> SendResponse:
        """Delete a message locally."""
        data = await self._request(
            "POST",
            f"/message/{message_id}/delete",
            device_id=device_id,
            json={"phone": phone},
        )
        return SendResponse(**data)

    async def react_message(
        self,
        message_id: str,
        phone: str,
        emoji: str,
        *,
        device_id: Optional[str] = None,
    ) -> SendResponse:
        """React to a message with an emoji."""
        data = await self._request(
            "POST",
            f"/message/{message_id}/reaction",
            device_id=device_id,
            json={"phone": phone, "emoji": emoji},
        )
        return SendResponse(**data)

    async def update_message(
        self,
        message_id: str,
        phone: str,
        message: str,
        *,
        device_id: Optional[str] = None,
    ) -> SendResponse:
        """Edit a sent message (within 15 min window)."""
        data = await self._request(
            "POST",
            f"/message/{message_id}/update",
            device_id=device_id,
            json={"phone": phone, "message": message},
        )
        return SendResponse(**data)

    async def read_message(
        self,
        message_id: str,
        phone: str,
        *,
        device_id: Optional[str] = None,
    ) -> SendResponse:
        """Mark a message as read."""
        data = await self._request(
            "POST",
            f"/message/{message_id}/read",
            device_id=device_id,
            json={"phone": phone},
        )
        return SendResponse(**data)

    async def star_message(
        self,
        message_id: str,
        phone: str,
        *,
        device_id: Optional[str] = None,
    ) -> GenericResponse:
        """Star a message."""
        data = await self._request(
            "POST",
            f"/message/{message_id}/star",
            device_id=device_id,
            json={"phone": phone},
        )
        return GenericResponse(**data)

    async def unstar_message(
        self,
        message_id: str,
        phone: str,
        *,
        device_id: Optional[str] = None,
    ) -> GenericResponse:
        """Unstar a message."""
        data = await self._request(
            "POST",
            f"/message/{message_id}/unstar",
            device_id=device_id,
            json={"phone": phone},
        )
        return GenericResponse(**data)

    async def download_message_media(
        self,
        message_id: str,
        phone: str,
        *,
        device_id: Optional[str] = None,
    ) -> DownloadMediaResponse:
        """Download media from a message (returns base64-encoded data)."""
        data = await self._request(
            "GET",
            f"/message/{message_id}/download",
            device_id=device_id,
            params={"phone": phone},
        )
        return DownloadMediaResponse(**data)

    # ══════════════════════════════════════════════════════════════════════
    #  CHAT
    # ══════════════════════════════════════════════════════════════════════

    async def list_chats(
        self,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        search: Optional[str] = None,
        has_media: Optional[bool] = None,
        archived: Optional[bool] = None,
        device_id: Optional[str] = None,
    ) -> ChatListResponse:
        """Get list of chats with pagination."""
        data = await self._request(
            "GET",
            "/chats",
            device_id=device_id,
            params={
                "limit": limit,
                "offset": offset,
                "search": search,
                "has_media": has_media,
                "archived": archived,
            },
        )
        return ChatListResponse(**data)

    async def get_chat_messages(
        self,
        chat_jid: str,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        media_only: Optional[bool] = None,
        is_from_me: Optional[bool] = None,
        search: Optional[str] = None,
        device_id: Optional[str] = None,
    ) -> ChatMessagesResponse:
        """Get messages from a specific chat."""
        data = await self._request(
            "GET",
            f"/chat/{chat_jid}/messages",
            device_id=device_id,
            params={
                "limit": limit,
                "offset": offset,
                "start_time": start_time,
                "end_time": end_time,
                "media_only": media_only,
                "is_from_me": is_from_me,
                "search": search,
            },
        )
        return ChatMessagesResponse(**data)

    async def label_chat(
        self,
        chat_jid: str,
        label_id: str,
        label_name: str,
        labeled: bool,
        *,
        device_id: Optional[str] = None,
    ) -> LabelChatResponse:
        """Apply or remove a label from a chat."""
        data = await self._request(
            "POST",
            f"/chat/{chat_jid}/label",
            device_id=device_id,
            json={"label_id": label_id, "label_name": label_name, "labeled": labeled},
        )
        return LabelChatResponse(**data)

    async def pin_chat(
        self,
        chat_jid: str,
        pinned: bool,
        *,
        device_id: Optional[str] = None,
    ) -> PinChatResponse:
        """Pin or unpin a chat."""
        data = await self._request(
            "POST",
            f"/chat/{chat_jid}/pin",
            device_id=device_id,
            json={"pinned": pinned},
        )
        return PinChatResponse(**data)

    async def set_disappearing_timer(
        self,
        chat_jid: str,
        timer_seconds: int,
        *,
        device_id: Optional[str] = None,
    ) -> SetDisappearingTimerResponse:
        """Set disappearing messages timer (0=off, 86400=24h, 604800=7d, 7776000=90d)."""
        data = await self._request(
            "POST",
            f"/chat/{chat_jid}/disappearing",
            device_id=device_id,
            json={"timer_seconds": timer_seconds},
        )
        return SetDisappearingTimerResponse(**data)

    async def archive_chat(
        self,
        chat_jid: str,
        archived: bool,
        *,
        device_id: Optional[str] = None,
    ) -> ArchiveChatResponse:
        """Archive or unarchive a chat."""
        data = await self._request(
            "POST",
            f"/chat/{chat_jid}/archive",
            device_id=device_id,
            json={"archived": archived},
        )
        return ArchiveChatResponse(**data)

    # ══════════════════════════════════════════════════════════════════════
    #  GROUP
    # ══════════════════════════════════════════════════════════════════════

    async def group_info(
        self, group_id: str, *, device_id: Optional[str] = None
    ) -> GroupInfoResponse:
        """Get group information."""
        data = await self._request(
            "GET", "/group/info", device_id=device_id, params={"group_id": group_id}
        )
        return GroupInfoResponse(**data)

    async def create_group(
        self,
        title: str,
        participants: List[str],
        *,
        device_id: Optional[str] = None,
    ) -> CreateGroupResponse:
        """Create a group and add participants."""
        data = await self._request(
            "POST",
            "/group",
            device_id=device_id,
            json={"title": title, "participants": participants},
        )
        return CreateGroupResponse(**data)

    async def get_group_participants(
        self, group_id: str, *, device_id: Optional[str] = None
    ) -> GroupParticipantsResponse:
        """Get list of group participants."""
        data = await self._request(
            "GET",
            "/group/participants",
            device_id=device_id,
            params={"group_id": group_id},
        )
        return GroupParticipantsResponse(**data)

    async def add_participants_to_group(
        self,
        group_id: str,
        participants: List[str],
        *,
        device_id: Optional[str] = None,
    ) -> ManageParticipantResponse:
        """Add participants to a group."""
        data = await self._request(
            "POST",
            "/group/participants",
            device_id=device_id,
            json={"group_id": group_id, "participants": participants},
        )
        return ManageParticipantResponse(**data)

    async def remove_participants_from_group(
        self,
        group_id: str,
        participants: List[str],
        *,
        device_id: Optional[str] = None,
    ) -> ManageParticipantResponse:
        """Remove participants from a group."""
        data = await self._request(
            "POST",
            "/group/participants/remove",
            device_id=device_id,
            json={"group_id": group_id, "participants": participants},
        )
        return ManageParticipantResponse(**data)

    async def promote_participants_to_admin(
        self,
        group_id: str,
        participants: List[str],
        *,
        device_id: Optional[str] = None,
    ) -> ManageParticipantResponse:
        """Promote participants to admin."""
        data = await self._request(
            "POST",
            "/group/participants/promote",
            device_id=device_id,
            json={"group_id": group_id, "participants": participants},
        )
        return ManageParticipantResponse(**data)

    async def demote_participants_to_member(
        self,
        group_id: str,
        participants: List[str],
        *,
        device_id: Optional[str] = None,
    ) -> ManageParticipantResponse:
        """Demote participants to member."""
        data = await self._request(
            "POST",
            "/group/participants/demote",
            device_id=device_id,
            json={"group_id": group_id, "participants": participants},
        )
        return ManageParticipantResponse(**data)

    async def export_group_participants(
        self, group_id: str, *, device_id: Optional[str] = None
    ) -> str:
        """Export group participants as CSV string."""
        data = await self._request(
            "GET",
            "/group/participants/export",
            device_id=device_id,
            params={"group_id": group_id},
        )
        return data.get("results", "")

    async def join_group_with_link(
        self, link: str, *, device_id: Optional[str] = None
    ) -> GenericResponse:
        """Join a group via invitation link."""
        data = await self._request(
            "POST",
            "/group/join-with-link",
            device_id=device_id,
            json={"link": link},
        )
        return GenericResponse(**data)

    async def get_group_info_from_link(
        self, link: str, *, device_id: Optional[str] = None
    ) -> GroupInfoFromLinkResponse:
        """Get group info from an invitation link without joining."""
        data = await self._request(
            "GET",
            "/group/info-from-link",
            device_id=device_id,
            params={"link": link},
        )
        return GroupInfoFromLinkResponse(**data)

    async def get_group_participant_requests(
        self, group_id: str, *, device_id: Optional[str] = None
    ) -> GroupParticipantRequestListResponse:
        """Get pending participant join requests."""
        data = await self._request(
            "GET",
            "/group/participant-requests",
            device_id=device_id,
            params={"group_id": group_id},
        )
        return GroupParticipantRequestListResponse(**data)

    async def approve_group_participant_request(
        self,
        group_id: str,
        participants: List[str],
        *,
        device_id: Optional[str] = None,
    ) -> GenericResponse:
        """Approve pending participant join requests."""
        data = await self._request(
            "POST",
            "/group/participant-requests/approve",
            device_id=device_id,
            json={"group_id": group_id, "participants": participants},
        )
        return GenericResponse(**data)

    async def reject_group_participant_request(
        self,
        group_id: str,
        participants: List[str],
        *,
        device_id: Optional[str] = None,
    ) -> GenericResponse:
        """Reject pending participant join requests."""
        data = await self._request(
            "POST",
            "/group/participant-requests/reject",
            device_id=device_id,
            json={"group_id": group_id, "participants": participants},
        )
        return GenericResponse(**data)

    async def leave_group(
        self, group_id: str, *, device_id: Optional[str] = None
    ) -> GenericResponse:
        """Leave a group."""
        data = await self._request(
            "POST", "/group/leave", device_id=device_id, json={"group_id": group_id}
        )
        return GenericResponse(**data)

    async def set_group_photo(
        self,
        group_id: str,
        *,
        photo: Optional[Union[BinaryIO, bytes, str, Path]] = None,
        filename: str = "photo.jpg",
        device_id: Optional[str] = None,
    ) -> SetGroupPhotoResponse:
        """Set or remove group photo."""
        fd = self._build_form(
            {"group_id": group_id},
            file_field="photo" if photo else None,
            file=photo,
            filename=filename,
            content_type="image/jpeg",
        )
        data = await self._request("POST", "/group/photo", device_id=device_id, data=fd)
        return SetGroupPhotoResponse(**data)

    async def set_group_name(
        self,
        group_id: str,
        name: str,
        *,
        device_id: Optional[str] = None,
    ) -> GenericResponse:
        """Set group name (max 25 chars)."""
        data = await self._request(
            "POST",
            "/group/name",
            device_id=device_id,
            json={"group_id": group_id, "name": name},
        )
        return GenericResponse(**data)

    async def set_group_locked(
        self,
        group_id: str,
        locked: bool,
        *,
        device_id: Optional[str] = None,
    ) -> GenericResponse:
        """Lock/unlock group so only admins can modify info."""
        data = await self._request(
            "POST",
            "/group/locked",
            device_id=device_id,
            json={"group_id": group_id, "locked": locked},
        )
        return GenericResponse(**data)

    async def set_group_announce(
        self,
        group_id: str,
        announce: bool,
        *,
        device_id: Optional[str] = None,
    ) -> GenericResponse:
        """Enable/disable announce mode (only admins can send)."""
        data = await self._request(
            "POST",
            "/group/announce",
            device_id=device_id,
            json={"group_id": group_id, "announce": announce},
        )
        return GenericResponse(**data)

    async def set_group_topic(
        self,
        group_id: str,
        topic: str = "",
        *,
        device_id: Optional[str] = None,
    ) -> GenericResponse:
        """Set or clear the group topic/description."""
        data = await self._request(
            "POST",
            "/group/topic",
            device_id=device_id,
            json={"group_id": group_id, "topic": topic},
        )
        return GenericResponse(**data)

    async def group_invite_link(
        self,
        group_id: str,
        *,
        reset: bool = False,
        device_id: Optional[str] = None,
    ) -> GetGroupInviteLinkResponse:
        """Get (or reset) the group invite link."""
        data = await self._request(
            "GET",
            "/group/invite-link",
            device_id=device_id,
            params={"group_id": group_id, "reset": reset},
        )
        return GetGroupInviteLinkResponse(**data)

    # ══════════════════════════════════════════════════════════════════════
    #  NEWSLETTER
    # ══════════════════════════════════════════════════════════════════════

    async def unfollow_newsletter(
        self, newsletter_id: str, *, device_id: Optional[str] = None
    ) -> GenericResponse:
        """Unfollow a newsletter."""
        data = await self._request(
            "POST",
            "/newsletter/unfollow",
            device_id=device_id,
            json={"newsletter_id": newsletter_id},
        )
        return GenericResponse(**data)

    # ══════════════════════════════════════════════════════════════════════
    #  CHATWOOT
    # ══════════════════════════════════════════════════════════════════════

    async def chatwoot_sync(
        self,
        *,
        device_id_body: Optional[str] = None,
        days_limit: Optional[int] = None,
        include_media: Optional[bool] = None,
        include_groups: Optional[bool] = None,
    ) -> ChatwootSyncResponse:
        """Initiate Chatwoot message history sync."""
        body: Dict[str, Any] = {}
        if device_id_body is not None:
            body["device_id"] = device_id_body
        if days_limit is not None:
            body["days_limit"] = days_limit
        if include_media is not None:
            body["include_media"] = include_media
        if include_groups is not None:
            body["include_groups"] = include_groups
        data = await self._request("POST", "/chatwoot/sync", json=body)
        return ChatwootSyncResponse(**data)

    async def chatwoot_sync_status(
        self, *, device_id_query: Optional[str] = None
    ) -> ChatwootSyncStatusResponse:
        """Get Chatwoot sync progress."""
        data = await self._request(
            "GET", "/chatwoot/sync/status", params={"device_id": device_id_query}
        )
        return ChatwootSyncStatusResponse(**data)

    async def chatwoot_webhook(self, payload: Dict[str, Any]) -> None:
        """Forward a Chatwoot webhook payload."""
        await self._request("POST", "/chatwoot/webhook", json=payload)
