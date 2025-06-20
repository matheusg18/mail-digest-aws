import asyncio
import json

import loguru

from core.logger import L
from core.settings import settings
from services.telegram_service import deal_with_webhook_message


def lambda_handler(event, context):
    request_id = context.aws_request_id if context else "local"
    logger = L(request_id)
    logger.info("Telegram webhook handler invoked.")

    try:
        secret_token = event.get("headers", {}).get(
            "X-Telegram-Bot-Api-Secret-Token"
        )

        if not validate_secret_token(secret_token):
            logger.warning("Invalid secret token.")
            return {
                "statusCode": 403,
                "body": json.dumps({
                    "status": "error",
                    "message": "Forbidden",
                }),
            }

        payload = json.loads(event.get("body", "{}"))
        asyncio.run(main_logic(payload, logger=logger))

        return {"statusCode": 200, "body": json.dumps({"status": "ok"})}
    except Exception as e:
        logger.exception("Error processing webhook message", exc_info=e)
        return {"statusCode": 200, "body": json.dumps({"status": "error"})}


def validate_secret_token(secret_token: str) -> bool:
    if not secret_token:
        return False

    return secret_token == settings.TELEGRAM_WEBHOOK_SECRET_TOKEN


async def main_logic(payload: dict, *, logger: loguru.Logger) -> None:
    message = payload.get("message")
    if not message:
        logger.info("No message found in the payload. Ignoring.")
        return

    logger.info(f"Processing message: {message}")
    await deal_with_webhook_message(message, logger=logger)
