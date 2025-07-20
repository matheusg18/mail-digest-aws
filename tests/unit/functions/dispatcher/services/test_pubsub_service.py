import uuid
from unittest.mock import MagicMock, patch

from google.api_core.exceptions import GoogleAPICallError

from functions.dispatcher.services import pubsub_service

GCP_PROJECT = "sumio"


@patch("functions.dispatcher.services.pubsub_service._publisher", new_callable=MagicMock)
def test_publish_messages_no_messages(mock_publisher):
    topic_id = "test-topic"

    result = pubsub_service.publish_messages([], topic_id)

    assert result == {"successful": 0, "failed": 0, "total": 0}
    mock_publisher.publish.assert_not_called()


@patch("functions.dispatcher.services.pubsub_service._publisher", new_callable=MagicMock)
def test_publish_messages_all_success(mock_publisher):
    messages = [{"user_id": str(uuid.uuid4())}, {"user_id": str(uuid.uuid4())}]
    topic_id = "test-topic"

    mock_future = MagicMock()
    mock_future.result.return_value = None

    mock_publisher.topic_path.return_value = f"projects/{GCP_PROJECT}/topics/{topic_id}"
    mock_publisher.publish.return_value = mock_future

    result = pubsub_service.publish_messages(messages, topic_id)

    assert result == {"successful": 2, "failed": 0, "total": 2}
    assert mock_publisher.publish.call_count == 2  # noqa: PLR2004


@patch("functions.dispatcher.services.pubsub_service._publisher", new_callable=MagicMock)
def test_publish_messages_some_fail(mock_publisher):
    messages = [{"user_id": str(uuid.uuid4())}, {"user_id": str(uuid.uuid4())}]
    topic_id = "test-topic"

    mock_future_success = MagicMock()
    mock_future_success.result.return_value = None
    mock_future_fail = MagicMock()
    mock_future_fail.result.side_effect = GoogleAPICallError("fail")

    mock_publisher.topic_path.return_value = f"projects/{GCP_PROJECT}/topics/{topic_id}"
    # First publish returns success, second returns fail
    mock_publisher.publish.side_effect = [mock_future_success, mock_future_fail]

    result = pubsub_service.publish_messages(messages, topic_id)

    assert result == {"successful": 1, "failed": 1, "total": 2}
    assert mock_publisher.publish.call_count == 2  # noqa: PLR2004


@patch("functions.dispatcher.services.pubsub_service._publisher", new_callable=MagicMock)
def test_publish_messages_publish_raises(mock_publisher):
    messages = [{"user_id": str(uuid.uuid4())}]
    topic_id = "test-topic"

    mock_publisher.topic_path.return_value = f"projects/{GCP_PROJECT}/topics/{topic_id}"
    mock_publisher.publish.side_effect = Exception("fail to schedule")

    result = pubsub_service.publish_messages(messages, topic_id)

    assert result == {"successful": 0, "failed": 1, "total": 1}
    mock_publisher.publish.assert_called_once()
