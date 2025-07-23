import uuid
from datetime import datetime, timezone
from http import HTTPStatus

from loguru import logger

from shared.domain.user import User
from shared.exceptions.sumio_exception import SumioException
from shared.services import (
    delivery_channel_service,
    google_auth_service,
    telegram_service,
    user_service,
)

from ..langchain.loaders import GmailLoader
from ..templates.summary_templates import get_template


async def generate_daily_email_summary(user_id: uuid.UUID) -> None:
    user = await _get_user_with_mail_accounts(user_id)

    gmail_loader = GmailLoader(
        await google_auth_service.get_access_token(user.mail_accounts[0].credentials),
        days=1,
    )
    emails = await gmail_loader.aload()

    if not emails:
        logger.warning("No emails found for today.")
        raise ValueError("No emails found for today. Please check your Gmail settings.")

    logger.info(f"Found {len(emails)} emails to summarize.")
    template_fn = get_template("classic")
    summary = await template_fn(emails, {"timezone": user.get_timezone()})

    active_delivery_channels = await delivery_channel_service.list_user_delivery_channels(
        user.id,
        is_active=True,
    )
    telegram_delivery_channel = active_delivery_channels[0]

    if not telegram_delivery_channel:
        raise ValueError("No active Telegram delivery channel found for the user. Please add a delivery channel.")
    logger.info(f"Sending aggregated summary to Telegram channel: {telegram_delivery_channel.address}")
    await telegram_service.send_message(
        int(telegram_delivery_channel.address),
        summary,
    )


async def _get_user_with_mail_accounts(user_id: uuid.UUID) -> User:
    user = await user_service.get_user_with_mail_accounts(user_id)
    if not user.mail_accounts or len(user.mail_accounts) == 0:
        raise SumioException(
            "No mail accounts found for user",
            code=HTTPStatus.NOT_FOUND,
            details={"user_id": str(user_id)},
        )

    mail_account = user.mail_accounts[0]
    if not mail_account.credentials:
        raise SumioException(
            "Mail account does not have credentials",
            code=HTTPStatus.BAD_REQUEST,
            details={"mail_account_id": str(mail_account.id)},
        )

    return user
