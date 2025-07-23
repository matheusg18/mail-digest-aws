import json
from http import HTTPStatus
from unittest.mock import AsyncMock, patch

import pytest
import respx
from httpx import Response

from shared.core.settings import settings
from shared.domain.delivery_channel import DeliveryChannelEnum
from shared.exceptions.sumio_exception import SumioException
from shared.services import telegram_service
from tests.factories import DeliveryChannelFactory, TelegramChatFactory, TelegramMessageFactory, UserFactory

TELEGRAM_API_URL = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"


@pytest.mark.asyncio
async def test_process_webhook_message_valid_start():
    user = UserFactory()
    chat = TelegramChatFactory()
    message = TelegramMessageFactory(chat=chat, text=f"/start {user.id}")

    with (
        patch("shared.services.telegram_service.user_service.get_user", new_callable=AsyncMock, return_value=user),
        patch(
            "shared.services.delivery_channel_service.list_user_delivery_channels",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "shared.services.delivery_channel_service.add_delivery_channel",
            new_callable=AsyncMock,
        ) as add_channel_mock,
        patch("shared.services.telegram_service.send_message", new_callable=AsyncMock) as send_message_mock,
    ):
        await telegram_service.process_webhook_message(message)

    add_channel_mock.assert_awaited_once_with(
        user_id=user.id,
        chat_id=chat.id,
        channel_type=DeliveryChannelEnum.TELEGRAM,
    )
    send_message_mock.assert_awaited_once_with(
        chat.id,
        "✅ Telegram conectado com sucesso!",
    )


@pytest.mark.asyncio
async def test_process_webhook_message_no_chat():
    message = TelegramMessageFactory(chat=None, text="/start something")

    with (
        patch("shared.services.telegram_service.send_message", new_callable=AsyncMock) as send_message_mock,
        pytest.raises(SumioException) as exc_info,
    ):
        await telegram_service.process_webhook_message(message)

    assert exc_info.type is SumioException
    assert exc_info.value.message == "Invalid message: No chat or text found."
    send_message_mock.assert_not_called()


@pytest.mark.asyncio
async def test_process_webhook_message_no_text():
    chat = TelegramChatFactory()
    message = TelegramMessageFactory(chat=chat, text=None)

    with (
        patch("shared.services.telegram_service.send_message", new_callable=AsyncMock) as send_message_mock,
        pytest.raises(SumioException) as exc_info,
    ):
        await telegram_service.process_webhook_message(message)

    assert exc_info.type is SumioException
    assert exc_info.value.message == "Invalid message: No chat or text found."
    send_message_mock.assert_not_called()


@pytest.mark.asyncio
async def test_process_webhook_message_malformed_start():
    chat = TelegramChatFactory()
    message = TelegramMessageFactory(chat=chat, text="/start")

    with (
        patch("shared.services.telegram_service.send_message", new_callable=AsyncMock) as send_message_mock,
        pytest.raises(SumioException) as exc_info,
    ):
        await telegram_service.process_webhook_message(message)

    assert exc_info.type is SumioException
    assert exc_info.value.message == "Invalid message: Start command malformed."
    send_message_mock.assert_not_called()


@pytest.mark.asyncio
async def test_process_webhook_message_invalid_uuid():
    chat = TelegramChatFactory()
    message = TelegramMessageFactory(chat=chat, text="/start invalid-uuid")

    with (
        patch("shared.services.telegram_service.send_message", new_callable=AsyncMock) as send_message_mock,
        pytest.raises(SumioException) as exc_info,
    ):
        await telegram_service.process_webhook_message(message)

    assert exc_info.type is SumioException
    assert exc_info.value.message == "Invalid message: Start command with invalid user_id."
    send_message_mock.assert_not_called()


@pytest.mark.asyncio
async def test_process_webhook_message_inexistent_user():
    user = UserFactory()
    chat = TelegramChatFactory()
    message = TelegramMessageFactory(chat=chat, text=f"/start {user.id}")

    with (
        patch("shared.services.telegram_service.user_service.get_user", new_callable=AsyncMock, return_value=None),
        patch("shared.services.telegram_service.send_message", new_callable=AsyncMock) as send_message_mock,
        pytest.raises(SumioException) as exc_info,
    ):
        await telegram_service.process_webhook_message(message)

    assert exc_info.type is SumioException
    assert exc_info.value.message == "User not found"
    send_message_mock.assert_awaited_once_with(
        chat.id,
        "❌ Erro ao conectar com o Telegram. Usuário não encontrado.",
    )


