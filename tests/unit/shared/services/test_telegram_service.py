from http import HTTPStatus
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from shared.core.settings import settings
from shared.domain.delivery_channel import DeliveryChannelEnum
from shared.exceptions.sumio_exception import SumioException
from shared.services import telegram_service
from tests.factories import DeliveryChannelFactory, TelegramChatFactory, TelegramMessageFactory, UserFactory

TELEGRAM_API_URL = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"


@pytest.mark.asyncio
@patch(
    "shared.services.telegram_service.delivery_channel_service.list_user_delivery_channels",
    new_callable=AsyncMock,
    return_value=[],
)
@patch("shared.services.telegram_service.user_service.get_user", new_callable=AsyncMock)
@patch("shared.services.telegram_service.delivery_channel_service.add_delivery_channel", new_callable=AsyncMock)
@patch("shared.services.telegram_service.send_message", new_callable=AsyncMock)
async def test_process_webhook_message_valid_start(
    send_message_mock, add_channel_mock, get_user_mock, list_user_delivery_channels_mock
):
    user = UserFactory()
    chat = TelegramChatFactory()
    message = TelegramMessageFactory(chat=chat, text=f"/start {user.id}")

    get_user_mock.return_value = user

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
@patch("shared.services.telegram_service.send_message", new_callable=AsyncMock)
async def test_process_webhook_message_no_chat(send_message_mock):
    message = TelegramMessageFactory(chat=None, text="/start something")

    with pytest.raises(SumioException) as exc_info:
        await telegram_service.process_webhook_message(message)

    assert exc_info.type is SumioException
    assert exc_info.value.message == "Invalid message: No chat or text found."
    send_message_mock.assert_not_called()


@pytest.mark.asyncio
@patch("shared.services.telegram_service.send_message", new_callable=AsyncMock)
async def test_process_webhook_message_no_text(send_message_mock):
    chat = TelegramChatFactory()
    message = TelegramMessageFactory(chat=chat, text=None)

    with pytest.raises(SumioException) as exc_info:
        await telegram_service.process_webhook_message(message)

    assert exc_info.type is SumioException
    assert exc_info.value.message == "Invalid message: No chat or text found."
    send_message_mock.assert_not_called()


@pytest.mark.asyncio
@patch("shared.services.telegram_service.send_message", new_callable=AsyncMock)
async def test_process_webhook_message_malformed_start(send_message_mock):
    chat = TelegramChatFactory()
    message = TelegramMessageFactory(chat=chat, text="/start")

    with pytest.raises(SumioException) as exc_info:
        await telegram_service.process_webhook_message(message)

    assert exc_info.type is SumioException
    assert exc_info.value.message == "Invalid message: Start command malformed."
    send_message_mock.assert_not_called()


@pytest.mark.asyncio
@patch("shared.services.telegram_service.send_message", new_callable=AsyncMock)
async def test_process_webhook_message_invalid_uuid(send_message_mock):
    chat = TelegramChatFactory()
    message = TelegramMessageFactory(chat=chat, text="/start invalid-uuid")

    with pytest.raises(SumioException) as exc_info:
        await telegram_service.process_webhook_message(message)

    assert exc_info.type is SumioException
    assert exc_info.value.message == "Invalid message: Start command with invalid user_id."
    send_message_mock.assert_not_called()


@pytest.mark.asyncio
@patch("shared.services.telegram_service.user_service.get_user", new_callable=AsyncMock)
@patch("shared.services.telegram_service.send_message", new_callable=AsyncMock)
async def test_process_webhook_message_inexistent_user(send_message_mock, get_user_mock):
    user = UserFactory()
    chat = TelegramChatFactory()
    message = TelegramMessageFactory(chat=chat, text=f"/start {user.id}")

    get_user_mock.return_value = None

    with pytest.raises(SumioException) as exc_info:
        await telegram_service.process_webhook_message(message)

    assert exc_info.type is SumioException
    assert exc_info.value.message == "User not found"
    send_message_mock.assert_awaited_once_with(
        chat.id,
        "❌ Erro ao conectar com o Telegram. Usuário não encontrado.",
    )


@pytest.mark.asyncio
@patch("shared.services.telegram_service.user_service.get_user", new_callable=AsyncMock)
@patch("shared.services.telegram_service.delivery_channel_service.list_user_delivery_channels", new_callable=AsyncMock)
@patch("shared.services.telegram_service.send_message", new_callable=AsyncMock)
async def test_process_webhook_message_user_already_has_telegram_channel(
    send_message_mock, list_user_delivery_channels_mock, get_user_mock
):
    user = UserFactory()
    telegram_delivery_channel = DeliveryChannelFactory(user_id=user.id)
    chat = TelegramChatFactory()
    message = TelegramMessageFactory(chat=chat, text=f"/start {user.id}")

    get_user_mock.return_value = user
    list_user_delivery_channels_mock.return_value = [telegram_delivery_channel]

    await telegram_service.process_webhook_message(message)

    list_user_delivery_channels_mock.assert_awaited_once_with(user.id, channel_type=DeliveryChannelEnum.TELEGRAM)
    send_message_mock.assert_awaited_once_with(
        chat.id,
        "ℹ️ Telegram já está conectado para este usuário!",
    )


