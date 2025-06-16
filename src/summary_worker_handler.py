import json
import asyncio

from core.logger import L
from services.email_summary_service import generate_daily_email_summary


def lambda_handler(event, context):
    request_id = context.aws_request_id if context else "local"
    logger = L(request_id)

    logger.info("Starting execution of the worker function.")

    return asyncio.run(main_logic(event, context, logger=logger))


async def main_logic(event, context, *, logger):
    logger.info(f"Received event: {json.dumps(event)}")
    logger.info("Processing SQS event records...")

    for record in event.get("Records", []):
        try:
            message_body = json.loads(record.get("body", "{}"))
            mail_account_id = message_body.get("mail_account_id")

            if not mail_account_id:
                logger.warning(
                    f"SQS message does not contain 'mail_account_id': {record.get('body')}"
                )
                continue

            await process_single_account(mail_account_id, logger=logger)

        except json.JSONDecodeError as e:
            logger.exception(
                f"Failed to decode JSON from SQS message body: {record.get('body')}. Error: {e}"
            )
        except Exception as e:
            logger.exception(
                f"An error occurred while processing SQS message: {record.get('body')}. Error: {e}"
            )
            raise e

    return {"statusCode": 200, "body": json.dumps({"status": "ok"})}


async def process_single_account(mail_account_id, *, logger):
    await generate_daily_email_summary(mail_account_id, logger=logger)
