from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from core.settings import settings

llm = ChatOpenAI(
    model="gpt-4.1-mini",
    max_completion_tokens=3000,
    api_key=SecretStr(settings.OPENAI_API_KEY),
)

system_prompt = SystemMessage(
    "You are an expert executive summary generator. "
    "Your task is to create a concise executive summary based "
    "on the provided email summaries."
)
human_prompt_template = HumanMessagePromptTemplate.from_template(
    "Generate an executive summary based on the following email summaries:\n\n"
    "{summaries}\n\n"
    "The summary should include urgent items, "
    "upcoming events, pending actions, and important decisions."
    "Return the summary following the format below, but in pt-BR:\n\n"
    "📋 EXECUTIVE SUMMARY (last 24h)\n\n"
    "🚨 URGENT ITEMS:\n"
    "- [Summary of high priority emails with deadlines]\n\n"
    "📅 UPCOMING EVENTS:\n"
    "- [Meetings, deadlines, etc.]\n\n"
    "⚡ PENDING ACTIONS:\n"
    "- [What needs to be done, by whom, when]\n\n"
    "💼 IMPORTANT DECISIONS:\n"
    "- [Approvals, changes in direction, etc.]"
)

aggregated_summary_prompt_template = ChatPromptTemplate.from_messages(
    [
        system_prompt,
        human_prompt_template,
    ]
)

chain = aggregated_summary_prompt_template | llm
