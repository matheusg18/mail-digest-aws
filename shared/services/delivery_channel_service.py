import uuid
from http import HTTPStatus
from typing import List, Optional

from loguru import logger

from shared.core.supabase_client import create_supabase_client
from shared.domain.delivery_channel import DeliveryChannel, DeliveryChannelEnum
from shared.exceptions.sumio_exception import SumioException


async def list_user_delivery_channels(
    user_id: uuid.UUID,
    *,
    is_active: Optional[bool] = None,
    channel_type: Optional[DeliveryChannelEnum] = None,
) -> List[DeliveryChannel]:
    supabase_client = await create_supabase_client()

    try:
        logger.info(
            f"Fetching delivery channels for user ID: {str(user_id)}",
            extra={"is_active": is_active, "channel_type": str(channel_type)},
        )

        query = supabase_client.table("delivery_channels").select("*")
        query = query.eq("user_id", str(user_id))
        if is_active is not None:
            query = query.eq("is_active", is_active)
        if channel_type is not None:
            query = query.eq("channel_type", channel_type.value)

        response = await query.execute()

        logger.info(
            f"Delivery channels fetched successfully for user ID: {str(user_id)}",
            extra={"count": len(response.data)},
        )
        return [DeliveryChannel(**channel) for channel in response.data]
    except Exception as e:
        logger.error("Error fetching active delivery channels", extra={"error": e})
        raise SumioException(
            "Error fetching active delivery channels",
            code=HTTPStatus.INTERNAL_SERVER_ERROR,
            details={
                "user_id": str(user_id),
                "is_active": is_active,
                "channel_type": str(channel_type),
                "error": str(e),
            },
        ) from e


async def add_delivery_channel(
    user_id: uuid.UUID,
    chat_id: int,
    channel_type: DeliveryChannelEnum,
    is_active: bool = True,
) -> DeliveryChannel:
    supabase_client = await create_supabase_client()

    try:
        delivery_channel = DeliveryChannel(
            user_id=user_id,
            channel_type=channel_type,
            address=str(chat_id),
            is_active=is_active,
        )

        logger.info("Adding delivery channel")
        response = (
            await supabase_client.table("delivery_channels").insert(delivery_channel.model_dump(mode="json")).execute()
        )

        logger.success("Delivery channel added successfully")
        return DeliveryChannel(**response.data[0])
    except Exception as e:
        logger.error("Error adding delivery channel", extra={"error": e})
        raise SumioException(
            "Error adding delivery channel",
            code=HTTPStatus.INTERNAL_SERVER_ERROR,
            details={
                "user_id": str(user_id),
                "chat_id": chat_id,
                "channel_type": str(channel_type),
                "is_active": is_active,
                "error": str(e),
            },
        ) from e
