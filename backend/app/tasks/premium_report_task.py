"""
DigIdentity Engine — Task Celery per la pipeline PREMIUM.

Triggerato dal webhook Stripe dopo checkout.session.completed.

Flusso:
1. Recupera lead e dati scraping da Supabase
2. Genera report premium AI con Claude (40-50 pagine, multi-sezione)
3. Converte in PDF professionale premium
4. Invia email premium con PDF allegato
5. Aggiorna stato su Supabase
"""

import logging
import tempfile
from pathlib import Path

from backend.app.core.celery_app import celery_app
from backend.app.core.config import settings
from backend.app.core.supabase_client import get_supabase

logger = logging.getLogger(__name__)


@celery_app.task(
    name="task_premium_report",
    bind=True,
    max_retries=2,
    default_retry_delay=180,
    acks_late=True,
)
def task_premium_report(self, lead_id: str):
    """
    Pipeline completa per la generazione e invio del report premium.
    Viene triggerato dopo il pagamento Stripe (via webhook).
    """
    from execution.scraper import scrape_lead
    from execution.ai_report import generate_premium_report
    from execution.pdf_generator import markdown_to_pdf
    from execution.send_email import send_premium_report_email

    logger.info(f"[PREMIUM] Inizio pipeline per lead {lead_id}")
    db = get_supabase()

    # ── 1. Recupera lead e dati scraping ──
    try:
        result = db.table("leads").select("*").eq("id", lead_id).execute()
        if not result.data:
            logger.error(f"[PREMIUM] Lead {lead_id} non trovato")
            return {"status": "error", "message": "Lead non trovato"}
        lead = result.data[0]
    except Exception as e:
        logger.error(f"[PREMIUM] Errore recupero lead {lead_id}: {e}")
        raise self.retry(exc=e)

    company_name = lead["company_name"]
    website_url = lead["website_url"]
    email = lead["email"]
    contact_name = lead.get("contact_name")
    scraping_data = lead.get("scraping_data")
    free_report = lead.get("free_report_markdown", "")

    logger.info(f"[PREMIUM] Lead: {company_name} — {website_url}")

    # Aggiorna stato
    db.table("leads").update({"status": "generating_premium"}).eq("id", lead_id).execute()

    # ── 2. Re-scraping se necessario (dati più freschi o mancanti) ──
    if not scraping_data:
        logger.info(f"[PREMIUM] Dati scraping mancanti, eseguo nuovo scraping")
        try:
            scraping_data = scrape_lead(website_url, company_name)
            db.table("leads").update({
                "scraping_data": scraping_data,
            }).eq("id", lead_id).execute()
        except Exception as e:
            logger.error(f"[PREMIUM] Errore re-scraping per {company_name}: {e}")
            db.table("leads").update({
                "status": "error",
                "error_message": f"Errore scraping premium: {str(e)}",
            }).eq("id", lead_id).execute()
            raise self.retry(exc=e)

    # ── 3. Generazione report premium AI (multi-sezione) ──
    try:
        report_markdown = generate_premium_report(scraping_data, free_report)

        # Salva report su Supabase
        db.table("leads").update({
            "premium_report_markdown": report_markdown,
        }).eq("id", lead_id).execute()

        logger.info(
            f"[PREMIUM] Report AI generato per {company_name}: "
            f"{len(report_markdown)} caratteri"
        )
    except Exception as e:
        logger.error(f"[PREMIUM] Errore generazione AI per {company_name}: {e}")
        db.table("leads").update({
            "status": "error",
            "error_message": f"Errore AI premium: {str(e)}",
        }).eq("id", lead_id).execute()
        raise self.retry(exc=e)

    # ── 4. Generazione PDF premium ──
    try:
        pdf_dir = Path(tempfile.gettempdir()) / "digidentity" / "reports"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = str(pdf_dir / f"premium_{lead_id}.pdf")

        markdown_to_pdf(
            markdown_text=report_markdown,
            output_path=pdf_path,
            report_type="premium",
            company_name=company_name,
        )
        logger.info(f"[PREMIUM] PDF generato: {pdf_path}")
    except Exception as e:
        logger.error(f"[PREMIUM] Errore PDF per {company_name}: {e}")
        db.table("leads").update({
            "status": "error",
            "error_message": f"Errore PDF premium: {str(e)}",
        }).eq("id", lead_id).execute()
        raise self.retry(exc=e)

    # ── 5. Invio email premium ──
    try:
        email_sent = send_premium_report_email(
            to_email=email,
            company_name=company_name,
            contact_name=contact_name,
            pdf_path=pdf_path,
        )

        if email_sent:
            db.table("leads").update({
                "status": "premium_sent",
            }).eq("id", lead_id).execute()
            logger.info(f"[PREMIUM] Email premium inviata a {email}")
        else:
            db.table("leads").update({
                "status": "error",
                "error_message": "Errore invio email premium",
            }).eq("id", lead_id).execute()
            logger.error(f"[PREMIUM] Errore invio email premium a {email}")

    except Exception as e:
        logger.error(f"[PREMIUM] Errore invio email per {company_name}: {e}")
        db.table("leads").update({
            "status": "error",
            "error_message": f"Errore email premium: {str(e)}",
        }).eq("id", lead_id).execute()
        raise self.retry(exc=e)

    logger.info(
        f"[PREMIUM] Pipeline completata con successo per "
        f"{company_name} ({lead_id})"
    )
    return {
        "status": "success",
        "lead_id": lead_id,
        "company_name": company_name,
        "email": email,
        "pdf_path": pdf_path,
    }
