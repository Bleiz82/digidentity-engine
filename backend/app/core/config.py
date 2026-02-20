"""
DigIdentity Engine — Configurazione centralizzata.
Carica variabili d'ambiente da .env nella root del progetto.
"""

import os
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv

# Carica .env dalla root del progetto
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)


class Settings:
    """Impostazioni globali caricate da variabili d'ambiente."""

    # --- Supabase ---
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")

    # --- Stripe ---
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_PRICE_ID: str = os.getenv("STRIPE_PRICE_ID", "")
    STRIPE_PRICE_ID_PREMIUM: str = os.getenv("STRIPE_PRICE_ID_PREMIUM", os.getenv("STRIPE_PRICE_ID", ""))
    STRIPE_PRICE_ID_CONSULENZA: str = os.getenv("STRIPE_PRICE_ID_CONSULENZA", "")
    STRIPE_LINK_PREMIUM: str = os.getenv("STRIPE_LINK_PREMIUM", "")
    STRIPE_LINK_CONSULENZA: str = os.getenv("STRIPE_LINK_CONSULENZA", "")

    # --- Anthropic ---
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # --- SerpAPI ---
    SERPAPI_KEY: str = os.getenv("SERPAPI_KEY", os.getenv("SERP_API_KEY", ""))

    # --- Perplexity ---
    PERPLEXITY_API_KEY: str = os.getenv("PERPLEXITY_API_KEY", "")
    PERPLEXITY_MODEL: str = os.getenv("PERPLEXITY_MODEL", "sonar-pro")

    # --- Apify ---
    APIFY_API_KEY: str = os.getenv("APIFY_API_KEY", "")

    # --- Google APIs ---
    GOOGLE_PAGESPEED_API_KEY: str = os.getenv("GOOGLE_PAGESPEED_API_KEY", "")

    # --- OpenAI ---
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # --- SMTP ---
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "DigIdentity Engine")

    # --- Redis / Celery ---
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

    # --- App ---
    APP_BASE_URL: str = os.getenv("APP_BASE_URL", "http://127.0.0.1:8080")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


import logging as _logging
_config_logger = _logging.getLogger(__name__)


@lru_cache()
def get_settings() -> Settings:
    s = Settings()
    # Validazione base all'avvio
    critical = {
        "SUPABASE_URL": s.SUPABASE_URL,
        "SUPABASE_SERVICE_KEY": s.SUPABASE_SERVICE_KEY,
        "STRIPE_SECRET_KEY": s.STRIPE_SECRET_KEY,
        "ANTHROPIC_API_KEY": s.ANTHROPIC_API_KEY,
        "SERPAPI_KEY": s.SERPAPI_KEY,
        "SMTP_USER": s.SMTP_USER,
        "SMTP_PASSWORD": s.SMTP_PASSWORD,
    }
    for key, value in critical.items():
        if not value:
            _config_logger.warning(f"[CONFIG] MANCANTE: {key} non configurata nel .env")
    return s


settings = get_settings()
