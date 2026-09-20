from pydantic import field_validator
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

    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

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


settings = Settings()
