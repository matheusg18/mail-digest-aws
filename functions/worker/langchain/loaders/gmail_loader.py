import base64
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from bs4 import BeautifulSoup
from langchain.document_loaders.base import BaseLoader

from shared.services import gmail_service

from ..documents import EmailDocument, EmailMetadata


class GmailLoader(BaseLoader):
    """Custom LangChain loader for Gmail emails"""

    def __init__(self, access_token: str, days: int = 1, query: str = ""):
        self.days = days
        self.query = query
        self.access_token = access_token

    async def aload(self) -> List[EmailDocument]:
        return await self._load_recent_emails(days=self.days, query=self.query)

    async def _load_recent_emails(self, days: int = 1, query: str = "") -> List[EmailDocument]:
        """Load emails from the last N days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        after_date = int(start_date.timestamp())
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
                    metadata = EmailMetadata(
                        message_id=email_data["id"],
                        subject=email_data["subject"],
                        sender=email_data["sender"],
                        receiver=email_data["receiver"],
                        date=email_data["date"],
                        thread_id=email_data["thread_id"],
                        labels=email_data["labels"],
                    )
                    doc = EmailDocument(
                        page_content=email_data["body"].strip(),
                        metadata=metadata,
                    )
                    documents.append(doc)

            return documents

        except Exception as e:
            print(f"Error loading emails: {e}")
            return []

    async def _get_message_content(self, message_id: str) -> Dict[str, Any] | None:
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
            receiver = next(
                (h["value"] for h in headers if h["name"] == "To"),
                "Unknown Receiver",
            )
            date = self._convert_date(
                next(
                    (h["value"] for h in headers if h["name"] == "Date"),
                    "Unknown Date",
                )
            )

            # Extract body
            body = self._extract_body(message["payload"], message_id)

            return {
                "id": message_id,
                "subject": subject,
                "sender": sender,
                "receiver": receiver,
                "date": date,
                "body": body,
                "thread_id": message.get("threadId", ""),
                "labels": message.get("labelIds", []),
            }
        except Exception as e:
            print(f"Error getting message {message_id}: {e}")
            return None

    @staticmethod
    def _convert_date(date_str: str) -> datetime:
        cleaned_str = date_str.split(" (", 1)[0]
        dt = datetime.strptime(cleaned_str, "%a, %d %b %Y %H:%M:%S %z").astimezone(timezone.utc)
        return dt

    def _extract_body(self, payload, message_id: str) -> str:
        if "parts" in payload:
            return self._walk_parts(payload["parts"], message_id)
        elif payload["body"].get("data"):
            print("Extracting body from single part", message_id)
            if payload["mimeType"] == "text/plain":
                print("Extracting text/plain part", message_id)
                data = payload["body"]["data"]
                body = base64.urlsafe_b64decode(data).decode("utf-8")
                body = self._clean_links(body)
                lines = body.splitlines()
                cleaned_lines = [line.strip() for line in lines if line.strip()]
                return "\n".join(cleaned_lines)
            elif payload["mimeType"] == "text/html":
                print("Extracting text/html part", message_id)
                data = payload["body"]["data"]
                body = base64.urlsafe_b64decode(data).decode("utf-8")
                soup = BeautifulSoup(body, "html.parser")
                text = soup.get_text()
                text = self._clean_links(text)
                lines = text.splitlines()
                cleaned_lines = [line.strip() for line in lines if line.strip()]
                return "\n".join(cleaned_lines)
        return ""

    @staticmethod
    def _clean_links(text_body: str) -> str:
        """
        Replace all URLs in a text with "external_link".
        """
        url_pattern = r"(?:(?:https?|ftp):\/\/|www\.)[^\s>]+"

        return re.sub(url_pattern, "external_link", text_body)

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
                body = self._clean_links(body)
                lines = body.splitlines()
                cleaned_lines = [line.strip() for line in lines if line.strip()]
                return "\n".join(cleaned_lines)
            elif part["mimeType"] == "text/html":
                print("Extracting text/html part", message_id)
                data = part["body"]["data"]
                body = base64.urlsafe_b64decode(data).decode("utf-8")
                soup = BeautifulSoup(body, "html.parser")
                text = soup.get_text()
                text = self._clean_links(text)
                lines = text.splitlines()
                cleaned_lines = [line.strip() for line in lines if line.strip()]
                return "\n".join(cleaned_lines)
        return ""
