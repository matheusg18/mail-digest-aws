from datetime import datetime
from typing import Dict, List

from loguru import logger

from shared.utils import time_utils

from ...langchain.documents.email_document import EmailDocument
from ..summary_templates import register_template
from .chains import generate_aggregated_summary, summarize_email


async def classic_template(emails: List[EmailDocument], context: Dict) -> str:
    timezone = context["timezone"]
    now = datetime.now(timezone)

    email_summaries = await _batch_summarize_emails(emails, context)
    aggregated_summary = await generate_aggregated_summary.chain.ainvoke(
        {"today_date": time_utils.format_to_iso_date(now), "structured_emails": email_summaries},
        {
            "run_name": "[classic] generate_aggregated_summary",
        },
    )

    logger.success("Generated aggregated summary successfully.")
    return aggregated_summary.text()


async def _batch_summarize_emails(emails: List[EmailDocument], context: Dict) -> List[Dict]:
    logger.info(f"Summarizing {len(emails)} emails in batch.")

    timezone = context["timezone"]
    input_data_list = [
        {
            "subject": email.metadata.subject,
            "sender": email.metadata.sender,
            "receiver": email.metadata.receiver,
            "date": time_utils.format_to_iso_datetime(email.metadata.date.astimezone(timezone)),
            "body": email.page_content,
        }
        for email in emails
    ]
    result = await summarize_email.chain.abatch(input_data_list, {"run_name": "[classic] summarize_email"})

    logger.success(f"Summarized {len(result)} emails successfully.")
    return result


register_template("classic", classic_template)
