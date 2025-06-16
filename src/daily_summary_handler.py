import json
import os
import boto3
import asyncio

from core.logger import L
from core.supabase_client import create_supabase_client

SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL")
sqs = boto3.client("sqs")


async def get_active_mail_accounts_from_db(*, logger):
    logger.info("Searching for active mail accounts in the database...")
    supabase = await create_supabase_client()
    try:
        response = (
            await supabase.table("mail_accounts")
            .select("id")
            .eq("is_active", True)
            .execute()
        )
        active_mail_accounts = response.data

        logger.success(f"{len(active_mail_accounts)} mail active accounts found.")
        return active_mail_accounts
    except Exception as e:
        logger.exception(f"Error fetching active mail accounts: {e}")
        raise e


async def main_logic(event, context, *, logger):
    if not SQS_QUEUE_URL:
        raise EnvironmentError(
            "SQS_QUEUE_URL environment variable is not set. Please configure it."
        )

    active_mail_accounts = await get_active_mail_accounts_from_db(logger=logger)

    if not active_mail_accounts:
        logger.info("No active mail accounts found to process.")
        return {
            "statusCode": 200,
            "body": json.dumps(
                {"message": "No active mail accounts found to process."}
            ),
        }

    logger.info(f"Found {len(active_mail_accounts)} active mail accounts to process.")
    success_count = 0
    failure_count = 0

    for mail_account in active_mail_accounts:
        mail_account_id = mail_account.get("id")
        if not mail_account_id:
            logger.info(
                f"Skipping mail account with missing id: {mail_account}"
            )
            failure_count += 1
            continue
        try:
            message_body = json.dumps({"mail_account_id": mail_account_id})
            sqs.send_message(QueueUrl=SQS_QUEUE_URL, MessageBody=message_body)
            logger.success(
                f"Message sent to SQS for mail_account_id: {mail_account_id}"
            )
            success_count += 1
        except Exception as e:
            logger.exception(
                f"Failed to send message for mail_account_id {mail_account_id}: {e}"
            )
            failure_count += 1

    logger.success(
        f"Process completed: {success_count} successful, {failure_count} failed."
    )
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "Process completed.",
                "total_accounts": len(active_mail_accounts),
                "success_count": success_count,
                "failure_count": failure_count,
            }
        ),
    }


def lambda_handler(event, context):
    request_id = context.aws_request_id if context else "local"
    logger = L(request_id)

    logger.info("Iniciando execução do dispatcher.")

    return asyncio.run(main_logic(event, context, logger=logger))
