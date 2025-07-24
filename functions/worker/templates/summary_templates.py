from typing import Awaitable, Callable, Dict, List

from ..langchain.documents.email_document import EmailDocument

SummaryTemplateFn = Callable[[Dict[str, List[EmailDocument]], Dict], Awaitable[str]]

TEMPLATE_REGISTRY: Dict[str, SummaryTemplateFn] = {}


def register_template(name: str, fn: SummaryTemplateFn):
    TEMPLATE_REGISTRY[name] = fn


def get_template(name: str) -> SummaryTemplateFn:
    if name not in TEMPLATE_REGISTRY:
        raise ValueError(f"Template '{name}' not found.")
    return TEMPLATE_REGISTRY[name]
