import uuid
from typing import List

from core.supabase_client import create_supabase_client
from domain.delivery_channel import DeliveryChannel


async def get_active_delivery_channels(
    user_id: uuid.UUID, *, logger
) -> List[DeliveryChannel]:
    supabase = await create_supabase_client()
    try:
        logger.info(
            f"Fetching active delivery channels for user ID: {user_id}"
        )
        response = (
            await supabase.table("delivery_channels")
            .select("*")
            .eq("user_id", str(user_id))
            .eq("is_active", True)
            .execute()
        )

        if not response.data:
            logger.warning(
                f"No active delivery channels found for user ID {user_id}."
            )
            return []

        logger.success(f"Active delivery channels found: {response.data}")
        return [DeliveryChannel(**channel) for channel in response.data]
    except Exception as e:
        logger.error(f"Error fetching active delivery channels: {e}")
        raise Exception(f"Error fetching active delivery channels: {e}") from e
