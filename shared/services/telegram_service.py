import uuid
from http import HTTPStatus

import httpx
from loguru import logger

from shared.core.settings import settings
from shared.domain.delivery_channel import DeliveryChannelEnum
from shared.domain.telegram.telegram_message import TelegramMessage
from shared.exceptions.sumio_exception import SumioException
from shared.services import delivery_channel_service, user_service

TELEGRAM_API_URL = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"


async def process_webhook_message(message: TelegramMessage) -> None:
    if message.chat is None or not message.text:
        raise SumioException(
            "Invalid message: No chat or text found.",
            code=HTTPStatus.BAD_REQUEST,
            details={"message": message.model_dump()},
        )

    if message.text.startswith("/start"):
        await _handle_start_command(message.text, message.chat.id)


async def _handle_start_command(text: str, chat_id: int) -> None:
    START_COMMAND_PARTS = 2
    parts = text.split()
    if len(parts) != START_COMMAND_PARTS:
        raise SumioException(
            "Invalid message: Start command malformed.",
            code=HTTPStatus.BAD_REQUEST,
            details={"text": text, "chat_id": chat_id},
        )

    try:
        user_id = uuid.UUID(parts[1])
    except (ValueError, AttributeError) as e:
        raise SumioException(
            "Invalid message: Start command with invalid user_id.",
            code=HTTPStatus.BAD_REQUEST,
            details={"text": text, "chat_id": chat_id, "error": e},
        )

    logger.info(f"Processing /start command for code: {user_id}")
    await _add_telegram_delivery_channel(user_id, chat_id)


async def _add_telegram_delivery_channel(user_id: uuid.UUID, chat_id: int) -> None:
    user = await user_service.get_user(user_id)
    if not user:
        await send_message(
            chat_id,
            "❌ Erro ao conectar com o Telegram. Usuário não encontrado.",
        )
        raise SumioException(
            "User not found",
            code=HTTPStatus.NOT_FOUND,
            details={"user_id": user_id, "chat_id": chat_id},
        )

    if await _user_already_has_telegram_channel(user_id):
        logger.warning(f"User with ID {user_id} already has a Telegram channel connected.")
        await send_message(chat_id, "ℹ️ Telegram já está conectado para este usuário!")
        return

    try:
        await delivery_channel_service.add_delivery_channel(
            user_id=user_id,
            chat_id=chat_id,
            channel_type=DeliveryChannelEnum.TELEGRAM,
        )
        logger.success(f"Telegram connected successfully for user: {user_id}")
        await send_message(chat_id, "✅ Telegram conectado com sucesso!")
    except SumioException as e:
        logger.error(f"Error connecting Telegram for user {user_id}: {e}")
        await send_message(
            chat_id,
            "❌ Erro ao conectar com o Telegram. Tente novamente mais tarde.",
        )
        raise e


async def _user_already_has_telegram_channel(user_id: uuid.UUID) -> bool:
    channels = await delivery_channel_service.list_user_delivery_channels(
        user_id, channel_type=DeliveryChannelEnum.TELEGRAM
    )
    return len(channels) > 0


async def send_message(chat_id: int, text: str) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TELEGRAM_API_URL}/sendMessage",
            json={"chat_id": chat_id, "text": text},
        )

        is_ok = response.status_code == HTTPStatus.OK and response.json().get("ok", False)
        if not is_ok:
            raise SumioException(
                "Failed to send Telegram message",
                code=response.status_code,
                details={
                    "chat_id": chat_id,
                    "text": text,
                    "response": response.json(),
                },
            )
