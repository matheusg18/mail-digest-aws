import asyncio
import uuid
from datetime import datetime, timezone
from http import HTTPStatus
from typing import Any, Dict

import functions_framework
from flask import Request, make_response
from loguru import logger

from shared.core.logger import trace_id_var
from shared.core.settings import settings
from shared.services.user_service import get_users_with_active_mail_digest_at

from .services.pubsub_service import publish_messages


@functions_framework.http
def handler(request: Request):
    logger.info("Dispatcher handler invoked")

    try:
        triggered_hour = datetime.now(timezone.utc).hour
        result = asyncio.run(_process_mail_digest(triggered_hour))
        return make_response(result, HTTPStatus.OK)
    except Exception as e:
        logger.error("Dispatcher execution failed", extra={"error": e})
        return make_response({"status": "error", "message": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR)


async def _process_mail_digest(triggered_hour: int) -> Dict[str, Any]:
    trace_id_var.set(str(uuid.uuid4()))

    users_with_active_mail_digest = await get_users_with_active_mail_digest_at(triggered_hour)
    messages = [{"user_id": str(user.id)} for user in users_with_active_mail_digest]
    result = publish_messages(messages, settings.PUBSUB_TOPIC_ID)

    logger.success(f"Batch publish summary: {result}")
    return result
