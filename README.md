# py-wago

[![PyPI version](https://img.shields.io/pypi/v/py-wago)](https://pypi.org/project/py-wago/)
[![Python versions](https://img.shields.io/pypi/pyversions/py-wago)](https://pypi.org/project/py-wago/)
[![Publish pypi package](https://github.com/t0mer/py-wago/actions/workflows/python_publish.yml/badge.svg)](https://github.com/t0mer/py-wago/actions/workflows/python_publish.yml)

Async Python client library for the **Wago WhatsApp API** (MultiDevice v8).

`py-wago` wraps the REST API of a self-hosted WhatsApp gateway in a typed, `asyncio`-friendly
client built on [aiohttp](https://docs.aiohttp.org/) and [Pydantic v2](https://docs.pydantic.dev/).
It is meant for Python developers who run their own GOWA-compatible gateway (the author calls it
"Wago") and want to send messages, manage
groups, chats and devices, or sync with Chatwoot from Python code, without hand-writing HTTP calls.

The API this client targets is described in
[`swagger.yml`](https://github.com/t0mer/py-wago/blob/main/swagger.yml) ("WhatsApp API
MultiDevice", spec version 8.3.0). That bundled spec matches the OpenAPI file shipped with
[go-whatsapp-web-multidevice (GOWA)](https://github.com/aldinokemal/go-whatsapp-web-multidevice)
releases v8.3.3 to v8.3.5. GOWA is a Go WhatsApp REST gateway built on
[whatsmeow](https://github.com/tulir/whatsmeow).
<!-- TODO: verify the origin of the name "Wago" -->

> **Unofficial project.** `py-wago` is not affiliated with, endorsed by, or connected to
> WhatsApp, Meta Platforms, Inc., or the authors of the upstream gateway. "WhatsApp" is a
> trademark of its respective owner.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Authentication](#authentication)
- [Multi-Device Support](#multi-device-support)
- [Custom Headers](#custom-headers)
- [Client Options](#client-options)
- [API Coverage](#api-coverage)
- [Responses and Models](#responses-and-models)
- [Error Handling](#error-handling)
- [Sending Media](#sending-media)
- [Known Issues](#known-issues)
- [Security Notes](#security-notes)
- [Responsible Use](#responsible-use)
- [Development](#development)
- [Contributing](#contributing)
- [Issues](#issues)
- [License](#license)

## Features

- Fully async client (`async with WagoClient(...)`) on top of `aiohttp`.
- Covers all 75 REST operations in the bundled `swagger.yml`: app login/status, multi-device
  management, user info, sending (text, image, audio, file, sticker, video, contact, link,
  location, poll, presence), message actions, chats, groups, newsletters and Chatwoot.
- HTTP Basic Auth on every request.
- Multi-device: a default `X-Device-Id` on the client, overridable per call.
- Custom headers on every request (for example Cloudflare Access service tokens).
- Media upload from a file path, `bytes`, a binary file object, or a URL the gateway downloads (image, audio, sticker and video only).
- Pydantic v2 response models with optional fields.
- One exception per HTTP error class, all derived from `WagoError`.

Not covered: the gateway's WebSocket endpoint (`/ws?device_id=<id>`) and receiving the
webhooks the gateway sends to your application. The client only makes outgoing REST calls
(including `chatwoot_webhook`, which forwards a payload to the gateway).

## Requirements

- Python 3.9 or newer.
- `aiohttp>=3.9` and `pydantic>=2.0` (installed automatically).
- A running, reachable gateway that exposes the API in `swagger.yml`, with Basic Auth
  credentials.

## Installation

From [PyPI](https://pypi.org/project/py-wago/):

```bash
pip install py-wago
```

From source:

```bash
git clone https://github.com/t0mer/py-wago.git
cd py-wago
pip install .
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

Phone numbers and chats are passed as WhatsApp JIDs, for example
`628123456789@s.whatsapp.net` for a person or `<id>@g.us` for a group, as in the upstream spec.
Login calls (`app_login_with_code`, `login_device_with_code`) take a plain number such as
`628123456789`.

The client opens its `aiohttp` session on the first request. Use `async with`, or call
`await client.close()` yourself when you're done.

The shorter snippets in the rest of this README assume they run inside an `async def main()`
with an open `client`, as in the example above, started once with `asyncio.run(main())`.

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

Both arguments are required. The client does not support API keys or tokens. If your gateway
sits behind a proxy that needs extra credentials, use [custom headers](#custom-headers).

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

The device ID is sent in the `X-Device-Id` header. Most methods accept a keyword-only
`device_id=` override. The exceptions:

- The device-management methods (`list_devices`, `get_device`, `login_device`, ...) take the
  device ID as a path argument and have no per-call header override. They still send the
  client's default `X-Device-Id`, if one is set.
- `app_devices()` and the Chatwoot methods have no `device_id=` override either. For Chatwoot,
  the device is passed in the body or query instead (see [API Coverage](#api-coverage)).

Managing device slots:

```python
await client.add_device("sales-phone")               # create a slot
login = await client.login_device("sales-phone")     # QR code login
print(login.results.qr_link)

code = await client.login_device_with_code("sales-phone", phone="628123456789")
print(code.results.pair_code)                         # pairing-code login

status = await client.get_device_status("sales-phone")
```

## Custom Headers

You can pass extra HTTP headers that will be included in **every request**.
This is useful when the API is behind a reverse proxy such as Cloudflare Access
or any other service that requires additional authentication headers:

```python
client = WagoClient(
    base_url="https://wago.example.com",
    username="user",
    password="pass",
    custom_headers={
        "CF-Access-Client-Id": "<client-id>",
        "CF-Access-Client-Secret": "<client-secret>",
    },
)
```

The headers are merged with the per-request headers (e.g. `X-Device-Id`), so
you can combine `custom_headers` with `device_id` without conflicts. If `custom_headers`
also contains `X-Device-Id`, the client's device ID wins whenever one is set.

## Client Options

`WagoClient(base_url, username, password, *, device_id=None, timeout=30.0, session=None, custom_headers=None)`

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `base_url` | `str` | required | Gateway base URL, e.g. `https://wago.example.com`. A trailing `/` is stripped. Paths such as `/send/message` are appended directly. |
| `username` | `str` | required | Basic Auth username. |
| `password` | `str` | required | Basic Auth password. |
| `device_id` | `str \| None` | `None` | Default `X-Device-Id` header. |
| `timeout` | `float` | `30.0` | Total request timeout in seconds. |
| `session` | `aiohttp.ClientSession \| None` | `None` | Bring your own session. You are then responsible for closing it. |
| `custom_headers` | `dict[str, str] \| None` | `None` | Extra headers sent on every request. |

Using your own session: the client applies Basic Auth and `timeout` **only to the session it
creates itself**. If you pass `session=`, configure auth (and the timeout) on that session:

```python
import asyncio
import aiohttp
from py_wago import WagoClient

async def main():
    async with aiohttp.ClientSession(
        auth=aiohttp.BasicAuth("user", "pass"),
        timeout=aiohttp.ClientTimeout(total=30),
    ) as session:
        client = WagoClient("https://wago.example.com", "user", "pass", session=session)
        await client.app_status()

asyncio.run(main())
```

The library doesn't read any environment variables or config files. Everything is passed to
the constructor.

## API Coverage

Every method is a coroutine. Arguments after `*` in the signatures below are keyword-only.
Unless noted otherwise, each method also takes a keyword-only `device_id=` override.

### App

| Method | Endpoint | Description |
|--------|----------|-------------|
| `app_login()` | `GET /app/login` | Login via QR code |
| `app_login_with_code(phone)` | `GET /app/login-with-code` | Login via pairing code |
| `app_logout()` | `GET /app/logout` | Logout and remove database |
| `app_reconnect()` | `GET /app/reconnect` | Reconnect to WhatsApp |
| `app_devices()` | `GET /app/devices` | List connected devices (no `device_id=` override) |
| `app_status()` | `GET /app/status` | Get connection status |

### Device Management

These methods take the device ID as a path argument and have no `device_id=` override.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `list_devices()` | `GET /devices` | List all registered devices |
| `add_device(device_id=None)` | `POST /devices` | Add a new device slot |
| `get_device(device_id)` | `GET /devices/{device_id}` | Get device info |
| `remove_device(device_id)` | `DELETE /devices/{device_id}` | Remove a device |
| `login_device(device_id)` | `GET /devices/{device_id}/login` | QR login for device |
| `login_device_with_code(device_id, phone)` | `POST /devices/{device_id}/login/code` | Pairing code login |
| `logout_device(device_id)` | `POST /devices/{device_id}/logout` | Logout device |
| `reconnect_device(device_id)` | `POST /devices/{device_id}/reconnect` | Reconnect device |
| `get_device_status(device_id)` | `GET /devices/{device_id}/status` | Get device status |

### User

| Method | Endpoint | Description |
|--------|----------|-------------|
| `user_info(phone)` | `GET /user/info` | Get user info |
| `user_avatar(phone, *, is_preview=None, is_community=None)` | `GET /user/avatar` | Get user avatar (see [Known Issues](#known-issues)) |
| `user_change_avatar(avatar, *, filename="avatar.jpg")` | `POST /user/avatar` | Change avatar |
| `user_change_push_name(push_name)` | `POST /user/pushname` | Change display name |
| `user_my_privacy()` | `GET /user/my/privacy` | Get privacy settings |
| `user_my_groups()` | `GET /user/my/groups` | List joined groups |
| `user_my_newsletters()` | `GET /user/my/newsletters` | List newsletters |
| `user_my_contacts()` | `GET /user/my/contacts` | List contacts |
| `user_check(phone)` | `GET /user/check` | Check if on WhatsApp |
| `user_business_profile(phone)` | `GET /user/business-profile` | Get business profile |

### Send

All send methods except `send_presence` and `send_chat_presence` accept an optional
`duration=` (disappearing-message timer, in seconds). All except `send_poll`, `send_presence`
and `send_chat_presence` also accept `is_forwarded=`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `send_message(phone, message, *, reply_message_id=None, mentions=None)` | `POST /send/message` | Send text message |
| `send_image(phone, *, image=None, image_url=None, caption=None, view_once=None, compress=None, filename="image.jpg")` | `POST /send/image` | Send image |
| `send_audio(phone, *, audio=None, audio_url=None, filename="audio.mp3")` | `POST /send/audio` | Send audio |
| `send_file(phone, *, file=None, caption=None, filename="document")` | `POST /send/file` | Send document |
| `send_sticker(phone, *, sticker=None, sticker_url=None, filename="sticker.webp")` | `POST /send/sticker` | Send sticker |
| `send_video(phone, *, video=None, video_url=None, caption=None, view_once=None, compress=None, filename="video.mp4")` | `POST /send/video` | Send video |
| `send_contact(phone, contact_name, contact_phone)` | `POST /send/contact` | Send contact card |
| `send_link(phone, link, *, caption=None)` | `POST /send/link` | Send link |
| `send_location(phone, latitude, longitude)` | `POST /send/location` | Send location (coordinates as strings, e.g. `"-7.797068"`) |
| `send_poll(phone, question, options, max_answer)` | `POST /send/poll` | Send poll |
| `send_presence(presence_type)` | `POST /send/presence` | Set presence status (`"available"` / `"unavailable"`) |
| `send_chat_presence(phone, action)` | `POST /send/chat-presence` | Typing indicator (`"start"` / `"stop"`) |

### Message

| Method | Endpoint | Description |
|--------|----------|-------------|
| `revoke_message(message_id, phone)` | `POST /message/{message_id}/revoke` | Revoke/unsend |
| `delete_message(message_id, phone)` | `POST /message/{message_id}/delete` | Delete locally |
| `react_message(message_id, phone, emoji)` | `POST /message/{message_id}/reaction` | React with emoji |
| `update_message(message_id, phone, message)` | `POST /message/{message_id}/update` | Edit message |
| `read_message(message_id, phone)` | `POST /message/{message_id}/read` | Mark as read |
| `star_message(message_id, phone)` | `POST /message/{message_id}/star` | Star message |
| `unstar_message(message_id, phone)` | `POST /message/{message_id}/unstar` | Unstar message |
| `download_message_media(message_id, phone)` | `GET /message/{message_id}/download` | Download media (base64 in `results.data`) |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| `list_chats(*, limit=None, offset=None, search=None, has_media=None, archived=None)` | `GET /chats` | List chats (see [Known Issues](#known-issues)) |
| `get_chat_messages(chat_jid, *, limit=None, offset=None, start_time=None, end_time=None, media_only=None, is_from_me=None, search=None)` | `GET /chat/{chat_jid}/messages` | Get chat messages (see [Known Issues](#known-issues)) |
| `label_chat(chat_jid, label_id, label_name, labeled)` | `POST /chat/{chat_jid}/label` | Label/unlabel chat |
| `pin_chat(chat_jid, pinned)` | `POST /chat/{chat_jid}/pin` | Pin/unpin chat |
| `set_disappearing_timer(chat_jid, timer_seconds)` | `POST /chat/{chat_jid}/disappearing` | Set disappearing timer (`0`, `86400`, `604800`, `7776000`) |
| `archive_chat(chat_jid, archived)` | `POST /chat/{chat_jid}/archive` | Archive/unarchive chat |

### Group

| Method | Endpoint | Description |
|--------|----------|-------------|
| `group_info(group_id)` | `GET /group/info` | Get group info |
| `create_group(title, participants)` | `POST /group` | Create group |
| `get_group_participants(group_id)` | `GET /group/participants` | List participants |
| `add_participants_to_group(group_id, participants)` | `POST /group/participants` | Add participants |
| `remove_participants_from_group(group_id, participants)` | `POST /group/participants/remove` | Remove participants |
| `promote_participants_to_admin(group_id, participants)` | `POST /group/participants/promote` | Promote to admin |
| `demote_participants_to_member(group_id, participants)` | `POST /group/participants/demote` | Demote to member |
| `export_group_participants(group_id)` | `GET /group/participants/export` | Export as CSV (returns a `str`) |
| `join_group_with_link(link)` | `POST /group/join-with-link` | Join via link |
| `get_group_info_from_link(link)` | `GET /group/info-from-link` | Info from link |
| `get_group_participant_requests(group_id)` | `GET /group/participant-requests` | Pending requests |
| `approve_group_participant_request(group_id, participants)` | `POST /group/participant-requests/approve` | Approve join |
| `reject_group_participant_request(group_id, participants)` | `POST /group/participant-requests/reject` | Reject join |
| `leave_group(group_id)` | `POST /group/leave` | Leave group |
| `set_group_photo(group_id, *, photo=None, filename="photo.jpg")` | `POST /group/photo` | Set photo, or remove it when `photo` is omitted |
| `set_group_name(group_id, name)` | `POST /group/name` | Set name |
| `set_group_locked(group_id, locked)` | `POST /group/locked` | Lock/unlock |
| `set_group_announce(group_id, announce)` | `POST /group/announce` | Announce mode |
| `set_group_topic(group_id, topic="")` | `POST /group/topic` | Set or clear topic |
| `group_invite_link(group_id, *, reset=False)` | `GET /group/invite-link` | Get invite link (see [Known Issues](#known-issues)) |

### Newsletter & Chatwoot

The Chatwoot methods take no `device_id=` header override. Pass the device in the request
instead, with `device_id_body=` or `device_id_query=`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `unfollow_newsletter(newsletter_id)` | `POST /newsletter/unfollow` | Unfollow newsletter |
| `chatwoot_sync(*, device_id_body=None, days_limit=None, include_media=None, include_groups=None)` | `POST /chatwoot/sync` | Sync to Chatwoot |
| `chatwoot_sync_status(*, device_id_query=None)` | `GET /chatwoot/sync/status` | Sync progress |
| `chatwoot_webhook(payload)` | `POST /chatwoot/webhook` | Forward webhook (returns `None`) |

## Responses and Models

Methods return Pydantic v2 models that mirror the gateway's JSON envelope:

```python
resp = await client.send_message(phone="628123456789@s.whatsapp.net", message="hi")
resp.code                 # e.g. "SUCCESS"
resp.message              # human-readable message from the server
resp.results.message_id   # typed payload
```

All model fields are optional, so check for `None` before you use a value. The models live in
`py_wago.models` (for example `SendResponse`, `AppStatusResponse`, `ChatListResponse`,
`GroupInfoResponse`). They aren't re-exported from the top-level `py_wago` package.

## Error Handling

```python
from py_wago import WagoClient, WagoBadRequestError, WagoUnauthorizedError

async with WagoClient("https://wago.example.com", "user", "pass") as client:
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

Every exception has `message`, `code` (the API error code), `status` (HTTP status) and
`details` (the response's `results`, if any). For `WagoConnectionError`, `code`, `status` and
`details` are always `None`; any HTTP status appears only in the message text.

When the error body is JSON, other error statuses (for example 403 or 502) raise the base
`WagoError`. A non-JSON error page, such as a reverse proxy's HTML 502, raises
`WagoConnectionError` instead.

`WagoConnectionError` wraps any `aiohttp.ClientError`. That includes a response whose
`Content-Type` isn't JSON. Other bad bodies are not wrapped:

- Malformed JSON served as `application/json` raises `json.JSONDecodeError`.
- An empty JSON body leads to a `TypeError`.
- A request that exceeds `timeout` raises `asyncio.TimeoutError`.

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

Media arguments accept a path (`str` or `pathlib.Path`), `bytes`, or a binary file object.
The client uploads them as `multipart/form-data` with a fixed content type per method:

| Method | Content type |
|--------|--------------|
| `send_image`, `set_group_photo` | `image/jpeg` |
| `send_audio` | `audio/mpeg` |
| `send_sticker` | `image/webp` |
| `send_video` | `video/mp4` |
| `send_file`, `user_change_avatar` | `application/octet-stream` |

The file name sent to the server comes from `filename=`, not from the path. Set it when the
extension matters, as with `send_file`. `send_file` has no URL variant.

Downloading media returns base64:

```python
import base64
import os

media = await client.download_message_media("MESSAGE_ID", phone="628123456789@s.whatsapp.net")
if media.results is not None and media.results.data is not None:
    name = os.path.basename(media.results.file_name or "") or "download.bin"
    with open(name, "wb") as out:
        out.write(base64.b64decode(media.results.data))
```

## Known Issues

These describe the current code (0.2.0):

- **Boolean query parameters raise `TypeError`.** `aiohttp` does not accept `True`/`False` as
  query values. As a result:
  - `group_invite_link()` always fails, because `reset` defaults to `False`.
  - `list_chats(has_media=..., archived=...)`, `get_chat_messages(media_only=..., is_from_me=...)`
    and `user_avatar(is_preview=..., is_community=...)` fail when you set those flags.

  Leave these flags unset until this is fixed.
- **`session=` skips auth.** A session you pass in does not get the client's Basic Auth or
  timeout (see [Client Options](#client-options)).
- **File handles opened from paths aren't closed** by the client after upload.
- `py_wago.__version__` reports `0.1.0`, while the package metadata is `0.2.0`.
- The client was written against spec version 8.3.0. Upstream GOWA has since moved to v9.x.
  In v9.x, `POST /chat/{chat_jid}/label` (`label_chat`) was removed, and v9 adds operations
  that this client doesn't wrap.
  <!-- TODO: verify full request/response schema compatibility with GOWA v9.x -->

## Security Notes

- Basic Auth credentials go with every request. Use an `https://` `base_url`, or keep the
  gateway on a private network.
- Keep credentials and proxy tokens (such as Cloudflare Access secrets) out of source code.
  Load them from environment variables or a secrets manager in your own application.
- The gateway holds a logged-in WhatsApp session. Anyone who can reach its API with valid
  credentials can send messages as that account, so don't expose it to the public internet
  without extra access control.
- Downloaded media and exported participant lists can contain personal data. Handle them
  accordingly.

## Responsible Use

WhatsApp's [Terms of Service](https://www.whatsapp.com/legal/terms-of-service) do not allow
unofficial or automated clients. Gateways built on WhatsApp Web, like the one this library
talks to, can get the linked phone number **restricted or banned**, especially for bulk,
unsolicited, or high-volume messaging. Use this library only with accounts you are prepared
to lose, only message people who expect to hear from you, and follow local anti-spam and
privacy laws. For business messaging at scale, use the official WhatsApp Business Platform.

## Development

```bash
git clone https://github.com/t0mer/py-wago.git
cd py-wago
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"      # pytest, pytest-asyncio, aioresponses, ruff, mypy
ruff check py_wago
mypy py_wago
```

The repository doesn't contain a test suite yet.

Project layout:

```
py_wago/
├── __init__.py     # public exports (WagoClient + exceptions)
├── client.py       # WagoClient, one coroutine per endpoint
├── models.py       # Pydantic response models
└── exceptions.py   # WagoError hierarchy
swagger.yml         # upstream OpenAPI spec the client is written against
```

Releases are published to PyPI by the
[`python_publish.yml`](https://github.com/t0mer/py-wago/blob/main/.github/workflows/python_publish.yml)
workflow. It runs on a published GitHub release or on manual dispatch.

## Contributing

Pull requests are welcome. Keep changes aligned with `swagger.yml`, and run `ruff` and `mypy`
before opening a PR.

## Issues

Found a bug or have a feature request? Please [open an issue](https://github.com/t0mer/py-wago/issues).

## License

The package metadata (`pyproject.toml`, `setup.py`) declares the **MIT** license, but the
repository doesn't include a `LICENSE` file yet.
<!-- TODO: add a LICENSE file (MIT) to the repository -->