@pytest.mark.asyncio
async def test_process_webhook_message_user_already_has_telegram_channel():
    user = UserFactory()
    telegram_delivery_channel = DeliveryChannelFactory(user_id=user.id)
    chat = TelegramChatFactory()
    message = TelegramMessageFactory(chat=chat, text=f"/start {user.id}")

    with (
        patch("shared.services.telegram_service.user_service.get_user", new_callable=AsyncMock, return_value=user),
        patch(
            "shared.services.delivery_channel_service.list_user_delivery_channels",
            new_callable=AsyncMock,
            return_value=[telegram_delivery_channel],
        ) as list_channels_mock,
        patch("shared.services.telegram_service.send_message", new_callable=AsyncMock) as send_message_mock,
    ):
        await telegram_service.process_webhook_message(message)

    list_channels_mock.assert_awaited_once_with(user.id, channel_type=DeliveryChannelEnum.TELEGRAM)
    send_message_mock.assert_awaited_once_with(
        chat.id,
        "ℹ️ Telegram já está conectado para este usuário!",
    )


@pytest.mark.asyncio
async def test_process_webhook_message_add_delivery_channel_error():
    user = UserFactory()
    chat = TelegramChatFactory()
    message = TelegramMessageFactory(chat=chat, text=f"/start {user.id}")

    with (
        patch("shared.services.telegram_service.user_service.get_user", new_callable=AsyncMock, return_value=user),
        patch(
            "shared.services.delivery_channel_service.list_user_delivery_channels",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "shared.services.delivery_channel_service.add_delivery_channel",
            new_callable=AsyncMock,
            side_effect=SumioException("Error adding delivery channel", code=HTTPStatus.INTERNAL_SERVER_ERROR),
        ) as add_channel_mock,
        patch("shared.services.telegram_service.send_message", new_callable=AsyncMock) as send_message_mock,
        pytest.raises(SumioException) as exc_info,
    ):
        await telegram_service.process_webhook_message(message)

    assert exc_info.type is SumioException
    assert exc_info.value.message == "Error adding delivery channel"
    add_channel_mock.assert_awaited_once_with(
        user_id=user.id,
        chat_id=chat.id,
        channel_type=DeliveryChannelEnum.TELEGRAM,
    )
    send_message_mock.assert_awaited_once_with(
        chat.id,
        "❌ Erro ao conectar com o Telegram. Tente novamente mais tarde.",
    )


@pytest.mark.asyncio
@respx.mock
async def test_send_message_success():
    chat_id = 123456
    text = "Hello, world!"
    url = f"{TELEGRAM_API_URL}/sendMessage"

    route = respx.post(url).mock(return_value=Response(HTTPStatus.OK, json={"ok": True}))

    await telegram_service.send_message(chat_id, text)

    assert route.called
    assert route.call_count == 1
    assert json.loads(route.calls[0][0].content.decode()) == {"chat_id": chat_id, "text": text}


@pytest.mark.asyncio
@respx.mock
async def test_send_message_empty_text():
    chat_id = 123456
    text = ""
    url = f"{TELEGRAM_API_URL}/sendMessage"

    route = respx.post(url).mock(return_value=Response(HTTPStatus.OK, json={"ok": True}))

    await telegram_service.send_message(chat_id, text)

    assert not route.called


@pytest.mark.asyncio
@respx.mock
async def test_send_message_failure():
    chat_id = 123456
    text = "Hello, world!"
    url = f"{TELEGRAM_API_URL}/sendMessage"

    respx.post(url).mock(return_value=Response(HTTPStatus.BAD_REQUEST, json={"ok": False}))

    with pytest.raises(SumioException) as exc_info:
        await telegram_service.send_message(chat_id, text)

    assert exc_info.value.message.startswith("Failed to send Telegram message")
    assert exc_info.value.code == HTTPStatus.INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
@respx.mock
async def test_send_message_long_text():
    chat_id = 123456
    text = "A" * 5000
    url = f"{TELEGRAM_API_URL}/sendMessage"

    route = respx.post(url).mock(return_value=Response(HTTPStatus.OK, json={"ok": True}))

    await telegram_service.send_message(chat_id, text)

    assert route.called
    assert route.call_count == 2  # noqa: PLR2004
    assert json.loads(route.calls[0][0].content.decode()) == {"chat_id": chat_id, "text": "A" * 4096}
    assert json.loads(route.calls[1][0].content.decode()) == {"chat_id": chat_id, "text": "A" * 904}
