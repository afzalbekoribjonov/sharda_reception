from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    BOT_TOKEN: str
    MONGO_URI: str
    MONGO_DB: str = "suuz_bot"
    SUPER_ADMIN_TG_ID: int
    WEBAPP_URL: str | None = None

    TZ: str = "Asia/Tashkent"
    INTRO_PHOTO_FILE_ID: str | None = None


settings = Settings()