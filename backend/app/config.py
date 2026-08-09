from pydantic_settings import BaseSettings, SettingsConfigDict
import re
import warnings
from pathlib import Path

# Project root: /root/Hinata (backend/app/config.py -> parents[2])
PROJECT_ROOT = Path(__file__).resolve().parents[2]

_SQLITE_RELATIVE_RE = re.compile(r"^(sqlite(?:\+[a-z]+)?:///)(.*)$")


def _resolve_sqlite_url(url: str) -> str:
    """Resolve a relative SQLite path against the project root so the DB
    file location does not depend on the process working directory."""
    match = _SQLITE_RELATIVE_RE.match(url)
    if not match:
        return url
    scheme, path = match.group(1), match.group(2)
    if not path or path == ":memory:" or Path(path).is_absolute():
        return url
    resolved = PROJECT_ROOT / path
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return f"{scheme}{resolved}"


class Settings(BaseSettings):
    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite+aiosqlite:///data/hinata.db"
    SUPABASE_DB_URL: str = ""
    JWT_SECRET: str = ""
    JWT_ACCESS_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_EXPIRE_DAYS: int = 30
    ADMIN_USERNAME: str = "Admin"
    ADMIN_INITIAL_PASSWORD: str = ""
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

        database_url = self.DATABASE_URL
        if database_url == "sqlite+aiosqlite:///data/hinata.db" and self.SUPABASE_DB_URL:
            database_url = self.SUPABASE_DB_URL
        if database_url.startswith("postgres://"):
            database_url = "postgresql+asyncpg://" + database_url[len("postgres://"):]
        elif database_url.startswith("postgresql://"):
            database_url = "postgresql+asyncpg://" + database_url[len("postgresql://"):]
        self.DATABASE_URL = database_url

        if self.DATABASE_URL.startswith("sqlite") and "://" in self.DATABASE_URL:
            # Anchor relative SQLite paths to the project root so the database
            # file is stable regardless of which directory starts the server.
            self.DATABASE_URL = _resolve_sqlite_url(self.DATABASE_URL)

settings = Settings()
