"""
DigIdentity Engine — Stripe Service Layer.

Centralizza la logica Stripe: validazione config, creazione sessioni,
verifica webhook. Utilizzato da payment.py e dai task Celery.
"""

import logging
from typing import Optional

import stripe

from app.core.config import settings

logger = logging.getLogger(__name__)


def configure_stripe():
    """Configura e valida la connessione Stripe."""
    if not settings.STRIPE_SECRET_KEY:
        logger.warning("STRIPE_SECRET_KEY non configurata!")
        return False

    stripe.api_key = settings.STRIPE_SECRET_KEY

    # Verifica la connessione
    try:
        stripe.Account.retrieve()
        logger.info("Stripe configurato correttamente")
        return True
    except stripe.error.AuthenticationError:
        logger.error("STRIPE_SECRET_KEY non valida!")
        return False
    except Exception as e:
        logger.warning(f"Impossibile verificare Stripe: {e}")
        return True  # La chiave potrebbe essere valida, rete non disponibile


def create_checkout_session(
    lead_id: str,
    company_name: str,
    email: str,
    description: Optional[str] = None,
) -> Optional[stripe.checkout.Session]:
    """
    Crea una Stripe Checkout Session standardizzata per il report premium.
    Restituisce la session o None in caso di errore.
    """
    stripe.api_key = settings.STRIPE_SECRET_KEY

    if not description:
        description = (
            f"Piano Strategico Digitale completo per {company_name} "
            f"— 40-50 pagine con analisi approfondita, calendario editoriale, "
            f"e preventivo dettagliato."
        )

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": "DigIdentity — Report Premium",
                        "description": description,
                    },
                    "unit_amount": 9900,  # 99,00€ in centesimi
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=(
                f"{settings.APP_BASE_URL}/api/payment/success"
                f"?session_id={{CHECKOUT_SESSION_ID}}"
            ),
            cancel_url=f"{settings.APP_BASE_URL}/api/payment/cancel",
            metadata={
                "lead_id": lead_id,
                "company_name": company_name,
                "email": email,
            },
            customer_email=email,
        )
        logger.info(f"Checkout session creata: {session.id} per {company_name}")
        return session

    except stripe.error.StripeError as e:
        logger.error(f"Errore Stripe: {e}")
        return None


def verify_webhook_signature(payload: bytes, sig_header: str) -> Optional[dict]:
    """
    Verifica la firma di un webhook Stripe e restituisce l'evento.
    Restituisce None se la verifica fallisce.
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        logger.error(
            "STRIPE_WEBHOOK_SECRET non configurata! "
            "Esegui 'stripe listen' e copia il whsec_... nel .env"
        )
        return None

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
        return event
    except ValueError:
        logger.error("Webhook payload non valido (JSON malformato)")
        return None
    except stripe.error.SignatureVerificationError:
        logger.error(
            "Webhook firma non valida! Verifica che STRIPE_WEBHOOK_SECRET "
            "nel .env corrisponda al whsec_... di 'stripe listen'"
        )
        return None
