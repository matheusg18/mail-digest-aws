import json

from langchain.schema import Document
from sqlalchemy.ext.asyncio import AsyncSession

from langchain.chains import (
    generate_aggregated_summary,
    summarize_email_chain,
)
from langchain.loaders.gmail_loader import GmailLoader
from services import google_auth_service, telegram_service


async def generate_daily_email_summary(
    user, session: AsyncSession
) -> None:
    """
    Generate a daily email summary for the user.

    Args:
        user (User): The user for whom to generate the summary.

    Returns:
        str: A summary of the user's emails received today.
    """
    gmail_loader = GmailLoader(
        await google_auth_service.get_access_token(user, session=session),
        days=1,
    )
    documents = await gmail_loader.aload()

    if not documents:
        raise ValueError(
            'No emails found for today. Please check your Gmail settings.'
        )

    summaries = await _batch_summarize_emails(documents)

    aggregated_summary = await generate_aggregated_summary.chain.ainvoke(
        {
            'summaries': json.dumps(
                [summary.model_dump() for summary in summaries], indent=2
            )
        },
        {
            'run_name': 'executive_summary',
        },
    )

    await telegram_service.send_telegram_message(
        user.telegram_chat_id,  # type: ignore
        str(aggregated_summary.content),
    )


async def _batch_summarize_emails(documents: list[Document]):
    """Batch process emails to summarize them."""
    input_data_list = [
        {
            'subject': email.metadata['subject'],
            'sender': email.metadata['sender'],
            'date': email.metadata['date'],
            'body': email.page_content,
        }
        for email in documents
    ]

    return await summarize_email_chain.chain.abatch(
        input_data_list, {'run_name': 'generate_summary'}
    )
