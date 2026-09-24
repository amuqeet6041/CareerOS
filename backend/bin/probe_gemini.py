"""One-shot: why does pytest see openai when the factory reads gemini?

Runs inside pytest-flavoured plain python (no pytest import needed) and prints
authoritative facts about the exact module object pytest runs against. Every
line is computed at runtime by CPython from the same interpreter that will run
the suite — nothing hand-transcribed.
"""
import app.services.ai.provider as provider_module

name = (provider_module.settings.AI_PROVIDER or "").strip().lower()
print("MODULE_FILE", provider_module.__file__)
print("SUPPORTED", repr(provider_module.SUPPORTED_PROVIDERS))
print("SETTINGS_IS_SAME", provider_module.settings
      is __import__("app.core.config", fromlist=["settings"]).settings)
print("GEMINI_URL", repr(provider_module.PROVIDER_GEMINI_BASE_URL))
print("GEMINI_MODEL", repr(provider_module.GEMINI_DEFAULT_MODEL))

provider_module.settings.AI_PROVIDER = "gemini"
provider_module.settings.AI_API_KEY = "AIza-test"
provider_module.settings.AI_MODEL = ""
provider_module.settings.AI_BASE_URL = ""
p = provider_module.get_ai_provider()
print("RUNTIME_BASE_URL", repr(p._base_url))
print("RUNTIME_MODEL", repr(p._model))
