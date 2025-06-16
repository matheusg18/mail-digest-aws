import uuid
from core.supabase_client import create_supabase_client
from domain.mail_account import MailAccount


async def get_mail_account(mail_account_id: uuid.UUID, *, logger) -> MailAccount | None:
    supabase = await create_supabase_client()
    try:
        logger.info(f"Fetching mail account with ID: {mail_account_id}")
        response = (
            await supabase.table("mail_accounts")
            .select("*")
            .eq("id", str(mail_account_id))
            .execute()
        )

        if not response.data:
            logger.warning(f"Mail account with ID {mail_account_id} not found.")
            return None

        logger.success(f"Mail account found: {response.data[0]}")
        return MailAccount(**response.data[0])
    except Exception as e:
        logger.error(f"Error fetching mail account: {e}")
        raise Exception(f"Error fetching mail account: {e}") from e
