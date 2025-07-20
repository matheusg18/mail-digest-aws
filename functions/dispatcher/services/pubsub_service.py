import json
from typing import Any, Dict, List

from google.api_core.exceptions import GoogleAPICallError
from google.cloud.pubsub_v1 import PublisherClient
from google.cloud.pubsub_v1.publisher.futures import Future
from google.cloud.pubsub_v1.types import BatchSettings
from loguru import logger

from shared.core.settings import settings

_batch_settings = BatchSettings(
    max_messages=100,
    max_bytes=1024 * 1024,  # 1 MB
    max_latency=0.1,  # 100 ms
)

_publisher = PublisherClient(batch_settings=_batch_settings)


def publish_messages(messages: List[Dict[str, Any]], topic_id: str) -> Dict[str, int]:
    if not messages:
        logger.info("No messages provided for publishing.")
        return {"successful": 0, "failed": 0, "total": 0}

    topic_path = _publisher.topic_path(settings.GCP_PROJECT, topic_id)
    publish_futures: List[Future] = []

    for message in messages:
        try:
            message_body = json.dumps(message).encode("utf-8")
            future = _publisher.publish(topic_path, message_body)
            publish_futures.append(future)
        except Exception as e:
            logger.error("Failed to schedule message for publishing: {}", message, extra={"error": e})

    successful_count = 0
    for future in publish_futures:
        try:
            future.result(timeout=30)
            successful_count += 1
        except GoogleAPICallError as e:
            logger.error("Message failed to publish", extra={"error": e})

    failed_count = len(messages) - successful_count
    total = len(messages)

    logger.info(
        f"Publish completed: {successful_count} successful, {failed_count} failed",
        extra={"topic": topic_id, "successful": successful_count, "failed": failed_count, "total": total},
    )

    return {"successful": successful_count, "failed": failed_count, "total": total}
