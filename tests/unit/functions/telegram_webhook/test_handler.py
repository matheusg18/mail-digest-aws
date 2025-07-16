from http import HTTPStatus
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

from flask import Request

from functions.telegram_webhook import main
from shared.exceptions.sumio_exception import SumioException
from tests.factories import TelegramMessageFactory

TELEGRAM_WEBHOOK_SECRET_TOKEN = "telegram-webhook-secret-token-test"


@patch("functions.telegram_webhook.main.make_response")
@patch("functions.telegram_webhook.main.process_webhook_message", new_callable=AsyncMock)
def test_handler_success(mock_process_webhook_message, mock_make_response):
    message = TelegramMessageFactory()
    req = _build_request(
        headers={"X-Telegram-Bot-Api-Secret-Token": TELEGRAM_WEBHOOK_SECRET_TOKEN},
        json_data={"message": message.model_dump()},
    )

    main.handler(req)

    assert mock_process_webhook_message.call_count == 1
    mock_process_webhook_message.assert_awaited_once_with(message)
    assert mock_make_response.call_count == 1
    mock_make_response.assert_called_once_with(HTTPStatus.NO_CONTENT)


@patch("functions.telegram_webhook.main.make_response")
@patch("functions.telegram_webhook.main.process_webhook_message", new_callable=AsyncMock)
def test_handler_missing_secret_token(mock_process_webhook_message, mock_make_response):
    message = TelegramMessageFactory()
    req = _build_request(
        headers={},
        json_data={"message": message.model_dump()},
    )

    main.handler(req)

    mock_process_webhook_message.assert_not_called()
    assert mock_make_response.call_count == 1
    mock_make_response.assert_called_once_with(HTTPStatus.NO_CONTENT)


@patch("functions.telegram_webhook.main.make_response")
@patch("functions.telegram_webhook.main.process_webhook_message", new_callable=AsyncMock)
def test_handler_invalid_secret_token(mock_process_webhook_message, mock_make_response):
    message = TelegramMessageFactory()
    req = _build_request(
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong-token"},
        json_data={"message": message.model_dump()},
    )

    main.handler(req)

    mock_process_webhook_message.assert_not_called()
    assert mock_make_response.call_count == 1
    mock_make_response.assert_called_once_with(HTTPStatus.NO_CONTENT)


@patch("functions.telegram_webhook.main.make_response")
@patch("functions.telegram_webhook.main.process_webhook_message", new_callable=AsyncMock)
def test_handler_missing_message_in_payload(mock_process_webhook_message, mock_make_response):
    req = _build_request(
        headers={"X-Telegram-Bot-Api-Secret-Token": TELEGRAM_WEBHOOK_SECRET_TOKEN},
        json_data={},
    )

    main.handler(req)

    mock_process_webhook_message.assert_not_called()
    assert mock_make_response.call_count == 1
    mock_make_response.assert_called_once_with(HTTPStatus.NO_CONTENT)


@patch("functions.telegram_webhook.main.make_response")
@patch("functions.telegram_webhook.main.process_webhook_message", new_callable=AsyncMock)
def test_handler_exception_in_process_webhook_message(mock_process_webhook_message, mock_make_response):
    mock_process_webhook_message.side_effect = SumioException("Test exception")

    message = TelegramMessageFactory()
    req = _build_request(
        headers={"X-Telegram-Bot-Api-Secret-Token": TELEGRAM_WEBHOOK_SECRET_TOKEN},
        json_data={"message": message.model_dump()},
    )

    main.handler(req)

    mock_process_webhook_message.assert_awaited_once_with(message)
    assert mock_make_response.call_count == 1
    mock_make_response.assert_called_once_with(HTTPStatus.NO_CONTENT)


def _build_request(headers: Dict[str, str] | None = None, json_data: Dict[str, Any] | None = None) -> Request:
    request = MagicMock(spec=Request)
    request.headers = headers or {}
    request.get_json.return_value = json_data
    return request
