"""Pydantic models for the Wago WhatsApp API client."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Generic ──────────────────────────────────────────────────────────────────

class GenericResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    results: Any = None
    status: Optional[int] = None


# ── App / Login ──────────────────────────────────────────────────────────────

class QRResult(BaseModel):
    qr_duration: Optional[int] = None
    qr_link: Optional[str] = None


class LoginResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[QRResult] = None


class PairCodeResult(BaseModel):
    pair_code: Optional[str] = None


class LoginWithCodeResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[PairCodeResult] = None


class DeviceEntry(BaseModel):
    name: Optional[str] = None
    device: Optional[str] = None


class DeviceResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[List[DeviceEntry]] = None


class AppStatusResult(BaseModel):
    is_connected: Optional[bool] = None
    is_logged_in: Optional[bool] = None
    device_id: Optional[str] = None


class AppStatusResponse(BaseModel):
    status: Optional[int] = None
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[AppStatusResult] = None


# ── Device Management ────────────────────────────────────────────────────────

class DeviceInfo(BaseModel):
    id: Optional[str] = None
    phone_number: Optional[str] = None
    display_name: Optional[str] = None
    state: Optional[str] = None
    jid: Optional[str] = None
    created_at: Optional[str] = None


class DeviceListResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    status: Optional[int] = None
    results: Optional[List[DeviceInfo]] = None


class DeviceAddResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    status: Optional[int] = None
    results: Optional[DeviceInfo] = None


class DeviceInfoResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    status: Optional[int] = None
    results: Optional[DeviceInfo] = None


class DeviceStatusResult(BaseModel):
    device_id: Optional[str] = None
    is_connected: Optional[bool] = None
    is_logged_in: Optional[bool] = None


class DeviceStatusResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    status: Optional[int] = None
    results: Optional[DeviceStatusResult] = None


# ── User ─────────────────────────────────────────────────────────────────────

class UserDeviceInfo(BaseModel):
    User: Optional[str] = None
    Agent: Optional[int] = None
    Device: Optional[str] = None
    Server: Optional[str] = None
    AD: Optional[bool] = None


class UserInfoResult(BaseModel):
    verified_name: Optional[str] = None
    status: Optional[str] = None
    picture_id: Optional[str] = None
    devices: Optional[List[UserDeviceInfo]] = None


class UserInfoResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[UserInfoResult] = None


class UserAvatarResult(BaseModel):
    url: Optional[str] = None
    id: Optional[str] = None
    type: Optional[str] = None


class UserAvatarResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[UserAvatarResult] = None


class UserPrivacyResult(BaseModel):
    group_add: Optional[str] = None
    last_seen: Optional[str] = None
    status: Optional[str] = None
    profile: Optional[str] = None
    read_receipts: Optional[str] = None


class UserPrivacyResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[UserPrivacyResult] = None


class GroupParticipant(BaseModel):
    JID: Optional[str] = None
    IsAdmin: Optional[bool] = None
    IsSuperAdmin: Optional[bool] = None
    Error: Optional[int] = None


class GroupData(BaseModel):
    JID: Optional[str] = None
    OwnerJID: Optional[str] = None
    Name: Optional[str] = None
    NameSetAt: Optional[str] = None
    NameSetBy: Optional[str] = None
    GroupCreated: Optional[str] = None
    ParticipantVersionID: Optional[str] = None
    Participants: Optional[List[GroupParticipant]] = None


class UserGroupResult(BaseModel):
    data: Optional[List[GroupData]] = None


class UserGroupResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[UserGroupResult] = None


class Contact(BaseModel):
    jid: Optional[str] = None
    name: Optional[str] = None


class MyListContactsResult(BaseModel):
    data: Optional[List[Contact]] = None


class MyListContactsResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[MyListContactsResult] = None


class UserCheckResult(BaseModel):
    is_on_whatsapp: Optional[bool] = None


class UserCheckResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[UserCheckResult] = None


class BusinessHour(BaseModel):
    day_of_week: Optional[str] = None
    mode: Optional[str] = None
    open_time: Optional[str] = None
    close_time: Optional[str] = None


class BusinessCategory(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None


class BusinessProfileResult(BaseModel):
    jid: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    categories: Optional[List[BusinessCategory]] = None
    profile_options: Optional[Dict[str, Any]] = None
    business_hours_timezone: Optional[str] = None
    business_hours: Optional[List[BusinessHour]] = None


class BusinessProfileResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[BusinessProfileResult] = None


# ── Newsletter ───────────────────────────────────────────────────────────────

class NewsletterNameDetail(BaseModel):
    text: Optional[str] = None
    id: Optional[str] = None
    update_time: Optional[str] = None


class NewsletterDescriptionDetail(BaseModel):
    text: Optional[str] = None
    id: Optional[str] = None
    update_time: Optional[str] = None


class NewsletterPicture(BaseModel):
    url: Optional[str] = None
    id: Optional[str] = None
    type: Optional[str] = None
    direct_path: Optional[str] = None


class NewsletterThreadMetadata(BaseModel):
    creation_time: Optional[str] = None
    invite: Optional[str] = None
    name: Optional[NewsletterNameDetail] = None
    description: Optional[NewsletterDescriptionDetail] = None
    subscribers_count: Optional[str] = None
    verification: Optional[str] = None
    picture: Optional[NewsletterPicture] = None
    preview: Optional[NewsletterPicture] = None
    settings: Optional[Dict[str, Any]] = None


class NewsletterState(BaseModel):
    type: Optional[str] = None


class NewsletterViewerMetadata(BaseModel):
    mute: Optional[str] = None
    role: Optional[str] = None


class Newsletter(BaseModel):
    id: Optional[str] = None
    state: Optional[NewsletterState] = None
    thread_metadata: Optional[NewsletterThreadMetadata] = None
    viewer_metadata: Optional[NewsletterViewerMetadata] = None


class NewsletterResult(BaseModel):
    data: Optional[List[Newsletter]] = None


class NewsletterResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[NewsletterResult] = None


# ── Send ─────────────────────────────────────────────────────────────────────

class SendResult(BaseModel):
    message_id: Optional[str] = None
    status: Optional[str] = None


class SendResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[SendResult] = None


# ── Message / Download ───────────────────────────────────────────────────────

class DownloadMediaResult(BaseModel):
    status: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    file_name: Optional[str] = None
    data: Optional[str] = None  # base64


class DownloadMediaResponse(BaseModel):
    status: Optional[int] = None
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[DownloadMediaResult] = None


# ── Chat ─────────────────────────────────────────────────────────────────────

class Chat(BaseModel):
    jid: Optional[str] = None
    name: Optional[str] = None
    last_message_time: Optional[str] = None
    ephemeral_expiration: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    archived: Optional[bool] = None


class Pagination(BaseModel):
    limit: Optional[int] = None
    offset: Optional[int] = None
    total: Optional[int] = None


class ChatListResult(BaseModel):
    data: Optional[List[Chat]] = None
    pagination: Optional[Pagination] = None


class ChatListResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[ChatListResult] = None


class ChatMessage(BaseModel):
    id: Optional[str] = None
    chat_jid: Optional[str] = None
    sender_jid: Optional[str] = None
    content: Optional[str] = None
    timestamp: Optional[str] = None
    is_from_me: Optional[bool] = None
    media_type: Optional[str] = None
    filename: Optional[str] = None
    url: Optional[str] = None
    file_length: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ChatMessagesResult(BaseModel):
    data: Optional[List[ChatMessage]] = None
    pagination: Optional[Pagination] = None
    chat_info: Optional[Chat] = None


class ChatMessagesResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[ChatMessagesResult] = None


class LabelChatResult(BaseModel):
    status: Optional[str] = None
    message: Optional[str] = None
    chat_jid: Optional[str] = None
    label_id: Optional[str] = None
    labeled: Optional[bool] = None


class LabelChatResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[LabelChatResult] = None


class PinChatResult(BaseModel):
    status: Optional[str] = None
    message: Optional[str] = None
    chat_jid: Optional[str] = None
    pinned: Optional[bool] = None


class PinChatResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[PinChatResult] = None


class DisappearingTimerResult(BaseModel):
    status: Optional[str] = None
    message: Optional[str] = None
    chat_jid: Optional[str] = None
    timer_seconds: Optional[int] = None


class SetDisappearingTimerResponse(BaseModel):
    status: Optional[int] = None
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[DisappearingTimerResult] = None


class ArchiveChatResult(BaseModel):
    status: Optional[str] = None
    message: Optional[str] = None
    chat_jid: Optional[str] = None
    archived: Optional[bool] = None


class ArchiveChatResponse(BaseModel):
    status: Optional[int] = None
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[ArchiveChatResult] = None


# ── Group ────────────────────────────────────────────────────────────────────

class CreateGroupResult(BaseModel):
    group_id: Optional[str] = None


class CreateGroupResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[CreateGroupResult] = None


class GroupInfoResponse(BaseModel):
    status: Optional[int] = None
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[Dict[str, Any]] = None


class GroupParticipantItem(BaseModel):
    jid: Optional[str] = None
    phone_number: Optional[str] = None
    lid: Optional[str] = None
    display_name: Optional[str] = None
    is_admin: Optional[bool] = None
    is_super_admin: Optional[bool] = None


class GroupParticipantsResult(BaseModel):
    group_id: Optional[str] = None
    name: Optional[str] = None
    participants: Optional[List[GroupParticipantItem]] = None


class GroupParticipantsResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[GroupParticipantsResult] = None


class ManageParticipantResult(BaseModel):
    participant: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None


class ManageParticipantResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[List[ManageParticipantResult]] = None


class GroupInfoFromLinkResult(BaseModel):
    group_id: Optional[str] = None
    name: Optional[str] = None
    topic: Optional[str] = None
    created_at: Optional[str] = None
    participant_count: Optional[int] = None
    is_locked: Optional[bool] = None
    is_announce: Optional[bool] = None
    is_ephemeral: Optional[bool] = None
    description: Optional[str] = None


class GroupInfoFromLinkResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[GroupInfoFromLinkResult] = None


class ParticipantRequest(BaseModel):
    jid: Optional[str] = None
    phone_number: Optional[str] = None
    display_name: Optional[str] = None
    requested_at: Optional[str] = None


class GroupParticipantRequestListResult(BaseModel):
    data: Optional[List[ParticipantRequest]] = None


class GroupParticipantRequestListResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[GroupParticipantRequestListResult] = None


class SetGroupPhotoResult(BaseModel):
    picture_id: Optional[str] = None
    message: Optional[str] = None


class SetGroupPhotoResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[SetGroupPhotoResult] = None


class GroupInviteLinkResult(BaseModel):
    invite_link: Optional[str] = None
    group_id: Optional[str] = None


class GetGroupInviteLinkResponse(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[GroupInviteLinkResult] = None


# ── Chatwoot ─────────────────────────────────────────────────────────────────

class ChatwootSyncResult(BaseModel):
    device_id: Optional[str] = None
    days_limit: Optional[int] = None
    include_media: Optional[bool] = None
    include_groups: Optional[bool] = None


class ChatwootSyncResponse(BaseModel):
    status: Optional[int] = None
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[ChatwootSyncResult] = None


class ChatwootSyncStatusResult(BaseModel):
    device_id: Optional[str] = None
    status: Optional[str] = None
    total_chats: Optional[int] = None
    synced_chats: Optional[int] = None
    total_messages: Optional[int] = None
    synced_messages: Optional[int] = None
    failed_messages: Optional[int] = None
    current_chat: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


class ChatwootSyncStatusResponse(BaseModel):
    status: Optional[int] = None
    code: Optional[str] = None
    message: Optional[str] = None
    results: Optional[ChatwootSyncStatusResult] = None
