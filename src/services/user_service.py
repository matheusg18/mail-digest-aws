import json
import uuid

from core.supabase_client import create_supabase_client
from domain.delivery_channel import DeliveryChannel, DeliveryChannelEnum
from domain.user import User


async def get_user(user_id: uuid.UUID, *, logger) -> User | None:
    supabase = await create_supabase_client()
    try:
        logger.info(f"Fetching user with ID: {user_id}")
        response = (
            await supabase.table("users").select("*").eq("id", str(user_id)).execute()
        )

        if not response.data:
            logger.warning(f"User with ID {user_id} not found.")
            return None

        logger.success(f"User found: {response.data[0]}")
        return User(**response.data[0])
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        raise Exception(f"Error fetching user: {e}") from e


async def add_delivery_channel(
    user_id: uuid.UUID,
    chat_id: int,
    channel_type: DeliveryChannelEnum,
    is_active: bool = True,
    *,
    logger,
) -> DeliveryChannel:
    supabase = await create_supabase_client()
    try:
        delivery_channel = DeliveryChannel(
            user_id=user_id,
            channel_type=channel_type,
            address=str(chat_id),
            is_active=is_active,
        )

        logger.info(f"Adding delivery channel: {delivery_channel.model_dump()}")
        response = (
            await supabase.table("delivery_channels")
            .insert(json.loads(delivery_channel.model_dump_json()))
            .execute()
        )

        logger.success(f"Delivery channel added successfully: {response.data[0]}")
        return DeliveryChannel(**response.data[0])
    except Exception as e:
        logger.error(f"Error adding delivery channel: {e}")
        raise Exception(f"Error adding delivery channel: {e}") from e