@pytest.mark.asyncio
@patch(
    "shared.services.telegram_service.delivery_channel_service.list_user_delivery_channels",
    new_callable=AsyncMock,
    return_value=[],
)
@patch("shared.services.telegram_service.user_service.get_user", new_callable=AsyncMock)
@patch("shared.services.telegram_service.delivery_channel_service.add_delivery_channel", new_callable=AsyncMock)
@patch("shared.services.telegram_service.send_message", new_callable=AsyncMock)
async def test_process_webhook_message_add_delivery_channel_error(
    send_message_mock, add_delivery_channel_mock, get_user_mock, list_user_delivery_channels_mock
):
    user = UserFactory()
    chat = TelegramChatFactory()
    message = TelegramMessageFactory(chat=chat, text=f"/start {user.id}")

    get_user_mock.return_value = user
    add_delivery_channel_mock.side_effect = SumioException(
        "Error adding delivery channel", code=HTTPStatus.INTERNAL_SERVER_ERROR
    )

    with pytest.raises(SumioException) as exc_info:
        await telegram_service.process_webhook_message(message)

    assert exc_info.type is SumioException
    assert exc_info.value.message == "Error adding delivery channel"
    add_delivery_channel_mock.assert_awaited_once_with(
        user_id=user.id,
        chat_id=chat.id,
        channel_type=DeliveryChannelEnum.TELEGRAM,
    )
    send_message_mock.assert_awaited_once_with(
        chat.id,
        "❌ Erro ao conectar com o Telegram. Tente novamente mais tarde.",
    )


@pytest.mark.asyncio
@patch("shared.services.telegram_service.telegram_client.send_message", new_callable=AsyncMock)
@patch("shared.services.telegram_service.telegramify_markdown.telegramify", new_callable=AsyncMock)
async def test_send_message_success(telegramify_mock, send_message_mock):
    chat_id = 123456
    text = "Hello, world!"

    async def telegramify_side_effect(text, interpreters_use):
        return _build_chunk(text, 4090)

    telegramify_mock.side_effect = telegramify_side_effect

    await telegram_service.send_message(chat_id, text)

    send_message_mock.assert_called_once()
    assert send_message_mock.call_args[0][0] == chat_id
    assert send_message_mock.call_args[0][1] == text


@pytest.mark.asyncio
@patch("shared.services.telegram_service.telegram_client.send_message", new_callable=AsyncMock)
@patch("shared.services.telegram_service.telegramify_markdown.telegramify", new_callable=AsyncMock)
async def test_send_message_long_text(telegramify_mock, send_message_mock):
    chat_id = 123456
    text = "A" * 5000

    def telegramify_side_effect(text, interpreters_use):
        return _build_chunk(text, 4090)

    telegramify_mock.side_effect = telegramify_side_effect

    await telegram_service.send_message(chat_id, text)

    assert send_message_mock.call_count == 2  # noqa: PLR2004
    assert send_message_mock.call_args_list[0][0] == (chat_id, text[:4090])
    assert send_message_mock.call_args_list[1][0] == (chat_id, text[4090:])


@pytest.mark.asyncio
@patch(
    "shared.services.telegram_service.telegram_client.send_message",
    new_callable=AsyncMock,
    side_effect=httpx.ConnectError("Connection failed"),
)
@patch("shared.services.telegram_service.telegramify_markdown.telegramify", new_callable=AsyncMock)
async def test_send_message_failure_on_first_chunk(telegramify_mock, send_message_mock):
    chat_id = 123456
    text = "A" * 5000

    async def telegramify_side_effect(text, interpreters_use):
        return _build_chunk(text, 4090)

    telegramify_mock.side_effect = telegramify_side_effect

    with pytest.raises(SumioException) as exc_info:
        await telegram_service.send_message(chat_id, text)

    assert "Failed to send message chunk 1" in str(exc_info.value)
    assert send_message_mock.call_count == 1
    assert send_message_mock.call_args[0][0] == chat_id
    assert send_message_mock.call_args[0][1] == text[:4090]


@pytest.mark.asyncio
@patch(
    "shared.services.telegram_service.telegram_client.send_message",
    new_callable=AsyncMock,
    side_effect=[None, httpx.ConnectError("Connection failed")],
)
@patch("shared.services.telegram_service.telegramify_markdown.telegramify", new_callable=AsyncMock)
async def test_send_message_failure_on_second_chunk(telegramify_mock, send_message_mock):
    chat_id = 123456
    text = "A" * 5000

    async def telegramify_side_effect(text, interpreters_use):
        return _build_chunk(text, 4090)

    telegramify_mock.side_effect = telegramify_side_effect

    with pytest.raises(SumioException) as exc_info:
        await telegram_service.send_message(chat_id, text)

    assert "Failed to send message chunk 2" in str(exc_info.value)
    assert send_message_mock.call_count == 2  # noqa: PLR2004
    assert send_message_mock.call_args_list[0][0] == (chat_id, text[:4090])
    assert send_message_mock.call_args_list[1][0] == (chat_id, text[4090:])


@pytest.mark.asyncio
@patch("shared.services.telegram_service.telegram_client.send_voice", new_callable=AsyncMock)
async def test_send_voice_success(send_voice_mock):
    chat_id = "123456"
    audio_content = b"fake-audio-bytes"

    await telegram_service.send_voice(chat_id, audio_content)

    send_voice_mock.assert_awaited_once_with(chat_id, audio_content)


@pytest.mark.asyncio
@patch(
    "shared.services.telegram_service.telegram_client.send_voice",
    new_callable=AsyncMock,
    side_effect=httpx.ConnectError("Connection failed"),
)
async def test_send_voice_failure(send_voice_mock):
    chat_id = "123456"
    audio_content = b"fake-audio-bytes"

    with pytest.raises(SumioException) as exc_info:
        await telegram_service.send_voice(chat_id, audio_content)

    assert "Failed to send voice message to chat_id=" in str(exc_info.value)
    send_voice_mock.assert_awaited_once_with(chat_id, audio_content)


def _build_chunk(text: str, max_length: int) -> list:
    class Chunk:
        def __init__(self, content):
            self.content = content

    return [Chunk(text[i : i + max_length]) for i in range(0, len(text), max_length)]
