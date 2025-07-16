from typing import Any, Dict

import httpx
from loguru import logger

from shared.core.settings import settings

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


async def get_access_token(mail_account_credentials: Dict[str, Any]) -> str:
    if not mail_account_credentials.get("refresh_token"):
        logger.warning("No refresh token found in mail account credentials.")
        raise ValueError("No refresh token found in mail account credentials.")

    tokens = await _refresh_access_token(mail_account_credentials["refresh_token"])
    logger.info("Access token refreshed successfully.")

    return tokens["access_token"]


async def _refresh_access_token(refresh_token: str) -> dict:
    logger.info("Refreshing access token using refresh token...")
    data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(GOOGLE_TOKEN_URL, data=data)
        response.raise_for_status()
        return response.json()
