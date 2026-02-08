"""
DigIdentity Engine — Supabase Client
Singleton per il client Supabase con service_role key.
"""

from functools import lru_cache
from supabase import create_client, Client
from app.config import get_settings


@lru_cache()
def get_supabase_client() -> Client:
    """
    Crea e restituisce un client Supabase singleton.
    Usa la service_role key per bypassare RLS (Row Level Security).
    
    Returns:
        Client: Istanza del client Supabase
    """
    settings = get_settings()
    
    # Usa service_role key per accesso completo al database
    client = create_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_service_key
    )
    
    return client


# Esporta istanza singleton per import diretto
supabase = get_supabase_client()
