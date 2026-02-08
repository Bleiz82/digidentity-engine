"""
DigIdentity Engine — Configurazione Centralizzata
Gestisce tutte le variabili d'ambiente e settings dell'applicazione.
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Settings centralizzate dell'applicazione.
    Tutte le variabili vengono lette dal file .env nella root del progetto.
    """
    
    # ---- App ----
    app_name: str = "DigIdentity Engine"
    app_base_url: str = "https://digidentityagency.it"
    reports_dir: str = "./reports"
    secret_key: str
    debug: bool = False
    
    # ---- Supabase ----
    supabase_url: str
    supabase_key: str  # anon key
    supabase_service_key: str  # service_role key per bypass RLS
    
    # ---- AI: Anthropic Claude (primario) ----
    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-4-20250514"
    anthropic_max_tokens: int = 4000
    
    # ---- AI: OpenAI (backup) ----
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    
    # ---- AI: Perplexity (ricerche contestuali) ----
    perplexity_api_key: Optional[str] = None
    perplexity_model: str = "sonar-pro"
    
    # ---- Google APIs ----
    google_pagespeed_api_key: str
    
    # ---- SerpAPI ----
    serp_api_key: str
    serp_api_monthly_limit: int = 250  # Free tier
    
    # ---- Stripe ----
    stripe_secret_key: str
    stripe_webhook_secret: str
    stripe_price_id_premium: Optional[str] = None  # Se usi Price ID invece di amount
    
    # ---- Email: Gmail SMTP ----
    gmail_smtp_user: str = "digidentityagency@gmail.com"
    gmail_smtp_password: str  # App password
    gmail_smtp_host: str = "smtp.gmail.com"
    gmail_smtp_port: int = 587
    
    # ---- Email: Resend (alternativo) ----
    resend_api_key: Optional[str] = None
    
    # ---- Email: Sender Info ----
    sender_email: str = "digidentityagency@gmail.com"
    sender_name: str = "DigIdentity Agency"
    
    # ---- WhatsApp: Meta Business API ----
    whatsapp_access_token: str  # Token permanente
    whatsapp_phone_number_id: str  # Phone Number ID
    whatsapp_webhook_verify_token: Optional[str] = None  # Per webhook verification
    
    # ---- Redis ----
    redis_url: str = "redis://localhost:6379/0"
    
    # ---- Celery ----
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # ---- Rate Limiting ----
    rate_limit_per_ip: int = 5  # Max richieste per IP al minuto
    
    # ---- Configurazione Pydantic ----
    model_config = SettingsConfigDict(
        env_file="../.env",  # Legge dalla root del progetto
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Singleton per le settings.
    Usa @lru_cache per caricare le settings una sola volta.
    
    Returns:
        Settings: Istanza delle settings
    """
    return Settings()


# Esporta per import diretto
settings = get_settings()
