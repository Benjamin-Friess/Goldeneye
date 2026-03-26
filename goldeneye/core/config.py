"""Application configuration loaded from environment / .env file."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Alpaca
    alpaca_api_key: str = Field(default="", alias="ALPACA_API_KEY")
    alpaca_secret_key: str = Field(default="", alias="ALPACA_SECRET_KEY")
    alpaca_paper: bool = Field(default=True, alias="ALPACA_PAPER")
    alpaca_feed: str = Field(default="iex", alias="ALPACA_FEED")  # "iex" (free) or "sip" (paid)

    # App
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    db_url: str = Field(default="sqlite+aiosqlite:///goldeneye.db", alias="DB_URL")


settings = Settings()
