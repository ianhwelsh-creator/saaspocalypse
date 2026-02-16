"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
    )

    # Mediastack (replaces NewsAPI)
    MEDIASTACK_KEY: str = ""

    # Twitter/X API (optional)
    TWITTER_BEARER_TOKEN: str = ""

    # Anthropic (Claude)
    ANTHROPIC_API_KEY: str = ""

    # Email (Resend)
    RESEND_API_KEY: str = ""

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/saaspocalypse.db"

    # App Config
    NEWS_REFRESH_INTERVAL_MINUTES: int = 15
    STOCK_CACHE_TTL_MINUTES: int = 15


settings = Settings()
