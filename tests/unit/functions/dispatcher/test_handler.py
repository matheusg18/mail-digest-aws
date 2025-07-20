from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch

from flask import Request
from freezegun import freeze_time

from functions.dispatcher import main
from shared.exceptions.sumio_exception import SumioException
from tests.factories import UserFactory

PUBSUB_TOPIC_ID = "pubsub-topic-id-test"


@freeze_time("2025-07-19 13:00:00+00:00")
@patch("functions.dispatcher.main.make_response")
@patch("functions.dispatcher.main.get_users_with_active_mail_digest_at", new_callable=AsyncMock)
@patch("functions.dispatcher.main.publish_messages")
def test_handler_success(mock_publish_messages, mock_get_users_with_active_mail_digest_at, mock_make_response):
    users = [UserFactory(), UserFactory(), UserFactory()]

    mock_get_users_with_active_mail_digest_at.return_value = users
    mock_publish_messages.return_value = {"failed": 0, "successful": 3, "total": 3}

    req = _build_request()
    main.handler(req)

    mock_get_users_with_active_mail_digest_at.assert_awaited_once_with(13)
    mock_publish_messages.assert_called_once_with([{"user_id": str(user.id)} for user in users], PUBSUB_TOPIC_ID)
    mock_make_response.assert_called_once_with({"failed": 0, "successful": 3, "total": 3}, HTTPStatus.OK)


@freeze_time("2025-07-19 13:00:00+00:00")
@patch("functions.dispatcher.main.make_response")
@patch("functions.dispatcher.main.get_users_with_active_mail_digest_at", new_callable=AsyncMock)
@patch("functions.dispatcher.main.publish_messages")
def test_handler_no_users(
    mock_publish_messages,
    mock_get_users_with_active_mail_digest_at,
    mock_make_response,
):
    mock_get_users_with_active_mail_digest_at.return_value = []
    mock_publish_messages.return_value = {"failed": 0, "successful": 0, "total": 0}

    req = _build_request()
    main.handler(req)

    mock_get_users_with_active_mail_digest_at.assert_awaited_once_with(13)
    mock_publish_messages.assert_called_once_with([], PUBSUB_TOPIC_ID)
    mock_make_response.assert_called_once_with({"failed": 0, "successful": 0, "total": 0}, HTTPStatus.OK)


@freeze_time("2025-07-19 13:00:00+00:00")
@patch("functions.dispatcher.main.make_response")
@patch("functions.dispatcher.main.get_users_with_active_mail_digest_at", new_callable=AsyncMock)
@patch("functions.dispatcher.main.publish_messages")
def test_handler_publish_messages_exception(
    mock_publish_messages,
    mock_get_users_with_active_mail_digest_at,
    mock_make_response,
):
    users = [UserFactory()]

    mock_get_users_with_active_mail_digest_at.return_value = users
    mock_publish_messages.side_effect = Exception("PubSub error")

    req = _build_request()
    main.handler(req)

    mock_get_users_with_active_mail_digest_at.assert_awaited_once_with(13)
    mock_publish_messages.assert_called_once_with([{"user_id": str(user.id)} for user in users], PUBSUB_TOPIC_ID)
    mock_make_response.assert_called_once()
    args, kwargs = mock_make_response.call_args
    assert args[0]["status"] == "error"
    assert "PubSub error" in args[0]["message"]
    assert args[1] == HTTPStatus.INTERNAL_SERVER_ERROR


@freeze_time("2025-07-19 13:00:00+00:00")
@patch("functions.dispatcher.main.make_response")
@patch("functions.dispatcher.main.get_users_with_active_mail_digest_at", new_callable=AsyncMock)
@patch("functions.dispatcher.main.publish_messages")
def test_handler_get_users_exception(
    mock_publish_messages,
    mock_get_users_with_active_mail_digest_at,
    mock_make_response,
):
    mock_get_users_with_active_mail_digest_at.side_effect = SumioException(
        "Test error", code=HTTPStatus.INTERNAL_SERVER_ERROR
    )

    req = _build_request()
    main.handler(req)

    mock_get_users_with_active_mail_digest_at.assert_awaited_once_with(13)
    mock_publish_messages.assert_not_called()
    mock_make_response.assert_called_once()
    args, kwargs = mock_make_response.call_args
    assert args[0]["status"] == "error"
    assert "Test error" in args[0]["message"]
    assert args[1] == HTTPStatus.INTERNAL_SERVER_ERROR


def _build_request():
    request = MagicMock(spec=Request)
    return request
