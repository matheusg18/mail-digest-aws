import json
import asyncio

from core.logger import L
from services.telegram_service import deal_with_webhook_message


def lambda_handler(event, context):
    request_id = context.aws_request_id if context else "local"
    logger = L(request_id)
    logger.info("Telegram webhook handler invoked.")

    try:
        payload = json.loads(event.get("body", "{}"))
        logger.info(f"Payload received: {payload}")

        asyncio.run(main_logic(payload, logger=logger))

        return {"statusCode": 200, "body": json.dumps({"status": "ok"})}
    except Exception as e:
        logger.exception("Error processing webhook message", exc_info=e)
        return {"statusCode": 200, "body": json.dumps({"status": "error"})}


async def main_logic(payload: dict, *, logger):
    message = payload.get("message")
    if not message:
        logger.info("No message found in the payload. Ignoring.")
        return

    logger.info(f"Processing message: {message}")
    await deal_with_webhook_message(message, logger=logger)
