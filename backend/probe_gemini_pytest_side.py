"""Mirror the gemini test import side, verbatim-style, to see whether pytest's
import path differs from the probe's. Prints the module identity pytest would
use and the factory result under gemini settings."""

import sys
sys.path.insert(0, ".")

from app.services.ai.provider import (
    GEMINI_DEFAULT_MODEL,
    PROVIDER_GEMINI_BASE_URL,
    OpenAICompatibleProvider,
    get_ai_provider,
    parse_json_payload,
)
import app.services.ai.provider as provider_module

from app.core.config import settings

print("MODULE_FILE", provider_module.__file__)
print("SUPPORTED", repr(sorted(provider_module.SUPPORTED_PROVIDERS)))
print("GEM_BASE_URL_CONST", repr(provider_module.PROVIDER_GEMINI_BASE_URL))
print("GEM_MODEL_CONST", repr(provider_module.GEMINI_DEFAULT_MODEL))
print("IMPORTED_GEM_BASE_URL", repr(PROVIDER_GEMINI_BASE_URL))
print("IMPORTED_GEM_MODEL", repr(GEMINI_DEFAULT_MODEL))

settings.AI_PROVIDER = "gemini"
settings.AI_API_KEY = "AIza-probe"
settings.AI_MODEL = ""
settings.AI_BASE_URL = ""
provider = get_ai_provider()
print("PROVIDER_TYPE", type(provider).__name__)
print("PROVIDER_BASE_URL", repr(getattr(provider, "_base_url", "<none>")))
print("PROVIDER_MODEL", repr(getattr(provider, "_model", "<none>")))
print("DEFAULT_FACTORY_IS", provider_module.get_ai_provider is get_ai_provider)
