from typing import Any, Dict

import httpx
from loguru import logger

from shared.core.settings import settings
from shared.exceptions.sumio_exception import SumioException

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
        try:
            response = await client.post(GOOGLE_TOKEN_URL, data=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to refresh token: {e.response.status_code} - {e.response.text}")

            error_data = e.response.json()
            error_reason = error_data.get("error")
            if error_reason in {"invalid_grant", "unauthorized_client"}:
                raise SumioException("The refresh token is invalid or has expired.")
            raise SumioException(
                "Failed to refresh access token",
                code=e.response.status_code,
                details={"error": error_data},
            ) from e
