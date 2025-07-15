from http import HTTPStatus

import httpx
from loguru import logger

from shared.core.settings import settings
from shared.domain.delivery_channel import DeliveryChannelEnum
from shared.exceptions.SumioException import SumioException
from shared.services import user_service

TELEGRAM_API_URL = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"
START_COMMAND_PARTS = 2


async def process_webhook_message(message: dict) -> None:
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if not text or not chat_id:
        logger.info("No text or chat_id found in the message. Ignoring.")
        return

    if text.startswith("/start"):
        await _handle_start_command(message)


async def _handle_start_command(message: dict) -> None:
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    parts = text.split()
    if len(parts) != START_COMMAND_PARTS:
        logger.warning(f"Malformed /start command received: {text}")
        return

    user_id = parts[1]
    logger.info(f"Processing /start command for code: {user_id}")

    user = await user_service.get_user(user_id=user_id)
    if not user:
        logger.warning(f"User with ID {user_id} not found.")
        await send_message(
            chat_id,
            "❌ Erro ao conectar com o Telegram. Usuário não encontrado.",
        )
        return

    try:
        await user_service.add_delivery_channel(
            user_id=user_id,
            chat_id=chat_id,
            channel_type=DeliveryChannelEnum.TELEGRAM,
        )
        logger.success(f"Telegram connected successfully for user: {user_id}")
        await send_message(chat_id, "✅ Telegram conectado com sucesso!")
    except Exception as e:
        logger.exception(f"Error connecting Telegram for user {user_id}: {e}")
        await send_message(
            chat_id,
            "❌ Erro ao conectar com o Telegram. Tente novamente mais tarde.",
        )


async def send_message(chat_id: int, text: str) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TELEGRAM_API_URL}/sendMessage",
            json={"chat_id": chat_id, "text": text},
        )

        is_ok = response.status_code == HTTPStatus.OK and response.json().get(
            "ok", False
        )
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
