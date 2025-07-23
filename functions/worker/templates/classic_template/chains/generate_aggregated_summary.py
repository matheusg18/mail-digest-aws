from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from shared.core.settings import settings

_llm = ChatOpenAI(
    model="gpt-4.1-mini",
    max_completion_tokens=5000,
    api_key=SecretStr(settings.OPENAI_API_KEY),
    temperature=0.1,
)


_system_prompt = SystemMessage(
    "You are a daily email summary generator. "
    "Your task is to group emails by account, sort them from newest to oldest, and display a short summary "
    "for each email, along with the sender and relative date."
)
_human_prompt_template = HumanMessagePromptTemplate.from_template(
    "Today is {today_date}.\n"
    "Here are the emails received in the last 24 hours, with pre-processed data:\n\n"
    "{structured_emails}\n\n"
    "Generate a summary in the following format, in pt-BR:\n\n"
    "🧾 RESUMO DAS ÚLTIMAS 24H\n\n"
    "🔹 Conta: example@email.com\n"
    '- [ontem às 08:55] Amazon — "Sua entrega está a caminho e deve chegar amanhã."\n'
    '- [hoje às 08:40] Nubank — "Sua fatura fechou em R$ 1.240, vence dia 10."\n\n'
    "🔹 Conta: trabalho@empresa.com\n"
    '- [hoje às 08:20] GitHub — "Seu pull request foi aprovado e já está no branch principal."\n'
    '- [hoje às 07:50] HR Team — "Reunião de alinhamento marcada para hoje às 11h."\n\n'
    "Rules:\n"
    "- Group by email account\n"
    "- Sort from newest to oldest within each account\n"
    "- Use 'hoje', 'ontem', 'anteontem' when possible\n"
    '- For each line, show: [relative date] Sender — "Short summary"\n'
    "- Do not invent content. Use only the provided short summary."
)

_aggregated_summary_prompt_template = ChatPromptTemplate.from_messages([
    _system_prompt,
    _human_prompt_template,
])

chain = _aggregated_summary_prompt_template | _llm
