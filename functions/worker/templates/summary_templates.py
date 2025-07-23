from typing import Awaitable, Callable, List

from ..langchain.documents.email_document import EmailDocument

SummaryTemplateFn = Callable[[List[EmailDocument], dict], Awaitable[str]]

TEMPLATE_REGISTRY: dict[str, SummaryTemplateFn] = {}


def register_template(name: str, fn: SummaryTemplateFn):
    TEMPLATE_REGISTRY[name] = fn


def get_template(name: str) -> SummaryTemplateFn:
    if name not in TEMPLATE_REGISTRY:
        raise ValueError(f"Template '{name}' not found.")
    return TEMPLATE_REGISTRY[name]
