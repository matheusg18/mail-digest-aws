from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from langchain.schema import Document


@dataclass
class EmailMetadata:
    message_id: str = ""
    subject: str = ""
    sender: str = ""
    receiver: str = ""
    date: datetime = datetime.now()
    thread_id: str = ""
    labels: List[str] = field(default_factory=list)


class EmailDocument(Document):
    metadata: EmailMetadata = EmailMetadata()

    def __init__(self, page_content: str, metadata: EmailMetadata):
        super().__init__(page_content=page_content, metadata=metadata)
