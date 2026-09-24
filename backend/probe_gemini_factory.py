"""One-shot authoritative probe of the gemini factory (Phase 7.3).

No shell quoting games: this imports the provider module through the same
config as pytest and prints, from the module's own namespace, what the
factory ACTUALLY builds for AI_PROVIDER=gemini. Purely confirmatory.
"""
import sys
import os

sys.path.insert(0, os.path.abspath("."))

from app.core.config import settings
from app.services.ai import provider as P

print("PROVIDER_MODULE", P.__file__)
print("SUPPORTED", sorted(P.SUPPORTED_PROVIDERS))
print("SUPPORTED_HAS_GEMINI", "gemini" in P.SUPPORTED_PROVIDERS)
print("GEMINI_BASE_URL_CONST", repr(getattr(P, "PROVIDER_GEMINI_BASE_URL", "<MISSING>")))
print("GEMINI_DEFAULT_MODEL_CONST", repr(getattr(P, "GEMINI_DEFAULT_MODEL", "<MISSING>")))

settings.AI_PROVIDER = "gemini"
settings.AI_API_KEY = "AIza-probe"
settings.AI_MODEL = ""
settings.AI_BASE_URL = ""

provider = P.get_ai_provider()
print("RUNTIME_BASE_URL", repr(provider._base_url))
print("RUNTIME_MODEL", repr(provider._model))
print(
    "MATCHES_GEMINI",
    provider._base_url == getattr(P, "PROVIDER_GEMINI_BASE_URL", None)
    and provider._model == getattr(P, "GEMINI_DEFAULT_MODEL", None),
)
