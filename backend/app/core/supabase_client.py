"""
DigIdentity Engine — Client Supabase singleton.
"""

from supabase import create_client, Client
from app.core.config import settings

_client: Client | None = None


def get_supabase() -> Client:
    """Restituisce il client Supabase (service role per operazioni backend)."""
    global _client
    if _client is None:
        _client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_KEY,
        )
    return _client
