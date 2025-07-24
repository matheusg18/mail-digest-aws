from typing import Dict

from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from shared.core.settings import settings

from ..schemas.email_summary_schema import EmailSummarySchema

_llm = ChatOpenAI(
    model="gpt-4.1-nano",
    max_completion_tokens=300,
    api_key=SecretStr(settings.OPENAI_API_KEY),
    temperature=0.1,
)


_system_prompt = SystemMessage(
    "You are an expert email summarizer. "
    "Your task is to read the content of an email and generate a concise summary in natural language, "
    "no more than one sentence, in pt-BR."
)
_human_prompt_template = HumanMessagePromptTemplate.from_template(
    "Subject: {subject}\nFrom: {sender}\nDate: {date}\n\n{body}\n\nSummary:"
)

_email_summary_prompt_template = ChatPromptTemplate.from_messages([
    _system_prompt,
    _human_prompt_template,
])

_summary_generation_chain = _email_summary_prompt_template | _llm.with_structured_output(EmailSummarySchema)


def _formatter(input_dict: Dict) -> Dict:
    return {
        "subject": input_dict["original_input"]["subject"],
        "sender": input_dict["original_input"]["sender"],
        "receiver": input_dict["original_input"]["receiver"],
        "date": input_dict["original_input"]["date"],
        "summary": input_dict["summary_message"].short_summary,
        "emoji": input_dict["summary_message"].emoji,
    }


chain = {
    "summary_message": _summary_generation_chain,
    "original_input": RunnablePassthrough(),
} | RunnableLambda(_formatter)
