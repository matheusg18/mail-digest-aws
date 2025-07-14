import asyncio
import base64
import json

import functions_framework
from cloudevents.http import CloudEvent
from loguru import logger
from services.email_summary_service import (
    generate_daily_email_summary,
)


@functions_framework.cloud_event
def handler(cloud_event: CloudEvent):
    logger.info(
        "Starting execution of the worker function (GCP Pub/Sub trigger)."
    )
    asyncio.run(main_logic(cloud_event))


async def main_logic(cloud_event):
    try:
        data = cloud_event.data
        if isinstance(data, dict) and "message" in data:
            pubsub_message = data["message"]
        else:
            pubsub_message = data
        # Pub/Sub message data is base64-encoded
        message_data = pubsub_message.get("data")
        if not message_data:
            logger.warning("No data field in Pub/Sub message.")
            return {"status": "error", "message": "No data in message."}
        try:
            decoded = base64.b64decode(message_data).decode("utf-8")
            message_body = json.loads(decoded)
        except Exception as e:
            logger.exception(f"Failed to decode or parse Pub/Sub message: {e}")
            return {"status": "error", "message": "Invalid message format."}
        mail_account_id = message_body.get("mail_account_id")
        if not mail_account_id:
            logger.warning(
                "Pub/Sub message does not contain 'mail_account_id': "
                f"{decoded}"
            )
            return {"status": "error", "message": "Missing mail_account_id."}
        await process_single_account(mail_account_id)
        return {"status": "ok"}
    except Exception as e:
        logger.exception(
            f"An error occurred while processing Pub/Sub message: {e}"
        )
        return {"status": "error", "message": str(e)}


async def process_single_account(mail_account_id):
    await generate_daily_email_summary(mail_account_id)
