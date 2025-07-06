import base64
from datetime import datetime, timedelta
from typing import Any, Dict, List

from bs4 import BeautifulSoup
from langchain.document_loaders.base import BaseLoader
from langchain.schema import Document

from services import gmail_service


class GmailLoader(BaseLoader):
    """Custom LangChain loader for Gmail emails"""

    def __init__(self, access_token: str, days: int = 1, query: str = ""):
        self.days = days
        self.query = query
        self.access_token = access_token

    async def aload(self) -> List[Document]:
        return await self._load_recent_emails(days=self.days, query=self.query)

    async def _load_recent_emails(
        self, days: int = 1, query: str = ""
    ) -> List[Document]:
        """Load emails from the last N days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        after_date = start_date.strftime("%Y/%m/%d")
        query_with_date = f"after:{after_date} {query}".strip()

        try:
            messages = await gmail_service.list_messages(
                user_id="me",
                access_token=self.access_token,
                query=query_with_date,
            )
            documents = []

            for message in messages:
                email_data = await self._get_message_content(message["id"])
                if email_data:
                    content = (
                        f"Subject: {email_data['subject']}\n"
                        + f"From: {email_data['sender']}\n"
                        + f"Date: {email_data['date']}\n\n"
                        + email_data["body"].strip()
                    )

                    doc = Document(
                        page_content=content,
                        metadata={
                            "message_id": email_data["id"],
                            "subject": email_data["subject"],
                            "sender": email_data["sender"],
                            "date": email_data["date"],
                            "thread_id": email_data["thread_id"],
                            "labels": email_data["labels"],
                        },
                    )
                    documents.append(doc)

            return documents

        except Exception as e:
            print(f"Error loading emails: {e}")
            return []

    async def _get_message_content(
        self, message_id: str
    ) -> Dict[str, Any] | None:
        """Get full message content including body"""
        try:
            message = await gmail_service.get_message(
                user_id="me",
                access_token=self.access_token,
                message_id=message_id,
            )

            # Extract headers
            headers = message["payload"].get("headers", [])
            subject = next(
                (h["value"] for h in headers if h["name"] == "Subject"),
                "No Subject",
            )
            sender = next(
                (h["value"] for h in headers if h["name"] == "From"),
                "Unknown Sender",
            )
            date = next(
                (h["value"] for h in headers if h["name"] == "Date"),
                "Unknown Date",
            )

            # Extract body
            body = self._extract_body(message["payload"], message_id)

            return {
                "id": message_id,
                "subject": subject,
                "sender": sender,
                "date": date,
                "body": body,
                "thread_id": message.get("threadId", ""),
                "labels": message.get("labelIds", []),
            }
        except Exception as e:
            print(f"Error getting message {message_id}: {e}")
            return None

    def _extract_body(self, payload, message_id: str) -> str:
        if "parts" in payload:
            return self._walk_parts(payload["parts"], message_id)
        elif payload["body"].get("data"):
            print("Extracting body from single part", message_id)
            if payload["mimeType"] == "text/plain":
                print("Extracting text/plain part", message_id)
                data = payload["body"]["data"]
                body = base64.urlsafe_b64decode(data).decode("utf-8")
                lines = body.splitlines()
                cleaned_lines = [
                    line.strip() for line in lines if line.strip()
                ]
                return "\n".join(cleaned_lines)
            elif payload["mimeType"] == "text/html":
                print("Extracting text/html part", message_id)
                data = payload["body"]["data"]
                body = base64.urlsafe_b64decode(data).decode("utf-8")
                soup = BeautifulSoup(body, "html.parser")
                text = soup.get_text()
                lines = text.splitlines()
                cleaned_lines = [
                    line.strip() for line in lines if line.strip()
                ]
                return "\n".join(cleaned_lines)
        return ""

    def _walk_parts(self, parts: List[Dict[str, Any]], message_id: str) -> str:
        for part in parts:
            if part.get("parts"):
                result = self._walk_parts(part["parts"], message_id)
                if result:
                    return result
            elif part["mimeType"] == "text/plain":
                print("Extracting text/plain part", message_id)
                data = part["body"]["data"]
                body = base64.urlsafe_b64decode(data).decode("utf-8")
                lines = body.splitlines()
                cleaned_lines = [
                    line.strip() for line in lines if line.strip()
                ]
                return "\n".join(cleaned_lines)
            elif part["mimeType"] == "text/html":
                print("Extracting text/html part", message_id)
                data = part["body"]["data"]
                body = base64.urlsafe_b64decode(data).decode("utf-8")
                soup = BeautifulSoup(body, "html.parser")
                text = soup.get_text()
                lines = text.splitlines()
                cleaned_lines = [
                    line.strip() for line in lines if line.strip()
                ]
                return "\n".join(cleaned_lines)
        return ""
