import json
import uuid
from typing import List

from langchain.schema import Document

from chains import (
    generate_aggregated_summary,
    summarize_email_chain,
)
from loaders.gmail_loader import GmailLoader
from services import (
    google_auth_service,
    mail_account_service,
    telegram_service,
)
from services.delivery_channel_service import get_active_delivery_channels


async def generate_daily_email_summary(mail_account_id: uuid.UUID, *, logger) -> None:
    mail_account = await mail_account_service.get_mail_account(
        mail_account_id, logger=logger
    )
    if not mail_account:
        raise ValueError(f"Mail account with ID {mail_account_id} not found.")

    if not mail_account.credentials:
        raise ValueError(
            f"Mail account with ID {mail_account_id} does not have credentials."
        )

    gmail_loader = GmailLoader(
        await google_auth_service.get_access_token(
            mail_account.credentials, logger=logger
        ),
        days=1,
    )
    documents = await gmail_loader.aload()

    if not documents:
        logger.warning("No emails found for today.")
        raise ValueError("No emails found for today. Please check your Gmail settings.")

    logger.info(f"Found {len(documents)} emails to summarize.")
    summaries = await _batch_summarize_emails(documents, logger=logger)

    aggregated_summary = await generate_aggregated_summary.chain.ainvoke(
        {
            "summaries": json.dumps(
                [summary.model_dump() for summary in summaries], indent=2
            )
        },
        {
            "run_name": "executive_summary",
        },
    )

    active_delivery_channels = await get_active_delivery_channels(
        mail_account.user_id, logger=logger
    )
    telegram_delivery_channel = active_delivery_channels[0]

    if not telegram_delivery_channel:
        raise ValueError(
            "No active Telegram delivery channel found for the user. Please add a delivery channel."
        )
    logger.info(
        f"Sending aggregated summary to Telegram channel: {telegram_delivery_channel.address}"
    )
    await telegram_service.send_message(
        int(telegram_delivery_channel.address),
        str(aggregated_summary.content),
    )


async def _batch_summarize_emails(
    documents: List[Document], *, logger
) -> list[Document]:
    logger.info(f"Summarizing {len(documents)} emails in batch.")
    input_data_list = [
        {
            "subject": email.metadata["subject"],
            "sender": email.metadata["sender"],
            "date": email.metadata["date"],
            "body": email.page_content,
        }
        for email in documents
    ]

    return await summarize_email_chain.chain.abatch(
        input_data_list, {"run_name": "generate_summary"}
    )
