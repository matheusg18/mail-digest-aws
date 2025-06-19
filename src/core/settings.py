import os

import boto3
from pydantic_settings import BaseSettings, SettingsConfigDict


def fetch_secrets_from_ssm() -> dict:
    """
    Busca os segredos do AWS SSM Parameter Store.
    Executado apenas quando o código está rodando dentro de uma Lambda na AWS.
    """
    # A variável AWS_LAMBDA_FUNCTION_NAME é um bom indicador de que estamos na AWS
    if not os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        return {}

    print("Ambiente AWS detectado. Buscando segredos do SSM Parameter Store...")
    ssm_client = boto3.client("ssm")

    # Pega os nomes dos parâmetros a partir das variáveis de ambiente
    param_names_map = {
        "SUPABASE_URL": os.getenv("SUPABASE_URL_SSM_NAME"),
        "SUPABASE_SERVICE_KEY": os.getenv("SUPABASE_SERVICE_KEY_SSM_NAME"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY_SSM_NAME"),
        "GOOGLE_CLIENT_ID": os.getenv("GOOGLE_CLIENT_ID_SSM_NAME"),
        "GOOGLE_CLIENT_SECRET": os.getenv("GOOGLE_CLIENT_SECRET_SSM_NAME"),
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN_SSM_NAME"),
        "LANGSMITH_TRACING": os.getenv("LANGSMITH_TRACING_SSM_NAME"),
        "LANGCHAIN_TRACING_ENDPOINT": os.getenv("LANGCHAIN_TRACING_ENDPOINT_SSM_NAME"),
        "LANGCHAIN_TRACING_API_KEY": os.getenv("LANGCHAIN_TRACING_API_KEY_SSM_NAME"),
        "LANGCHAIN_TRACING_PROJECT": os.getenv("LANGCHAIN_TRACING_PROJECT_SSM_NAME"),
        # Adicione todos os outros segredos aqui...
    }

    # Filtra nomes que não foram definidos para evitar erros
    ssm_param_names_to_fetch = [name for name in param_names_map.values() if name]

    if not ssm_param_names_to_fetch:
        return {}

    response = ssm_client.get_parameters(
        Names=ssm_param_names_to_fetch, WithDecryption=True
    )

    # Mapeia de volta para o nome simples (ex: /maildigest/dev/OPENAI_API_KEY -> OPENAI_API_KEY)
    ssm_name_to_simple_name = {v: k for k, v in param_names_map.items()}

    secrets = {}
    for p in response["Parameters"]:
        simple_name = ssm_name_to_simple_name[p["Name"]]
        secrets[simple_name] = p["Value"]

    print(f"{len(secrets)} segredos carregados com sucesso.")
    return secrets


# Os segredos são buscados uma única vez quando a Lambda inicia (cold start)
_aws_secrets = fetch_secrets_from_ssm()


class Settings(BaseSettings):
    # Para desenvolvimento local, ele lê do .env
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Variáveis não-secretas, lidas do ambiente ou .env
    ENVIRONMENT: str

    # Variáveis secretas.
    # O Pydantic irá preenchê-las a partir do dicionário _aws_secrets.
    # Se não estiver na AWS, _aws_secrets estará vazio, e ele tentará ler do .env.
    SUPABASE_URL: str = _aws_secrets.get("SUPABASE_URL", "")
    SUPABASE_SERVICE_KEY: str = _aws_secrets.get("SUPABASE_SERVICE_KEY", "")
    OPENAI_API_KEY: str = _aws_secrets.get("OPENAI_API_KEY", "")
    TELEGRAM_BOT_TOKEN: str = _aws_secrets.get("TELEGRAM_BOT_TOKEN", "")
    GOOGLE_CLIENT_ID: str = _aws_secrets.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = _aws_secrets.get("GOOGLE_CLIENT_SECRET", "")
    LANGSMITH_TRACING: bool = _aws_secrets.get("LANGSMITH_TRACING", "false").lower() == "true"
    LANGCHAIN_TRACING_ENDPOINT: str = _aws_secrets.get("LANGCHAIN_TRACING_ENDPOINT", "")
    LANGCHAIN_TRACING_API_KEY: str = _aws_secrets.get("LANGCHAIN_TRACING_API_KEY", "")
    LANGCHAIN_TRACING_PROJECT: str = _aws_secrets.get("LANGCHAIN_TRACING_PROJECT", "")
    # Adicione as outras aqui...


settings = Settings()  # type: ignore
