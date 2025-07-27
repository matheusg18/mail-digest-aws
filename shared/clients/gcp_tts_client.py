import base64

import httpx
from loguru import logger

from shared.core.settings import settings
from shared.services import google_auth_service


async def generate_audio(
    text: str, *, language_code: str = "en-US", gender: str = "FEMALE", voice_name: str = "en-US-Chirp3-HD-Achernar"
) -> bytes:
    TTS_API_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"

    access_token = await google_auth_service.get_service_account_token(["https://www.googleapis.com/auth/texttospeech"])

    payload = {
        "input": {"text": text},
        "voice": {"languageCode": language_code, "ssmlGender": gender, "name": voice_name},
        "audioConfig": {"audioEncoding": "OGG_OPUS"},
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "x-goog-user-project": settings.GCP_PROJECT,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(TTS_API_URL, json=payload, headers=headers, timeout=60.0)
            response.raise_for_status()

            response_data = response.json()
            audio_content_b64 = response_data.get("audioContent")

            if not audio_content_b64:
                raise Exception("No audio content received from TTS API")

            return _decode_audio_content(audio_content_b64)
        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error while generating audio: {}",
                e.response.text,
                extra={"text": text, "language_code": language_code, "gender": gender, "voice_name": voice_name},
            )
            raise
        except Exception as e:
            logger.exception(
                "Unexpected error while generating audio: {}",
                e,
                extra={"text": text, "language_code": language_code, "gender": gender, "voice_name": voice_name},
            )
            raise


def _decode_audio_content(audio_content_b64: str) -> bytes:
    """
    Decodes base64 encoded audio content.

    Args:
        audio_content_b64 (str): Base64 encoded audio content.

    Returns:
        bytes: Decoded audio content in bytes.
    """
    return base64.b64decode(audio_content_b64)
