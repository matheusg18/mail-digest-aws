import uuid

from loguru import logger

from shared.core.supabase_client import create_supabase_client
from shared.domain.mail_account import MailAccount
from shared.utils.security.crypto import decrypt_token


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
        raise Exception(f"Error fetching mail account: {e}") from e
