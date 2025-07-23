import asyncio
import base64
import json
import uuid
from http import HTTPStatus
from typing import Any, Dict

import functions_framework
from cloudevents.http import CloudEvent
from loguru import logger

from shared.core.logger import trace_id_var
from shared.exceptions.sumio_exception import SumioException

from .services.email_summary_service import generate_daily_email_summary


@functions_framework.cloud_event
def handler(cloud_event: CloudEvent) -> None:
    logger.info("Starting execution of the worker function")

    try:
        asyncio.run(_process_cloud_event(cloud_event))
    except Exception as e:
        logger.error("Worker execution failed: {}", e, extra={"error": e})


async def _process_cloud_event(cloud_event) -> None:
    trace_id_var.set(str(uuid.uuid4()))

    message_body = _get_message_body(cloud_event)
    user_id = message_body.get("user_id")
    if not user_id:
        logger.error("Pub/Sub message does not contain 'user_id': {}", message_body)
        raise SumioException(
            "Pub/Sub message does not contain 'user_id'",
            code=HTTPStatus.BAD_REQUEST,
            details={"message_body": message_body},
        )

    await generate_daily_email_summary(user_id)


def _get_message_body(cloud_event) -> Dict[str, Any]:
    if not (
        "message" in cloud_event.data and "data" in cloud_event.data["message"] and cloud_event.data["message"]["data"]
    ):
        raise SumioException(
            "Invalid Pub/Sub message format",
            code=HTTPStatus.BAD_REQUEST,
            details={"cloud_event": cloud_event},
        )

    try:
        decoded_data = base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8")
        message_data = json.loads(decoded_data)
        return message_data
    except (ValueError, json.JSONDecodeError) as e:
        raise SumioException(
            "Failed to decode or parse Pub/Sub message data",
            code=HTTPStatus.BAD_REQUEST,
            details={"error": e, "data": cloud_event.data["message"]["data"]},
        ) from e
