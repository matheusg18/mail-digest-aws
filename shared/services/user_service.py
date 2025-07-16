import uuid

from loguru import logger

from shared.core.supabase_client import create_supabase_client
from shared.domain.user import User


async def get_user(user_id: uuid.UUID) -> User | None:
    supabase = await create_supabase_client()
    try:
        logger.info(f"Fetching user with ID: {user_id}")
        response = (
            await supabase.table("users")
            .select("*")
            .eq("id", str(user_id))
            .execute()
        )

        if not response.data:
            logger.warning(f"User with ID {user_id} not found.")
            return None

        logger.success(f"User found: {response.data[0]}")
        return User(**response.data[0])
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        raise Exception(f"Error fetching user: {e}") from e
