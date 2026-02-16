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
import time
import os

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.supabase_client import get_supabase

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
    from execution.pdf_generator import generate_pdf
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

    # Estrazione città e settore (Fix 1)
    city = lead.get("citta") or lead.get("city", "")
    sector = lead.get("settore_attivita") or lead.get("sector", "")
    logger.info(f"[FREE] Città: {city}, Settore: {sector}")

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
        scraping_data = scrape_lead(website_url, company_name, social_links_db, city, sector)

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
        _gen_start = time.time()
        ai_result = generate_free_report(scraping_data)
        _gen_time = round(time.time() - _gen_start, 1)
        report_markdown = ai_result["text"]
        ai_model = ai_result.get("model", "unknown")
        ai_input = ai_result.get("input_tokens", 0)
        ai_output = ai_result.get("output_tokens", 0)
        ai_total = ai_input + ai_output

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

    # ── 4. Generazione PDF ──
    try:
        pdf_dir = Path("/app/reports/free")
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = str(pdf_dir / f"free_{lead_id}.pdf")

        generate_pdf(
            report_markdown,
            pdf_path,
            scraping_data=scraping_data,
            company_name=company_name,
            date_str="",
            location=f"{city}, {lead.get('provincia', '')}"
        )
        logger.info(f"[FREE] PDF generato: {pdf_path}")
    except Exception as e:
        logger.error(f"[FREE] Errore PDF per {company_name}: {e}")
        db.table("leads").update({
            "status": "error",
            "error_message": f"Errore PDF: {str(e)}",
        }).eq("id", lead_id).execute()
        raise self.retry(exc=e)

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

    # ── 7. Calcolo Score ──
    try:
        gb = scraping_data.get("google_business", {})
        gmb_rating = gb.get("rating", 0) or 0
        gmb_reviews_raw = gb.get("total_reviews", 0)
        gmb_reviews = len(gmb_reviews_raw) if isinstance(gmb_reviews_raw, list) else (gmb_reviews_raw or 0)
        score_gmb = min(100, int(gmb_rating * 12 + min(gmb_reviews, 200) * 0.2))

        apify_data = scraping_data.get("apify", {})
        ig_followers = (apify_data.get("instagram", {}).get("followers", 0) or 0)
        fb_followers = (apify_data.get("facebook", {}).get("followers", 0) or 0)
        ig_found = 1 if apify_data.get("instagram", {}).get("found") else 0
        fb_found = 1 if apify_data.get("facebook", {}).get("found") else 0
        score_social = min(100, int((ig_found + fb_found) * 25 + min(ig_followers + fb_followers, 5000) * 0.01))

        ps = scraping_data.get("pagespeed", {})
        perf = ps.get("performance_score", 0) or 0
        has_site = 1 if scraping_data.get("has_website") else 0
        score_sito = min(100, int(has_site * 40 + perf * 0.6))

        indexed = scraping_data.get("indexed_pages", {}).get("total", 0) or 0
        citations_count = len(scraping_data.get("citations", []))
        score_seo = min(100, int(min(indexed, 100) * 0.3 + min(citations_count, 20) * 3))

        comp = scraping_data.get("competitors", [])
        n_comp = len(comp) if isinstance(comp, list) else 0
        score_comp = max(20, 100 - n_comp * 10)

        score_totale = int(score_gmb * 0.30 + score_social * 0.25 + score_sito * 0.20 + score_seo * 0.15 + score_comp * 0.10)

        db.table("leads").update({
            "score_gmb": score_gmb, "score_social": score_social,
            "score_sito_web": score_sito, "score_seo": score_seo,
            "score_competitivo": score_comp, "score_totale": score_totale,
        }).eq("id", lead_id).execute()
        logger.info(f"[FREE] Score: totale={score_totale}, gmb={score_gmb}, social={score_social}, sito={score_sito}, seo={score_seo}, comp={score_comp}")
    except Exception as e:
        logger.warning(f"[FREE] Errore score: {e}")

    # ── 8. Insert in tabella reports ──
    try:
        pdf_size = 0
        try:
            pdf_size = os.path.getsize(pdf_path)
        except Exception:
            pass
        ai_cost = round((ai_input / 1000) * 0.003 + (ai_output / 1000) * 0.015, 4)
        db.table("reports").insert({
            "lead_id": lead_id, "report_type": "free", "ai_model": ai_model,
            "ai_tokens_input": ai_input, "ai_tokens_output": ai_output,
            "ai_total_tokens": ai_total, "ai_cost_usd": ai_cost,
            "pdf_path": pdf_path, "pdf_filename": os.path.basename(pdf_path),
            "pdf_size_bytes": pdf_size, "generation_time_seconds": _gen_time,
            "status": "generated",
        }).execute()
        logger.info(f"[FREE] Report in DB: model={ai_model}, tokens={ai_total}, cost=${ai_cost}")
    except Exception as e:
        logger.warning(f"[FREE] Errore insert reports: {e}")

    logger.info(f"[FREE] Pipeline completata con successo per {company_name} ({lead_id})")
    return {
        "status": "success",
        "lead_id": lead_id,
        "company_name": company_name,
        "email": email,
        "pdf_path": pdf_path,
        "checkout_url": checkout_url,
    }
