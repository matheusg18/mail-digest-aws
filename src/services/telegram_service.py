from http import HTTPStatus

import httpx

from core.settings import settings

TELEGRAM_API_URL = f'https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}'


async def send_telegram_message(chat_id: int, text: str) -> bool:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f'{TELEGRAM_API_URL}/sendMessage',
            json={'chat_id': chat_id, 'text': text},
        )
        return response.status_code == HTTPStatus.OK and response.json().get(
            'ok', False
        )
