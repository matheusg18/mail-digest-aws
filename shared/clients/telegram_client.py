from typing import Dict

import httpx
from loguru import logger

from shared.core.settings import settings

TELEGRAM_API_URL = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"


async def send_message(chat_id: int, text: str) -> Dict:
    """
    Sends a text message to a specified Telegram chat using the Telegram Bot API.
    The message is sent in MarkdownV2 format.

    Args:
        chat_id (int): The unique identifier for the target chat.
        text (str): The message text to be sent.

    Returns:
        Dict: The JSON response from the Telegram API as a dictionary.

    Raises:
        httpx.HTTPStatusError: If the Telegram API returns an error response.
        Exception: For any other unexpected errors during the request.
    """
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "MarkdownV2"}

    logger.info(f"Sending message to chat_id={chat_id}: {text[:20]}...")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=30.0)
            response.raise_for_status()
            logger.success(f"Text message sent successfully to chat_id={chat_id}")
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to send text message to chat_id={chat_id}: {e.response.text}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error while sending text message to chat_id={chat_id}: {e}")
            raise


async def send_voice(chat_id: str, audio_content: bytes) -> Dict:
    """
    Sends a voice message to a specified Telegram chat using the Telegram Bot API.

    Args:
        chat_id (int): The unique identifier for the target chat.
        audio_content (bytes): The audio content in bytes, expected to be in OGG format.

    Returns:
        Dict: The JSON response from the Telegram API as a dictionary.

    Raises:
        httpx.HTTPStatusError: If the Telegram API returns an error response.
        Exception: For any other unexpected errors during the request.
    """
    url = f"{TELEGRAM_API_URL}/sendVoice"
    files = {"voice": ("voice.ogg", audio_content, "audio/ogg")}
    data = {"chat_id": chat_id, "caption": "Voice message generated with GCP TTS"}

    logger.info(f"Sending voice message to chat_id={chat_id}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, files=files, data=data, timeout=30.0)
            response.raise_for_status()
            logger.success(f"Voice message sent successfully to chat_id={chat_id}")
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to send voice message to chat_id={chat_id}: {e.response.text}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error while sending voice message to chat_id={chat_id}: {e}")
            raise
