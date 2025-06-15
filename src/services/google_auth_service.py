from datetime import datetime, timedelta

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from core.settings import settings

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


async def get_access_token(user, session: AsyncSession) -> str:
    if user.token_expires_at and user.token_expires_at > datetime.now():
        return user.access_token

    if not user.refresh_token:
        raise ValueError("Refresh token is required to get a new access token.")

    tokens = await _refresh_access_token(user.refresh_token)
    user.access_token = tokens["access_token"]
    user.token_expires_at = datetime.now() + timedelta(
        seconds=tokens.get("expires_in", 3600)
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user.access_token


async def _refresh_access_token(refresh_token: str) -> dict:
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
