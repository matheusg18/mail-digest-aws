from typing import Any, Dict, List

from loguru import logger

from ...langchain.documents.email_document import EmailDocument
from ..summary_templates import register_template
from .chains import generate_aggregated_summary, summarize_email


async def classic_template(emails: List[EmailDocument], context: Dict[str, Any]) -> str:
    now = context["now"]

    email_summaries = await _batch_summarize_emails(emails)
    aggregated_summary = await generate_aggregated_summary.chain.ainvoke(
        {"today_date": now.strftime("%m/%d/%Y"), "structured_emails": email_summaries},
        {
            "run_name": "[classic] generate_aggregated_summary",
        },
    )

    logger.success("Generated aggregated summary successfully.")
    return aggregated_summary.text()


async def _batch_summarize_emails(documents: List[EmailDocument]) -> List[Dict[str, Any]]:
    logger.info(f"Summarizing {len(documents)} emails in batch.")

    input_data_list = [
        {
            "subject": email.metadata.subject,
            "sender": email.metadata.sender,
            "receiver": email.metadata.receiver,
            "date": email.metadata.date,
            "body": email.page_content,
        }
        for email in documents
    ]
    result = await summarize_email.chain.abatch(input_data_list, {"run_name": "[classic] summarize_email"})

    logger.success(f"Summarized {len(result)} emails successfully.")
    return result


register_template("classic", classic_template)
