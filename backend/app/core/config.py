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
    # Live job search (JSearch via RapidAPI). Empty JOBS_API_KEY disables
    # live recommendations; the seeded job catalogue stays browsable.
    JOBS_API_KEY: str = ""
    JOBS_API_HOST: str = "jsearch.p.rapidapi.com"
    JOBS_DEFAULT_COUNTRY: str = "pk"
    JOBS_DEFAULT_LOCATION: str = "Pakistan"
    JOBS_MAX_QUERIES: int = 3
    JOBS_DATE_POSTED: str = "month"
    JOBS_TIMEOUT_SECONDS: int = 20
    # Each query costs one request against the provider's monthly quota, so a
    # user's results are reused until their resume changes or this expires.
    JOBS_CACHE_MINUTES: int = 360
    # Keyless fallback used when JOBS_API_KEY is empty: "jobicy" (real remote
    # jobs, no key) or "" to disable live recommendations entirely.
    JOBS_FALLBACK_PROVIDER: str = "jobicy"
    # Jobicy region filter sent with each search, then a local filter that
    # keeps only postings open to one of JOBICY_ALLOWED_REGIONS (most are
    # country-locked, e.g. "USA"). Each query is cached for all users.
    JOBICY_GEO: str = "apac"
    JOBICY_ALLOWED_REGIONS: str = "anywhere,worldwide,global,apac,asia,pakistan"
    JOBICY_CACHE_MINUTES: int = 360

    MAX_RESUME_SIZE_MB: int = 5

    # AI resume intelligence. Empty AI_PROVIDER disables AI analysis entirely
    # (resumes are parsed deterministically). "openai" talks to any
    # OpenAI-compatible /chat/completions endpoint via httpx; "mock" is for
    # development/tests and is refused in production. AI_MODEL and AI_BASE_URL
    # are intentionally empty by default so the provider factory resolves each
    # provider's own endpoint/model (OpenAI vs Gemini); set them explicitly to
    # override the provider default.
    AI_PROVIDER: str = ""
    AI_API_KEY: str = ""
    AI_MODEL: str = ""
    AI_BASE_URL: str = ""
    AI_MAX_RESUME_CHARS: int = 30000
    AI_TIMEOUT_SECONDS: int = 30

    # Bounded retry policy for transient provider failures (rate limits,
    # timeouts, connection resets, 5xx). "AI_MAX_RETRIES" is the number of
    # *additional* attempts after the first, so the default of 2 means at most
    # 3 HTTP calls. Permanent failures (invalid key, bad request, unusable
    # output) are never retried. Backoff is exponential starting at
    # AI_RETRY_BASE_DELAY_SECONDS and capped at AI_RETRY_MAX_DELAY_SECONDS, so
    # the worst case stays well under a couple of seconds of added latency and
    # can never loop indefinitely.
    AI_MAX_RETRIES: int = 2
    AI_RETRY_BASE_DELAY_SECONDS: float = 0.5
    AI_RETRY_MAX_DELAY_SECONDS: float = 4.0

    # Explicit allow-list only: the Next.js dev server can run on 3000 or 3001
    # and may be reached via localhost or 127.0.0.1. Never use "*" with
    # credentials. Add real frontend origins before any production deploy.
    ALLOWED_ORIGINS: list[str] = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "https://career-os-five-lac.vercel.app",
    ]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("AI_MAX_RETRIES")
    @classmethod
    def _clamp_ai_max_retries(cls, value: int) -> int:
        # Bounded by design: at most 5 retries (6 calls) so a misconfigured
        # environment can never turn one upload into a long stall.
        return max(0, min(int(value), 5))

    @field_validator("AI_RETRY_BASE_DELAY_SECONDS", "AI_RETRY_MAX_DELAY_SECONDS")
    @classmethod
    def _clamp_ai_retry_delays(cls, value: float) -> float:
        return max(0.0, min(float(value), 10.0))

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
            if provider == "mock":
                # Development/tests only: a deterministic provider with no API
                # key. Refused in production so real deployments never run on
                # mock intelligence.
                if env == "production":
                    raise ValueError(
                        "AI_PROVIDER=mock is only for development and tests."
                    )
                return self
            if provider not in {"openai", "gemini"}:
                raise ValueError(
                    f"Unsupported AI_PROVIDER {provider!r}; expected one of: "
                    "{'openai', 'gemini'}, or leave empty to disable AI analysis."
                )
            if not (self.AI_API_KEY or "").strip():
                if env == "production":
                    raise ValueError(
                        "AI_API_KEY must be set when AI_PROVIDER is configured "
                        "and ENVIRONMENT=production."
                    )
        return self


settings = Settings()
