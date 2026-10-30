"""Environment-based application configuration."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    jwt_secret: str = Field(default="")
    database_url: str = "postgresql+psycopg://dukaan:dukaan@localhost:5432/dukaan"
    cors_origins: str = "http://localhost:5173"
    cookie_secure: bool = False
    access_token_expire_minutes: int = 60
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    shop_timezone: str = "Asia/Kolkata"
    debug: bool = False
    max_request_bytes: int = 2_500_000
    ai_max_message_chars: int = 4000
    ai_rate_limit_per_minute: int = 10
    gemini_timeout_ms: int = 20_000
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"
    hf_token: str = ""
    hf_model: str = "meta-llama/Llama-3.2-3B-Instruct"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2"
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_mode: str = "test"
    billing_list_amount_paise: int = 49_900
    billing_test_amount_paise: int = 100
    resend_api_key: str = ""
    resend_from_email: str = "Dukaan Assistant <beth.t@example.com>"
    frontend_url: str = "http://localhost:5173"
    cookie_name: str = "access_token"
    csrf_cookie_name: str = "csrf_token"
    csrf_header_name: str = "X-CSRF-Token"
    admin_email: str = ""
    admin_password: str = ""

    @field_validator("jwt_secret")
    @classmethod
    def strip_secret(cls, value: str) -> str:
        return value.strip()

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def require_jwt_secret(self) -> str:
        placeholder_values = {"", "change-me", "replace-with-a-long-random-string", "secret"}
        if self.jwt_secret.lower() in placeholder_values or len(self.jwt_secret) < 32:
            raise RuntimeError(
                "JWT_SECRET is missing or too weak. Set a random string of at least 32 "
                "characters in backend/.env before starting the server."
            )
        return self.jwt_secret


@lru_cache
def get_settings() -> Settings:
    return Settings()
