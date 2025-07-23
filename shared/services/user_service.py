import uuid
from http import HTTPStatus
from typing import List

from loguru import logger

from shared.core.supabase_client import create_supabase_client
from shared.domain.user import User
from shared.exceptions.sumio_exception import SumioException


async def get_user(user_id: uuid.UUID) -> User | None:
    supabase = await create_supabase_client()
    try:
        logger.info(f"Fetching user with ID: {user_id}")
        response = await supabase.table("users").select("*").eq("id", str(user_id)).execute()

        if not response.data:
            logger.warning(f"User with ID {user_id} not found.")
            return None

        logger.success(f"User found: {response.data[0]}")
        return User(**response.data[0])
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        raise SumioException(
            "Error fetching user",
            code=HTTPStatus.INTERNAL_SERVER_ERROR,
            details={"user_id": user_id, "error": str(e)},
        ) from e


async def get_users_with_active_mail_digest_at(
    digest_hour: int,
) -> List[User]:
    logger.info(f"Searching for users with active digest at {digest_hour}h...")
    supabase = await create_supabase_client()

    try:
        response = (
            await supabase.table("users")
            .select("*, mail_digest_configs!inner(digest_hour, is_active)")
            .eq("mail_digest_configs.digest_hour", digest_hour)
            .eq("mail_digest_configs.is_active", True)
            .execute()
        )
        users = [User(**user) for user in response.data]

        logger.success(f"{len(users)} users found with active mail digest at {digest_hour}h")
        return users
    except Exception as e:
        logger.error("Error fetching users with active mail digest", extra={"error": e})
        raise SumioException(
            "Error fetching users with active mail digest",
            code=HTTPStatus.INTERNAL_SERVER_ERROR,
            details={"digest_hour": digest_hour, "error": str(e)},
        ) from e


async def get_user_with_mail_accounts(user_id: uuid.UUID) -> User:
    logger.info(f"Fetching user with mail accounts for user ID: {str(user_id)}")
    supabase = await create_supabase_client()

    try:
        response = await supabase.table("users").select("*, mail_accounts(*)").eq("id", str(user_id)).single().execute()
        user = User(**response.data)

        logger.success("Found user with mail accounts")
        return user
    except Exception as e:
        logger.error("Error fetching user with mail accounts", extra={"error": e})
        raise SumioException(
            "Error fetching user with mail accounts",
            code=HTTPStatus.INTERNAL_SERVER_ERROR,
            details={"error": str(e)},
        ) from e
