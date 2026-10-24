from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://ortxcore:ortxcore@localhost:5432/ortxcore"
    admin_api_key: str = "change-me-development-only"
    fraud_deny_amount_minor: int = 1_000_000
    fraud_review_amount_minor: int = 250_000
    fraudshield_url: str | None = None
    fraudshield_timeout_seconds: float = 1.0
    # A failed risk call must never turn into an approval. REVIEW is the
    # conservative lab default; DENY can be selected by an operator.
    fraudshield_unavailable_policy: str = "REVIEW"
    nats_url: str = "nats://localhost:4222"
    audit_database_url: str = "postgresql+psycopg://ortxcore:ortxcore@localhost:5432/ortxcore_audit"


settings = Settings()
