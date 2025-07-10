import asyncio
import json

import functions_framework
from flask import Request, make_response
from google.cloud import pubsub_v1

from shared.core.logger import L
from shared.core.settings import settings
from shared.core.supabase_client import create_supabase_client


async def get_active_mail_accounts_from_db(*, logger):
    logger.info("Searching for active mail accounts in the database...")
    supabase = await create_supabase_client()
    try:
        response = (
            await supabase.table("mail_accounts")
            .select("id")
            .eq("is_active", True)
            .execute()
        )
        active_mail_accounts = response.data

        logger.success(
            f"{len(active_mail_accounts)} mail active accounts found."
        )
        return active_mail_accounts
    except Exception as e:
        logger.exception(f"Error fetching active mail accounts: {e}")
        raise e


@functions_framework.http
def handler(request: Request):
    request_id = request.headers.get("X-Request-Id", "local")
    logger = L(request_id)
    logger.info("Iniciando execução do dispatcher.")
    try:
        result = asyncio.run(main_logic(logger=logger))
        return make_response(json.dumps(result), 200)
    except Exception as e:
        logger.exception(f"Dispatcher execution failed: {e}")
        return make_response(
            json.dumps({"status": "error", "message": str(e)}), 500
        )


async def main_logic(*, logger):
    if not settings.GCP_PROJECT or not settings.PUBSUB_TOPIC_ID:
        raise EnvironmentError(
            "GCP_PROJECT/GOOGLE_CLOUD_PROJECT and PUBSUB_TOPIC environment variables must be set."
        )

    active_mail_accounts = await get_active_mail_accounts_from_db(
        logger=logger
    )

    if not active_mail_accounts:
        logger.info("No active mail accounts found to process.")
        return {
            "status": "ok",
            "message": "No active mail accounts found to process.",
            "total_accounts": 0,
            "success_count": 0,
            "failure_count": 0,
        }

    logger.info(
        f"Found {len(active_mail_accounts)} active mail accounts to process."
    )
    success_count = 0
    failure_count = 0

    for mail_account in active_mail_accounts:
        mail_account_id = mail_account.get("id")
        if not mail_account_id:
            logger.info(
                f"Skipping mail account with missing id: {mail_account}"
            )
            failure_count += 1
            continue
        try:
            message_body = json.dumps({"mail_account_id": mail_account_id})
            await publish_to_pubsub(message_body, logger)
            logger.success(
                f"Message sent to Pub/Sub for mail_account_id: {mail_account_id}"
            )
            success_count += 1
        except Exception as e:
            logger.exception(
                f"Failed to send message for mail_account_id {mail_account_id}: {e}"
            )
            failure_count += 1

    logger.success(
        f"Process completed: {success_count} successful, "
        f"{failure_count} failed."
    )
    return {
        "status": "ok",
        "message": "Process completed.",
        "total_accounts": len(active_mail_accounts),
        "success_count": success_count,
        "failure_count": failure_count,
    }


async def publish_to_pubsub(message_body: str, logger):
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(
        settings.GCP_PROJECT, settings.PUBSUB_TOPIC_ID
    )
    future = publisher.publish(topic_path, message_body.encode("utf-8"))
    await asyncio.get_event_loop().run_in_executor(None, future.result)
    logger.info(
        f"Published message to {settings.PUBSUB_TOPIC_ID}: {message_body}"
    )
