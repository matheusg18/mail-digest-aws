import asyncio
import json

import functions_framework
from flask import Request, make_response

from shared.core.logger import L
from shared.core.settings import settings
from shared.services.telegram_service import deal_with_webhook_message


@functions_framework.http
def handler(request: Request):
    request_id = request.headers.get("X-Request-Id", "local")
    logger = L(request_id)
    logger.info("Telegram webhook handler invoked.")

    try:
        secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")

        if not validate_secret_token(secret_token, logger=logger):
            logger.warning("Invalid secret token.")
            return make_response(
                json.dumps({
                    "status": "error",
                    "message": "Forbidden",
                }),
                200,
            )

        payload = request.get_json(silent=True) or {}
        asyncio.run(main_logic(payload, logger=logger))

        return make_response(json.dumps({"status": "ok"}), 200)
    except Exception as e:
        logger.exception("Error processing webhook message", exc_info=e)
        return make_response(json.dumps({"status": "error"}), 200)


def validate_secret_token(secret_token: str | None, logger) -> bool:
    if not secret_token:
        return False

    return secret_token == settings.TELEGRAM_WEBHOOK_SECRET_TOKEN


async def main_logic(payload: dict, *, logger) -> None:
    message = payload.get("message")
    if not message:
        logger.info("No message found in the payload. Ignoring.")
        return

    logger.info(f"Processing message: {message}")
    await deal_with_webhook_message(message, logger=logger)
