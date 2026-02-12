"""
DigIdentity Engine — Task Celery per la pipeline FREE.

Flusso:
1. Recupera lead da Supabase
2. Esegue scraping del sito web e presenza digitale
3. Genera report AI con Claude (diagnosi gratuita)
4. Converte in PDF professionale
5. Crea Stripe Checkout Session per premium
6. Invia email con PDF allegato e CTA per upgrade
7. Aggiorna stato su Supabase
"""

import logging
import tempfile
from pathlib import Path

from backend.app.core.celery_app import celery_app
from backend.app.core.config import settings
from backend.app.core.supabase_client import get_supabase

logger = logging.getLogger(__name__)


@celery_app.task(
    name="task_free_report",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
    acks_late=True,
)
def task_free_report(self, lead_id: str):
    """
    Pipeline completa per la generazione e invio del report gratuito.
    """
    import stripe
    from execution.scraper import scrape_lead
    from execution.ai_report import generate_free_report
    from execution.pdf_generator import markdown_to_pdf
    from execution.send_email import send_free_report_email

    logger.info(f"[FREE] Inizio pipeline per lead {lead_id}")
    db = get_supabase()

    # ── 1. Recupera lead ──
    try:
        result = db.table("leads").select("*").eq("id", lead_id).execute()
        if not result.data:
            logger.error(f"[FREE] Lead {lead_id} non trovato su Supabase")
            return {"status": "error", "message": "Lead non trovato"}
        lead = result.data[0]
    except Exception as e:
        logger.error(f"[FREE] Errore recupero lead {lead_id}: {e}")
        raise self.retry(exc=e)

    company_name = lead.get("nome_azienda") or lead.get("company_name", "")
    website_url = lead.get("sito_web") or lead.get("website_url", "")
    email = lead["email"]
    contact_name = lead.get("nome_contatto") or lead.get("contact_name", "")

    logger.info(f"[FREE] Lead: {company_name} — {website_url} — {email}")

    # Parsa piattaforme_social dal lead
    social_links_db = {}
    piattaforme_social_str = lead.get("piattaforme_social", "")
    if piattaforme_social_str:
        try:
            pairs = piattaforme_social_str.split(",")
            for pair in pairs:
                if ":" in pair:
                    platform, value = pair.split(":", 1)
                    social_links_db[platform.strip()] = value.strip()
        except Exception as e:
            logger.warning(f"Errore parsing piattaforme_social: {e}")

    # ── 2. Scraping ──
    try:
        db.table("leads").update({"status": "scraping"}).eq("id", lead_id).execute()
        scraping_data = scrape_lead(website_url, company_name, social_links_db)

        # Salva dati scraping su Supabase
        db.table("leads").update({
            "scraping_data": scraping_data,
        }).eq("id", lead_id).execute()

        logger.info(f"[FREE] Scraping completato per {company_name}")
    except Exception as e:
        logger.error(f"[FREE] Errore scraping per {company_name}: {e}")
        db.table("leads").update({
            "status": "error",
            "error_message": f"Errore scraping: {str(e)}",
        }).eq("id", lead_id).execute()
        raise self.retry(exc=e)

    # ── 3. Generazione report AI ──
    try:
        db.table("leads").update({"status": "generating_free"}).eq("id", lead_id).execute()
        report_markdown = generate_free_report(scraping_data)

        # Salva report su Supabase
        db.table("leads").update({
            "free_report_markdown": report_markdown,
        }).eq("id", lead_id).execute()

        logger.info(f"[FREE] Report AI generato per {company_name}: {len(report_markdown)} car.")
    except Exception as e:
        logger.error(f"[FREE] Errore generazione AI per {company_name}: {e}")
        db.table("leads").update({
            "status": "error",
            "error_message": f"Errore AI: {str(e)}",
        }).eq("id", lead_id).execute()
        raise self.retry(exc=e)

    # ── 4. Generazione PDF ──
    try:
        pdf_dir = Path(tempfile.gettempdir()) / "digidentity" / "reports"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = str(pdf_dir / f"free_{lead_id}.pdf")

        markdown_to_pdf(
            markdown_text=report_markdown,
            output_path=pdf_path,
            report_type="free",
            company_name=company_name,
        )
        logger.info(f"[FREE] PDF generato: {pdf_path}")
    except Exception as e:
        logger.error(f"[FREE] Errore PDF per {company_name}: {e}")
        db.table("leads").update({
            "status": "error",
            "error_message": f"Errore PDF: {str(e)}",
        }).eq("id", lead_id).execute()
        raise self.retry(exc=e)

    # ── 5. Crea Stripe Checkout URL per il premium ──
    checkout_url = f"{settings.APP_BASE_URL}/api/payment/create-checkout"
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": "DigIdentity — Report Premium",
                        "description": (
                            f"Piano Strategico Digitale completo per "
                            f"{company_name} — 40-50 pagine"
                        ),
                    },
                    "unit_amount": 9900,
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
        checkout_url = checkout_session.url

        # Salva session ID
        db.table("leads").update({
            "stripe_session_id": checkout_session.id,
        }).eq("id", lead_id).execute()

        logger.info(f"[FREE] Checkout session creata: {checkout_session.id}")
    except Exception as e:
        logger.warning(f"[FREE] Errore creazione Stripe session: {e} — uso URL fallback")
        # Fallback: usa l'endpoint API che creerà la session on-demand
        checkout_url = f"{settings.APP_BASE_URL}/api/payment/create-checkout?lead_id={lead_id}"

    # ── 6. Invio email ──
    try:
        email_sent = send_free_report_email(
            to_email=email,
            company_name=company_name,
            contact_name=contact_name,
            pdf_path=pdf_path,
            checkout_url=checkout_url,
        )

        if email_sent:
            db.table("leads").update({"status": "free_sent"}).eq("id", lead_id).execute()
            logger.info(f"[FREE] Email inviata con successo a {email}")
        else:
            db.table("leads").update({
                "status": "error",
                "error_message": "Errore invio email",
            }).eq("id", lead_id).execute()
            logger.error(f"[FREE] Errore invio email a {email}")

    except Exception as e:
        logger.error(f"[FREE] Errore invio email per {company_name}: {e}")
        db.table("leads").update({
            "status": "error",
            "error_message": f"Errore email: {str(e)}",
        }).eq("id", lead_id).execute()
        raise self.retry(exc=e)

    logger.info(f"[FREE] Pipeline completata con successo per {company_name} ({lead_id})")
    return {
        "status": "success",
        "lead_id": lead_id,
        "company_name": company_name,
        "email": email,
        "pdf_path": pdf_path,
        "checkout_url": checkout_url,
    }
