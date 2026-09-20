"""Job provider registry.

``get_active_provider()`` returns the provider used for ingestion/seeding. Only
providers bundled with the application are supported for now; external sources
arrive in later phases and swap in behind the same :class:`JobProvider`
contract.
"""

from app.services.providers.base import JobProvider, ProviderJob
from app.services.providers.demo import DemoJobProvider

__all__ = ["JobProvider", "ProviderJob", "DemoJobProvider", "get_active_provider"]


def get_active_provider() -> JobProvider:
    """Resolve the default job provider for the application.

    Configuration-driven selection (by ``JOBS_API_KEY`` or a dedicated setting)
    is deferred until a real external provider is integrated. The demo provider
    is always available so the full pipeline works out of the box.
    """
    return DemoJobProvider()