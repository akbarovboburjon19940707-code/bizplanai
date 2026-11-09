"""Ilova sozlamalari. Barcha qiymatlar muhit o'zgaruvchilaridan (Render Environment) o'qiladi."""
from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_env: Literal["development", "production", "test"] = "development"
    app_name: str = "BizplanAI API"
    secret_key: str = "dev-only-secret-key-change-me-0000000000"

    database_url: str = "sqlite+aiosqlite:///./dev.db"
    db_pool_size: int = 10
    db_max_overflow: int = 5
    redis_url: str | None = None  # None -> faqat dev: xotiradagi fakeredis

    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    frontend_url: str = "http://localhost:3000"
    public_api_url: str = "http://localhost:8000"
    cookie_domain: str | None = None  # prod: .bizplanai.uz
    cookie_secure: bool = False

    access_token_minutes: int = 15
    refresh_token_days: int = 30

    job_mode: Literal["queue", "inline"] = "inline"

    storage_backend: Literal["local", "r2"] = "local"
    local_storage_dir: str = "./storage"
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket: str = ""
    catalog_file_prefix: str = "catalog/pdfs/"
    download_url_ttl_seconds: int = 600
    max_receipt_bytes: int = 10 * 1024 * 1024
    max_plan_image_bytes: int = 5 * 1024 * 1024
    # Muqova rasmini avtomatik topish (Pexels: bepul, tijoriy foydalanishga ruxsat). Bo'sh bo'lsa o'chiq.
    pexels_api_key: str = ""

    telegram_bot_token: str = ""
    telegram_bot_name: str = "uzbiznesssbot"
    telegram_webhook_secret: str = ""
    telegram_admin_chat_id: str = ""
    telegram_initdata_max_age: int = 86400

    click_service_id: str = ""
    click_merchant_id: str = ""
    click_merchant_user_id: str = ""
    click_secret_key: str = ""
    payme_merchant_id: str = ""
    payme_secret_key: str = ""
    payme_checkout_url: str = "https://checkout.paycom.uz"
    manual_card_number: str = ""
    manual_card_holder: str = ""
    plan_credit_price_som: int = 50000
    pending_payment_ttl_hours: int = 24

    ai_enabled: bool = True
    ai_daily_token_budget: int = 2_000_000
    ai_timeout_seconds: float = 60.0
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5"

    sentry_dsn: str = ""
    log_level: str = "INFO"

    @field_validator("database_url")
    @classmethod
    def _normalize_db(cls, v: str) -> str:
        # Render "postgres://..." beradi; async drayverga moslaymiz
        if v.startswith("postgres://"):
            v = "postgresql+asyncpg://" + v[len("postgres://"):]
        elif v.startswith("postgresql://"):
            v = "postgresql+asyncpg://" + v[len("postgresql://"):]
        return v

    @model_validator(mode="after")
    def _production_guard(self):
        if self.app_env == "production":
            problems = []
            if len(self.secret_key) < 32 or self.secret_key.startswith("dev-only"):
                problems.append("SECRET_KEY kamida 32 belgili tasodifiy qiymat bo'lishi kerak")
            if self.database_url.startswith("sqlite"):
                problems.append("DATABASE_URL Postgres bo'lishi kerak")
            if not self.redis_url:
                problems.append("REDIS_URL majburiy")
            if self.job_mode != "queue":
                problems.append("JOB_MODE=queue bo'lishi kerak")
            if self.storage_backend != "r2":
                problems.append("STORAGE_BACKEND=r2 bo'lishi kerak")
            if not self.cookie_secure:
                problems.append("COOKIE_SECURE=true bo'lishi kerak")
            if problems:
                raise ValueError("Production sozlamalari xato: " + "; ".join(problems))
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
