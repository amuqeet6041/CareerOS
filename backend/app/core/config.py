from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Fallback used ONLY in development (ENVIRONMENT != "production") when the
# operator has not configured JWT_SECRET. Never rely on this for a real
# deployment: set `ENVIRONMENT=production` in backend/.env so an unset or
# placeholder secret is rejected instead of silently used.
DEV_ONLY_JWT_SECRET = "careeros-dev-only-secret-do-not-use-in-production"

# Values that are never acceptable for signing real tokens.
PLACEHOLDER_JWT_SECRETS = {"", "change-me", "replace-with-a-secure-random-secret"}


class Settings(BaseSettings):
    """
    Central application configuration, loaded from environment variables.
    See backend/.env.example for the full list of expected variables.
    """

    APP_NAME: str = "CareerOS API"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "postgresql://user:password@localhost:5432/careeros"

    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    LLM_API_KEY: str = ""
    JOBS_API_KEY: str = ""

    MAX_RESUME_SIZE_MB: int = 5

    # AI resume intelligence. Empty AI_PROVIDER disables AI analysis entirely
    # (resumes are parsed deterministically). "openai" talks to any
    # OpenAI-compatible /chat/completions endpoint via httpx; "mock" is for
    # development/tests and is refused in production.
    AI_PROVIDER: str = ""
    AI_API_KEY: str = ""
    AI_MODEL: str = "gpt-4o-mini"
    AI_BASE_URL: str = "https://api.openai.com/v1"
    AI_MAX_RESUME_CHARS: int = 30000
    AI_TIMEOUT_SECONDS: int = 30

    # Explicit allow-list only: the Next.js dev server can run on 3000 or 3001
    # and may be reached via localhost or 127.0.0.1. Never use "*" with
    # credentials. Add real frontend origins before any production deploy.
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("JWT_SECRET")
    @classmethod
    def _validate_jwt_secret(cls, value: str, info) -> str:
        env = (info.data.get("ENVIRONMENT") or "development").strip().lower()
        if value.strip() in PLACEHOLDER_JWT_SECRETS:
            if env == "production":
                raise ValueError(
                    "JWT_SECRET must be set to a strong random secret in "
                    "backend/.env when ENVIRONMENT=production."
                )
            return DEV_ONLY_JWT_SECRET
        return value.strip()

    @model_validator(mode="after")
    def _validate_ai_config(self) -> "Settings":
        env = (self.ENVIRONMENT or "development").strip().lower()
        provider = (self.AI_PROVIDER or "").strip().lower()
        if provider:
            if provider == "mock" and env == "production":
                raise ValueError(
                    "AI_PROVIDER=mock is only for development and tests."
                )
            if provider not in {"openai"}:
                raise ValueError(
                    f"Unsupported AI_PROVIDER {provider!r}; expected one of: "
                    "{'openai'}, or leave empty to disable AI analysis."
                )
            if not (self.AI_API_KEY or "").strip():
                if env == "production":
                    raise ValueError(
                        "AI_API_KEY must be set when AI_PROVIDER is configured "
                        "and ENVIRONMENT=production."
                    )
        return self


settings = Settings()
