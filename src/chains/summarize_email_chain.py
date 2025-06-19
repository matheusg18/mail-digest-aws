from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from core.settings import settings
from schemas.email_summary_schema import EmailSummarySchema

llm = ChatOpenAI(
    model="gpt-4.1-nano",
    max_completion_tokens=300,
    api_key=SecretStr(settings.OPENAI_API_KEY),
)

system_prompt = SystemMessage(
    "You are an expert email summarizer. "
    "Your task is to analyze the content of the email and provide "
    "a structured summary."
)
human_prompt_template = HumanMessagePromptTemplate.from_template(
    "Summarize the following email content:\n\n"
    "Subject: {subject}\n"
    "From: {sender}\n"
    "Date: {date}\n\n"
    "{body}\n\n"
    "Return a JSON object and use the same language as the email content."
)

email_summary_prompt_template = ChatPromptTemplate.from_messages(
    [
        system_prompt,
        human_prompt_template,
    ]
)

structured_llm = llm.with_structured_output(EmailSummarySchema)

chain = email_summary_prompt_template | structured_llm
