# py-wago

Async Python client library for the **Wago WhatsApp API** (MultiDevice v8).

## Installation

```bash
pip install .            # from source
# or
pip install py-wago      # once published
```

## Quick Start

```python
import asyncio
from py_wago import WagoClient

async def main():
    async with WagoClient(
        base_url="https://wago.example.com",
        username="admin",
        password="secret",
        device_id="my-device",           # optional default device
    ) as client:
        # Check connection status
        status = await client.app_status()
        print(status.results.is_connected)

        # Send a text message
        resp = await client.send_message(
            phone="628123456789@s.whatsapp.net",
            message="Hello from py-wago!",
        )
        print(resp.results.message_id)

asyncio.run(main())
```

## Authentication

Every request uses **HTTP Basic Auth**. Pass `username` and `password` when
creating the client:

```python
client = WagoClient(
    base_url="https://wago.example.com",
    username="user",
    password="pass",
)
```

## Multi-Device Support

Set a default `device_id` on the client, or override per-call:

```python
client = WagoClient(
    base_url="https://wago.example.com",
    username="user",
    password="pass",
    device_id="default-device",
)

# Override per-call
await client.send_message(
    phone="628123456789@s.whatsapp.net",
    message="Hello",
    device_id="other-device",
)
```

## API Coverage

### App

| Method | Description |
|--------|-------------|
| `app_login()` | Login via QR code |
| `app_login_with_code(phone)` | Login via pairing code |
| `app_logout()` | Logout and remove database |
| `app_reconnect()` | Reconnect to WhatsApp |
| `app_devices()` | List connected devices |
| `app_status()` | Get connection status |

### Device Management

| Method | Description |
|--------|-------------|
| `list_devices()` | List all registered devices |
| `add_device(device_id?)` | Add a new device slot |
| `get_device(device_id)` | Get device info |
| `remove_device(device_id)` | Remove a device |
| `login_device(device_id)` | QR login for device |
| `login_device_with_code(device_id, phone)` | Pairing code login |
| `logout_device(device_id)` | Logout device |
| `reconnect_device(device_id)` | Reconnect device |
| `get_device_status(device_id)` | Get device status |

### User

| Method | Description |
|--------|-------------|
| `user_info(phone)` | Get user info |
| `user_avatar(phone)` | Get user avatar |
| `user_change_avatar(avatar)` | Change avatar |
| `user_change_push_name(name)` | Change display name |
| `user_my_privacy()` | Get privacy settings |
| `user_my_groups()` | List joined groups |
| `user_my_newsletters()` | List newsletters |
| `user_my_contacts()` | List contacts |
| `user_check(phone)` | Check if on WhatsApp |
| `user_business_profile(phone)` | Get business profile |

### Send

| Method | Description |
|--------|-------------|
| `send_message(phone, message)` | Send text message |
| `send_image(phone, image=, image_url=)` | Send image |
| `send_audio(phone, audio=, audio_url=)` | Send audio |
| `send_file(phone, file=)` | Send document |
| `send_sticker(phone, sticker=, sticker_url=)` | Send sticker |
| `send_video(phone, video=, video_url=)` | Send video |
| `send_contact(phone, name, contact_phone)` | Send contact card |
| `send_link(phone, link)` | Send link |
| `send_location(phone, lat, lon)` | Send location |
| `send_poll(phone, question, options, max)` | Send poll |
| `send_presence(type)` | Set presence status |
| `send_chat_presence(phone, action)` | Typing indicator |

### Message

| Method | Description |
|--------|-------------|
| `revoke_message(msg_id, phone)` | Revoke/unsend |
| `delete_message(msg_id, phone)` | Delete locally |
| `react_message(msg_id, phone, emoji)` | React with emoji |
| `update_message(msg_id, phone, message)` | Edit message |
| `read_message(msg_id, phone)` | Mark as read |
| `star_message(msg_id, phone)` | Star message |
| `unstar_message(msg_id, phone)` | Unstar message |
| `download_message_media(msg_id, phone)` | Download media |

### Chat

| Method | Description |
|--------|-------------|
| `list_chats(limit=, offset=, ...)` | List chats |
| `get_chat_messages(chat_jid, ...)` | Get chat messages |
| `label_chat(jid, label_id, name, labeled)` | Label/unlabel chat |
| `pin_chat(jid, pinned)` | Pin/unpin chat |
| `set_disappearing_timer(jid, seconds)` | Set disappearing timer |
| `archive_chat(jid, archived)` | Archive/unarchive chat |

### Group

| Method | Description |
|--------|-------------|
| `group_info(group_id)` | Get group info |
| `create_group(title, participants)` | Create group |
| `get_group_participants(group_id)` | List participants |
| `add_participants_to_group(id, list)` | Add participants |
| `remove_participants_from_group(id, list)` | Remove participants |
| `promote_participants_to_admin(id, list)` | Promote to admin |
| `demote_participants_to_member(id, list)` | Demote to member |
| `export_group_participants(group_id)` | Export as CSV |
| `join_group_with_link(link)` | Join via link |
| `get_group_info_from_link(link)` | Info from link |
| `get_group_participant_requests(id)` | Pending requests |
| `approve_group_participant_request(...)` | Approve join |
| `reject_group_participant_request(...)` | Reject join |
| `leave_group(group_id)` | Leave group |
| `set_group_photo(group_id, photo=)` | Set/remove photo |
| `set_group_name(group_id, name)` | Set name |
| `set_group_locked(group_id, locked)` | Lock/unlock |
| `set_group_announce(group_id, announce)` | Announce mode |
| `set_group_topic(group_id, topic)` | Set topic |
| `group_invite_link(group_id, reset=)` | Get invite link |

### Newsletter & Chatwoot

| Method | Description |
|--------|-------------|
| `unfollow_newsletter(newsletter_id)` | Unfollow newsletter |
| `chatwoot_sync(...)` | Sync to Chatwoot |
| `chatwoot_sync_status(...)` | Sync progress |
| `chatwoot_webhook(payload)` | Forward webhook |

## Error Handling

```python
from py_wago import WagoClient, WagoBadRequestError, WagoUnauthorizedError

async with WagoClient(...) as client:
    try:
        await client.send_message(phone="invalid", message="hi")
    except WagoBadRequestError as e:
        print(f"Bad request: {e.message}")
    except WagoUnauthorizedError:
        print("Check your credentials")
```

### Exception Hierarchy

```
WagoError
├── WagoBadRequestError      (400)
├── WagoUnauthorizedError    (401)
├── WagoNotFoundError        (404)
├── WagoConflictError        (409)
├── WagoInternalServerError  (500)
└── WagoConnectionError      (network issues)
```

## Sending Media

```python
# From file path
await client.send_image(
    phone="628123456789@s.whatsapp.net",
    image="/path/to/photo.jpg",
    caption="Check this out!",
)

# From URL
await client.send_image(
    phone="628123456789@s.whatsapp.net",
    image_url="https://example.com/photo.jpg",
    caption="From the web",
)

# From bytes / file object
with open("doc.pdf", "rb") as f:
    await client.send_file(
        phone="628123456789@s.whatsapp.net",
        file=f,
        caption="Important document",
        filename="report.pdf",
    )
```

## License

MIT
