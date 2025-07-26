from http import HTTPStatus

import httpx
import pytest
import respx
from httpx import Response

from shared.clients import telegram_client
from shared.core.settings import settings

TELEGRAM_API_URL = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"


@pytest.mark.asyncio
@respx.mock
async def test_send_message_success():
    chat_id = 123456
    text = "Hello, world!"
    url = f"{TELEGRAM_API_URL}/sendMessage"

    route = respx.post(url).mock(return_value=Response(HTTPStatus.OK, json={"ok": True, "result": {"message_id": 1}}))

    result = await telegram_client.send_message(chat_id, text)

    assert route.called
    assert result["ok"] is True
    assert result["result"]["message_id"] == 1


@pytest.mark.asyncio
@respx.mock
async def test_send_message_http_error():
    chat_id = 123456
    text = "fail"
    url = f"{TELEGRAM_API_URL}/sendMessage"

    route = respx.post(url).mock(
        return_value=Response(HTTPStatus.BAD_REQUEST, json={"ok": False, "description": "Bad Request"})
    )

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await telegram_client.send_message(chat_id, text)

    assert route.called
    assert exc_info.value.response.status_code == HTTPStatus.BAD_REQUEST
    assert exc_info.value.response.json() == {"ok": False, "description": "Bad Request"}


@pytest.mark.asyncio
@respx.mock
async def test_send_message_unexpected_error():
    chat_id = 123456
    text = "fail"
    url = f"{TELEGRAM_API_URL}/sendMessage"

    def raise_connect_error(request):
        raise httpx.ConnectError("Connection failed", request=request)

    route = respx.post(url).mock(side_effect=raise_connect_error)

    with pytest.raises(httpx.ConnectError) as exc_info:
        await telegram_client.send_message(chat_id, text)

    assert route.called
    assert "Connection failed" in str(exc_info.value)


@pytest.mark.asyncio
@respx.mock
async def test_send_voice_success():
    chat_id = "123456"
    audio_content = b"fake ogg data"
    url = f"{TELEGRAM_API_URL}/sendVoice"

    route = respx.post(url).mock(return_value=Response(200, json={"ok": True, "result": {"message_id": 1}}))

    result = await telegram_client.send_voice(chat_id, audio_content)

    assert route.called
    assert result["ok"] is True
    assert result["result"]["message_id"] == 1


@pytest.mark.asyncio
@respx.mock
async def test_send_voice_http_error():
    chat_id = "123456"
    audio_content = b"bad ogg data"
    url = f"{TELEGRAM_API_URL}/sendVoice"

    route = respx.post(url).mock(
        return_value=Response(HTTPStatus.BAD_REQUEST, json={"ok": False, "description": "Bad Request"})
    )

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await telegram_client.send_voice(chat_id, audio_content)

    assert route.called
    assert exc_info.value.response.status_code == HTTPStatus.BAD_REQUEST
    assert exc_info.value.response.json() == {"ok": False, "description": "Bad Request"}


@pytest.mark.asyncio
@respx.mock
async def test_send_voice_unexpected_error():
    chat_id = "123456"
    audio_content = b"bad ogg data"
    url = f"{TELEGRAM_API_URL}/sendVoice"

    def raise_connect_error(request):
        raise httpx.ConnectError("Connection failed", request=request)

    route = respx.post(url).mock(side_effect=raise_connect_error)

    with pytest.raises(httpx.ConnectError) as exc_info:
        await telegram_client.send_voice(chat_id, audio_content)

    assert route.called
    assert "Connection failed" in str(exc_info.value)
