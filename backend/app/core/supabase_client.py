"""
DigIdentity Engine — Client Supabase singleton (thread-safe).
"""

import threading
from supabase import create_client, Client
from backend.app.core.config import settings

_client: Client | None = None
_lock = threading.Lock()


def get_supabase() -> Client:
    """Restituisce il client Supabase (service role per operazioni backend).
    Thread-safe per utilizzo in Celery worker con concurrency > 1.
    """
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                _client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_KEY,
                )
    return _client
