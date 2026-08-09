from pydantic_settings import BaseSettings, SettingsConfigDict
import warnings

class Settings(BaseSettings):
    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite+aiosqlite:///data/hinata.db"
    JWT_SECRET: str = ""
    JWT_ACCESS_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_EXPIRE_DAYS: int = 30
    WEB_ORIGINS: str = "http://localhost:2027,http://localhost:8000,http://127.0.0.1:2027,http://127.0.0.1:8000"
    BOT_TOKEN: str = ""
    GROQ_API_KEY: str = ""
    AI_PROVIDER: str = "groq"
    ENABLE_AI_FALLBACK: bool = True
    OPENCODE_ZEN_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    LOG_LEVEL: str = "INFO"
    OWNER_TELEGRAM_ID: int = 0

    model_config = SettingsConfigDict(env_file="/root/Hinata/.env", env_file_encoding="utf-8", extra="ignore")

    def model_post_init(self, __context):
        if self.APP_ENV == "production" and not self.JWT_SECRET:
            warnings.warn("JWT_SECRET is not set in production!")

        if self.DATABASE_URL.startswith("sqlite") and "://" in self.DATABASE_URL:
            # resolve to absolute path if needed
            pass

settings = Settings()
