import uuid
from http import HTTPStatus

from loguru import logger

from shared.core.supabase_client import create_supabase_client
from shared.domain.mail_account import MailAccount
from shared.exceptions.sumio_exception import SumioException
from shared.utils.security.crypto import decrypt_token


async def list_user_mail_accounts(user_id: uuid.UUID) -> list[MailAccount]:
    supabase = await create_supabase_client()

    try:
        logger.info(f"Fetching mail accounts for user: {user_id}")
        response = await supabase.table("mail_accounts").select("*").eq("user_id", str(user_id)).execute()

        if not response.data:
            logger.warning(f"No mail accounts found for user {user_id}.")
            return []

        logger.success(f"Found {len(response.data)} mail accounts for user {user_id}.")
        return [MailAccount(**account) for account in response.data]
    except Exception as e:
        logger.error(f"Error fetching mail accounts: {e}")
        raise SumioException(
            "Error fetching user mail accounts",
            code=HTTPStatus.INTERNAL_SERVER_ERROR,
            details={"user_id": user_id, "error": e},
        ) from e


async def get_mail_account(mail_account_id: uuid.UUID) -> MailAccount | None:
    supabase = await create_supabase_client()

    try:
        logger.info(f"Fetching mail account with ID: {mail_account_id}")
        response = await supabase.table("mail_accounts").select("*").eq("id", str(mail_account_id)).execute()

        if not response.data:
            logger.warning(f"Mail account with ID {mail_account_id} not found.")
            return None

        logger.success(f"Mail account found: {response.data[0]}")

        mail_account = MailAccount(**response.data[0])
        if mail_account.credentials:
            if mail_account.credentials.get("refresh_token"):
                decrypted_token = decrypt_token(mail_account.credentials["refresh_token"])
                mail_account.credentials["refresh_token"] = decrypted_token

        return mail_account
    except Exception as e:
        logger.error(f"Error fetching mail account: {e}")
        raise SumioException(
            "Error fetching mail account",
            code=HTTPStatus.INTERNAL_SERVER_ERROR,
            details={"mail_account_id": mail_account_id, "error": e},
        ) from e
