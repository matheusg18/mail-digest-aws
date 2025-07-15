from http import HTTPStatus

import pytest
import respx
from httpx import Response

from shared.core.settings import settings
from shared.exceptions.SumioException import SumioException
from shared.services import telegram_service

TELEGRAM_API_URL = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"


@pytest.mark.asyncio
@respx.mock
async def test_send_message_success():
    chat_id = 123456
    text = "Hello, world!"
    url = f"{TELEGRAM_API_URL}/sendMessage"

    respx.post(url).mock(
        return_value=Response(HTTPStatus.OK, json={"ok": True})
    )

    # Should not raise
    await telegram_service.send_message(chat_id, text)


@pytest.mark.asyncio
@respx.mock
async def test_send_message_failure_status():
    chat_id = 123456
    text = "Hello, world!"
    url = f"{TELEGRAM_API_URL}/sendMessage"

    respx.post(url).mock(
        return_value=Response(HTTPStatus.BAD_REQUEST, json={"ok": False})
    )

    with pytest.raises(SumioException) as exc_info:
        await telegram_service.send_message(chat_id, text)

    assert exc_info.value.message == "Failed to send Telegram message"
    assert exc_info.value.code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
@respx.mock
async def test_send_message_failure_json():
    chat_id = 123456
    text = "Hello, world!"
    url = f"{TELEGRAM_API_URL}/sendMessage"

    respx.post(url).mock(
        return_value=Response(HTTPStatus.OK, json={"ok": False})
    )

    with pytest.raises(SumioException) as exc_info:
        await telegram_service.send_message(chat_id, text)

    assert exc_info.value.message == "Failed to send Telegram message"
    assert exc_info.value.code == HTTPStatus.OK
