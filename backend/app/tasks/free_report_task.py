"""
DigIdentity Engine — Task Celery per la pipeline FREE.

Flusso:
1. Recupera lead da Supabase
2. Esegue scraping del sito web e presenza digitale
3. Genera report AI con Claude (diagnosi gratuita)
4. Converte in PDF professionale
5. Crea Stripe Checkout Session per premium
6. Genera pagina HTML interattiva
7. Invia email con PDF allegato, link HTML e CTA per upgrade
8. Aggiorna stato su Supabase
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
    from execution.html_generator import generate_free_html, save_free_html

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

    # Estrazione città e settore
    city = lead.get("citta") or lead.get("city", "")
    sector = lead.get("settore_attivita") or ""
    if not sector:
        # Prova anche il campo scraping_data se già presente
        scraping_cached = lead.get("scraping_data") or {}
        sector = scraping_cached.get("sector") or scraping_cached.get("extracted_sector") or ""
    
    indirizzo = lead.get("indirizzo") or ""
    logger.info(f"[FREE] Città: {city}, Settore: {sector}, Indirizzo: {indirizzo}")

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
        scraping_data = scrape_lead(website_url, company_name, social_links_db, city, sector, indirizzo)

        # Salva dati scraping su Supabase (Fix 1: persistenza totale)
        db.table("leads").update({
            "scraping_data": scraping_data,
            "settore_attivita": scraping_data.get("sector") or scraping_data.get("extracted_sector") or sector,
            "citta": scraping_data.get("city") or city,
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

    # ── 4. Crea Stripe Checkout URL per il premium ──
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
        checkout_url = f"{settings.APP_BASE_URL}/api/payment/create-checkout?lead_id={lead_id}"

    # ── 5. Calcolo Score Canonico (Fix: allineamento PDF/HTML/DB) ──
    from execution.calculate_scores import compute_free_scores
    scores = compute_free_scores(scraping_data)
    # Inietta score in scraping_data così che i generatori li trovino
    scraping_data["scores"] = scores
    # Per retrocompatibilità con pdf_generator
    scraping_data["social_score"] = scores["score_social"]
    
    logger.info(f"[FREE] Score calcolati: {scores['punteggio_globale']}/100")

    # ── 6. Generazione PDF ──
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

    # ── 7. Generazione HTML interattivo ──
    html_url = ""
    try:
        base_url = settings.APP_BASE_URL.rstrip("/")

        html_content = generate_free_html(
            scraping_data=scraping_data,
            report_markdown=report_markdown,
            company_name=company_name,
            contact_name=contact_name,
            sector=sector,
            city=city,
            checkout_url=checkout_url,
        )
        html_path = save_free_html(html_content, lead_id)
        html_url = f"{base_url}/api/reports/diagnosi/free/{lead_id}"

        logger.info(f"[FREE] HTML generato: {html_url}")
    except Exception as e:
        # L'HTML è un bonus — se fallisce, il PDF è già pronto
        logger.warning(f"[FREE] Errore generazione HTML (non bloccante): {e}")

    # ── 8. Invio email ──
    try:
        email_sent = send_free_report_email(
            to_email=email,
            company_name=company_name,
            contact_name=contact_name,
            pdf_path=pdf_path,
            checkout_url=checkout_url,
            html_url=html_url,
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

    # ── 9. Salvataggio Score su Supabase ──
    try:
        db.table("leads").update({
            "score_gmb": scores["score_gmb"], 
            "score_social": scores["score_social"],
            "score_sito_web": scores["score_sito_web"], 
            "score_seo": scores["score_seo"],
            "score_competitivo": scores["score_competitvo"] if "score_competitvo" in scores else scores["score_competitivo"], 
            "score_totale": scores["punteggio_globale"],
        }).eq("id", lead_id).execute()
    except Exception as e:
        logger.warning(f"[FREE] Errore salvataggio score DB: {e}")

    # ── 9. Insert in tabella reports (Fix 4: FK retry) ──
    try:
        # Verifica che il lead esista prima di inserire il report
        max_retries = 3
        for attempt in range(max_retries):
            check = db.table("leads").select("id").eq("id", lead_id).execute()
            if check.data:
                break
            logger.warning(f"[FREE] Lead {lead_id} non ancora in DB, retry {attempt+1}/{max_retries}")
            time.sleep(2)
        else:
            logger.warning(f"[FREE] Lead {lead_id} non trovato dopo {max_retries} retry — skip insert reports")
            check = None

        if check and check.data:
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
                "html_url": html_url,
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
        "html_url": html_url,
        "checkout_url": checkout_url,
    }
