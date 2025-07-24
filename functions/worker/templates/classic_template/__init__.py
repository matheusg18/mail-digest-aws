from datetime import datetime
from typing import Dict, List
from zoneinfo import ZoneInfo

from loguru import logger

from shared.utils import time_utils

from ...langchain.documents.email_document import EmailDocument
from ..summary_templates import register_template
from .chains import summarize_email


async def classic_template(emails_by_email_account: Dict[str, List[EmailDocument]], context: Dict) -> str:
    email_summaries_by_email_account = await _summarize_emails_by_email_account(emails_by_email_account, context)
    aggregated_summary = _generate_aggregated_summary(email_summaries_by_email_account, context)
    return aggregated_summary


async def _summarize_emails_by_email_account(
    emails_by_email_account: Dict[str, List[EmailDocument]], context: Dict
) -> Dict[str, List[Dict]]:
    logger.info("Summarizing emails by mail account")

    summaries_by_email_account = {}
    for email_account, emails in emails_by_email_account.items():
        logger.info(f"Summarizing emails for account: {email_account}")
        summaries = await _batch_summarize_emails(emails, context)
        summaries_by_email_account[email_account] = summaries
        logger.info(f"Completed summarizing emails for account: {email_account}")

    return summaries_by_email_account


async def _batch_summarize_emails(emails: List[EmailDocument], context: Dict) -> List[Dict]:
    logger.info(f"Summarizing {len(emails)} emails in batch")

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

    logger.info(f"Summarized {len(result)} emails successfully")
    return result


def _generate_aggregated_summary(email_summaries_by_email_account: Dict[str, List[Dict]], context: Dict) -> str:
    logger.info("Generating aggregated summary")
    timezone = context["timezone"]

    summary_lines = []
    summary_lines.append("**🧾 Resumo das últimas 24h**\n")
    for email_account, email_summaries in email_summaries_by_email_account.items():
        summary_lines.append(f"**📧 Conta:** {email_account}\n")
        for email_summary in email_summaries:
            summary_lines.append(_build_email_summary_line(email_summary, timezone))
        summary_lines.append("\n")

    logger.info("Aggregated summary generated successfully")
    return "\n".join(summary_lines).strip()


def _build_email_summary_line(email_summary: Dict, timezone: ZoneInfo) -> str:
    email_date = time_utils.from_iso_datetime(email_summary["date"]).astimezone(timezone)
    now = datetime.now(timezone)
    relative_time = _format_relative_time(email_date, now)
    sender = (
        email_summary["sender"].split("<")[0].strip() if "<" in email_summary["sender"] else email_summary["sender"]
    )

    return f"{relative_time}\n**{email_summary['emoji']} {sender} —** {email_summary['summary']}\n"


def _format_relative_time(dt: datetime, now: datetime) -> str:
    if dt.date() == now.date():
        return f"**🕘 Hoje às {dt.strftime('%H:%M')}**"
    elif (now.date() - dt.date()).days == 1:
        return f"**🕘 Ontem às {dt.strftime('%H:%M')}**"
    else:
        return f"**🕘 {dt.strftime('%d/%m %H:%M')}**"


register_template("classic", classic_template)
