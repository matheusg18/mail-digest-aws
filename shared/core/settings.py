from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8", extra="ignore"
    )

    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    OPENAI_API_KEY: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_SECRET_TOKEN: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    TOKEN_ENCRYPTION_KEY: str = ""
    LOG_FORMAT: str = "text"


settings = Settings()
