"""
DigIdentity Engine — Task Celery per la pipeline PREMIUM.

Triggerato dal webhook Stripe dopo checkout.session.completed.

Flusso:
1. Recupera lead e dati scraping da Supabase
2. Calcola punteggi con premium_scoring
3. Costruisce contesto con premium_context
4. Genera report premium AI con Claude (premium_ai)
5. Converte in PDF professionale premium
6. Genera pagina HTML interattiva
7. Invia email premium con PDF allegato + link HTML
8. Aggiorna stato su Supabase
"""

import logging
import tempfile
from pathlib import Path
import time
import os

from app.core.celery_app import celery_app
from app.core.supabase_client import get_supabase

logger = logging.getLogger(__name__)


def _normalize_lead(lead: dict) -> dict:
    """Normalizza i campi del lead per compatibilita con i moduli premium."""
    return {
        "id": lead.get("id", ""),
        "nome_titolare": lead.get("nome_contatto") or lead.get("contact_name") or lead.get("nome_titolare") or "Titolare",
        "nome_attivita": lead.get("nome_azienda") or lead.get("company_name") or lead.get("nome_attivita") or "Attivita",
        "settore": lead.get("settore_attivita") or lead.get("sector") or lead.get("settore") or "non specificato",
        "citta": lead.get("citta") or lead.get("city") or "",
        "provincia": lead.get("provincia") or "",
        "email": lead.get("email", ""),
        "telefono": lead.get("telefono") or lead.get("phone") or "",
        "website": lead.get("sito_web") or lead.get("website_url") or lead.get("website") or "",
        "scraping_data": lead.get("scraping_data") or {},
        "free_report_markdown": lead.get("free_report_markdown") or "",
    }


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
    from execution.premium_scoring import calculate_scores, determine_top_actions
    from execution.premium_context import build_context, SECTION_DATA_MAP
    from execution.premium_ai import generate_all_sections, assemble_premium_report
    from execution.pdf_generator import markdown_to_pdf
    from execution.send_email import send_premium_report_email
    from execution.html_generator import generate_premium_html, save_premium_html

    logger.info(f"[PREMIUM] Inizio pipeline per lead {lead_id}")
    db = get_supabase()

    # ── 1. Recupera lead ──
    try:
        result = db.table("leads").select("*").eq("id", lead_id).execute()
        if not result.data:
            logger.error(f"[PREMIUM] Lead {lead_id} non trovato")
            return {"status": "error", "message": "Lead non trovato"}
        lead_raw = result.data[0]
    except Exception as e:
        logger.error(f"[PREMIUM] Errore recupero lead {lead_id}: {e}")
        raise self.retry(exc=e)

    # Normalizza campi
    lead = _normalize_lead(lead_raw)
    company_name = lead["nome_attivita"]
    website_url = lead["website"]
    email = lead["email"]

    logger.info(f"[PREMIUM] Lead: {company_name} — {website_url}")

    # Aggiorna stato
    db.table("leads").update({"status": "generating_premium"}).eq("id", lead_id).execute()

    # ── 2. Re-scraping se necessario ──
    scraping_data = lead["scraping_data"]
    if not scraping_data:
        logger.info(f"[PREMIUM] Dati scraping mancanti, eseguo nuovo scraping")
        try:
            scraping_data = scrape_lead(website_url, company_name)
            db.table("leads").update({
                "scraping_data": scraping_data,
            }).eq("id", lead_id).execute()
            lead["scraping_data"] = scraping_data
        except Exception as e:
            logger.error(f"[PREMIUM] Errore re-scraping per {company_name}: {e}")
            db.table("leads").update({
                "status": "error",
                "error_message": f"Errore scraping premium: {str(e)}",
            }).eq("id", lead_id).execute()
            raise self.retry(exc=e)

    # ── 3. Calcolo punteggi ──
    try:
        scores = calculate_scores(scraping_data)
        top_actions = determine_top_actions(scraping_data, scores)
        logger.info(f"[PREMIUM] Punteggio globale: {scores.get('globale', 0)}/100")
    except Exception as e:
        logger.error(f"[PREMIUM] Errore calcolo punteggi per {company_name}: {e}")
        db.table("leads").update({
            "status": "error",
            "error_message": f"Errore scoring premium: {str(e)}",
        }).eq("id", lead_id).execute()
        raise self.retry(exc=e)

    # ── 4. Costruzione contesto ──
    try:
        ctx = build_context(lead, scores, top_actions)
        logger.info(f"[PREMIUM] Contesto costruito per {company_name}")
    except Exception as e:
        logger.error(f"[PREMIUM] Errore contesto per {company_name}: {e}")
        db.table("leads").update({
            "status": "error",
            "error_message": f"Errore contesto premium: {str(e)}",
        }).eq("id", lead_id).execute()
        raise self.retry(exc=e)

    # ── 5. Generazione report AI con Claude ──
    try:
        _gen_start = time.time()
        sections = generate_all_sections(ctx, SECTION_DATA_MAP)
        _gen_time = round(time.time() - _gen_start, 1)
        # Raccogli token da tutte le sezioni
        _total_input = sum(s.get("_tokens", {}).get("input", 0) for s in sections)
        _total_output = sum(s.get("_tokens", {}).get("output", 0) for s in sections)
        _total_tokens = _total_input + _total_output
        _ai_model = sections[0].get("_tokens", {}).get("model", "claude") if sections else "claude"
        report_markdown = assemble_premium_report(sections, ctx)

        # Salva report e punteggi su Supabase
        db.table("leads").update({
            "premium_report_markdown": report_markdown,
            "premium_scores": scores,
            "score_gmb": scores.get("gmb", scores.get("google_business", 0)),
            "score_social": scores.get("social", scores.get("social_media", 0)),
            "score_sito_web": scores.get("sito", scores.get("sito_web", 0)),
            "score_seo": scores.get("seo", 0),
            "score_competitivo": scores.get("competitivo", scores.get("competitor", 0)),
            "score_totale": scores.get("globale", scores.get("totale", 0)),
        }).eq("id", lead_id).execute()

        logger.info(
            f"[PREMIUM] Report AI generato per {company_name}: "
            f"{len(report_markdown)} caratteri, {len(sections)} sezioni"
        )
    except Exception as e:
        logger.error(f"[PREMIUM] Errore generazione AI per {company_name}: {e}")
        db.table("leads").update({
            "status": "error",
            "error_message": f"Errore AI premium: {str(e)}",
        }).eq("id", lead_id).execute()
        raise self.retry(exc=e)

    # ── 6. Generazione PDF premium ──
    try:
        pdf_dir = Path("/app/reports/premium")
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

    # ── 6b. Generazione HTML interattivo ──
    html_url = ""
    try:
        from app.core.config import settings as _app_settings
        base_url = _app_settings.APP_BASE_URL.rstrip("/")

        # Crea URL consulenza per il CTA nell'HTML
        _consulenza_url = "https://buy.stripe.com/3cI3cx3WUaTheOieMgdMI00"

        html_content = generate_premium_html(
            ctx=ctx,
            sections=sections,
            consulenza_url=_consulenza_url,
            lead_id=lead_id,
        )
        html_path = save_premium_html(html_content, lead_id)
        html_url = f"{base_url}/api/reports/diagnosi/premium/{lead_id}"

        # Salva URL su Supabase
        db.table("leads").update({
            "premium_html_url": html_url,
        }).eq("id", lead_id).execute()

        logger.info(f"[PREMIUM] HTML generato: {html_url}")
    except Exception as e:
        # L'HTML è un bonus — se fallisce, il PDF è già pronto
        logger.warning(f"[PREMIUM] Errore generazione HTML (non bloccante): {e}")

    # ── 7. Invio email premium ──
    try:
        # Crea checkout Stripe per consulenza
        consulenza_url = ""
        try:
            import stripe
            from app.core.config import settings as _settings
            stripe.api_key = _settings.STRIPE_SECRET_KEY
            if _settings.STRIPE_PRICE_ID_CONSULENZA:
                checkout = stripe.checkout.Session.create(
                    payment_method_types=["card"],
                    mode="payment",
                    customer_email=email,
                    line_items=[{"price": _settings.STRIPE_PRICE_ID_CONSULENZA, "quantity": 1}],
                    metadata={"lead_id": lead_id, "type": "consulenza"},
                    success_url=f"{_settings.APP_BASE_URL}/api/payment/success-consulenza?session_id={{CHECKOUT_SESSION_ID}}",
                    cancel_url=f"{_settings.APP_BASE_URL}/api/payment/cancel",
                )
                consulenza_url = checkout.url
                logger.info(f"[PREMIUM] Checkout consulenza creato per {company_name}")
        except Exception as ce:
            logger.warning(f"[PREMIUM] Checkout consulenza non creato: {ce}")

        email_sent = send_premium_report_email(
            to_email=email,
            company_name=company_name,
            contact_name=lead["nome_titolare"],
            pdf_path=pdf_path,
            consulenza_url=consulenza_url,
            html_url=html_url,
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

    # ── 8. Insert in tabella reports ──
    try:
        pdf_size = 0
        try:
            pdf_size = os.path.getsize(pdf_path)
        except Exception:
            pass
        ai_cost = round((_total_input / 1000) * 0.003 + (_total_output / 1000) * 0.015, 4)
        db.table("reports").insert({
            "lead_id": lead_id, "report_type": "premium", "ai_model": _ai_model,
            "ai_tokens_input": _total_input, "ai_tokens_output": _total_output,
            "ai_total_tokens": _total_tokens, "ai_cost_usd": ai_cost,
            "pdf_path": pdf_path, "pdf_filename": os.path.basename(pdf_path),
            "pdf_size_bytes": pdf_size, "generation_time_seconds": _gen_time,
            "html_url": html_url,
            "status": "generated",
        }).execute()
        logger.info(f"[PREMIUM] Report in DB: model={_ai_model}, tokens={_total_tokens}, cost=${ai_cost}")
    except Exception as e:
        logger.warning(f"[PREMIUM] Errore insert reports: {e}")

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
        "html_url": html_url,
        "scores": scores,
        "sections_count": len(sections),
        "report_length": len(report_markdown),
    }
