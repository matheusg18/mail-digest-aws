import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List

import functions_framework
from flask import Request, make_response
from google.cloud import pubsub_v1
from loguru import logger

from shared.core.settings import settings
from shared.core.supabase_client import create_supabase_client

publisher = pubsub_v1.PublisherClient()


@functions_framework.http
def handler(request: Request):
    triggered_hour = datetime.now(timezone.utc).hour
    logger.info(
        "Starting dispatcher execution. "
        f"Triggered hour (UTC): {triggered_hour}"
    )

    try:
        result = asyncio.run(main_logic(triggered_hour))
        return make_response(json.dumps(result), 200)
    except Exception as e:
        logger.error("Dispatcher execution failed", extra={"error": e})
        return make_response(
            json.dumps({"status": "error", "message": str(e)}), 500
        )


async def main_logic(triggered_hour: int):
    users_with_active_mail_digest = await get_users_with_active_mail_digest_at(
        triggered_hour
    )

    if not users_with_active_mail_digest:
        logger.info(
            f"No users found with active mail digest at {triggered_hour}h"
        )

        return {
            "status": "ok",
            "message": "No active mail accounts found.",
        }

    for user in users_with_active_mail_digest:
        try:
            message_body = json.dumps({"user_id": user.get("id")})
            await publish_to_pubsub(message_body)
            logger.success(
                f"Message sent to Pub/Sub for user: {user.get('full_name')}"
            )
        except Exception as e:
            logger.error(
                f"Failed to send message for user {user.get('full_name')}",
                extra={"error": e},
            )

    return {
        "status": "ok",
        "message": "Process completed.",
    }


async def get_users_with_active_mail_digest_at(
    digest_hour: int,
) -> List[Dict[str, uuid.UUID]]:
    logger.info(f"Searching for users with active digest at {digest_hour}h...")
    supabase = await create_supabase_client()

    try:
        response = (
            await supabase.from_("mail_digest_configs")
            .select("digest_hour, is_active, users(id, full_name)")
            .eq("digest_hour", digest_hour)
            .eq("is_active", True)
            .execute()
        )
        users_with_active_mail_digest = response.data
        users_with_active_mail_digest = [
            x["users"] for x in users_with_active_mail_digest
        ]

        logger.success(
            f"{len(users_with_active_mail_digest)} users found "
            f"with active mail digest at {digest_hour}h"
        )
        return users_with_active_mail_digest
    except Exception as e:
        logger.error(
            "Error fetching users with active mail digest", extra={"error": e}
        )
        raise e


async def publish_to_pubsub(message_body: str):
    topic_path = publisher.topic_path(
        settings.GCP_PROJECT, settings.PUBSUB_TOPIC_ID
    )
    future = publisher.publish(topic_path, message_body.encode("utf-8"))
    loop = asyncio.get_running_loop()

    try:
        await loop.run_in_executor(None, future.result)
        logger.info(f"Published message to {settings.PUBSUB_TOPIC_ID}")
    except Exception as e:
        logger.error("Failed to publish message", extra={"error": e})
