import asyncio
import uuid
from http import HTTPStatus
from typing import Any

import functions_framework
from flask import Request, Response, make_response
from loguru import logger

from shared.core.logger import trace_id_var
from shared.core.settings import settings
from shared.domain.telegram.telegram_message import TelegramMessage
from shared.exceptions.sumio_exception import SumioException
from shared.services.telegram_service import process_webhook_message


@functions_framework.http
def handler(request: Request) -> Response:
    logger.info("Telegram webhook handler invoked")

    try:
        _validate_secret_token(request)
        payload = request.get_json(silent=True) or {}
        asyncio.run(_process_payload(payload))
    except Exception as e:
        logger.error("An exception occurred while processing the webhook", extra={"request": request, "error": e})
    finally:
        return make_response("", HTTPStatus.NO_CONTENT)


def _validate_secret_token(request: Request) -> None:
    secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if not secret_token or secret_token != settings.TELEGRAM_WEBHOOK_SECRET_TOKEN:
        raise SumioException(
            "Invalid secret token: token is missing or does not match.",
            code=HTTPStatus.FORBIDDEN,
            details={"token": secret_token},
        )


async def _process_payload(payload: dict[str, Any]) -> None:
    trace_id_var.set(str(uuid.uuid4()))

    if not payload.get("message"):
        raise SumioException(
            "Invalid payload: No message found.",
            code=HTTPStatus.BAD_REQUEST,
            details={"payload": payload},
        )

    message = TelegramMessage.model_validate(payload["message"])
    logger.info("Processing message", extra={"message": message.model_dump()})
    await process_webhook_message(message)
