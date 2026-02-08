"""
DigIdentity Engine — Premium Report Task
Celery task per la pipeline diagnosi premium.
"""

import sys
import os
import asyncio
from celery import shared_task
from typing import Dict, Any

# Aggiungi execution/ al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../execution"))

from scrape_site_deep import scrape_site_deep
from analyze_ai_opportunities import analyze_ai_opportunities
from generate_pdf import generate_pdf_premium
from send_email import send_email_premium_report
from send_whatsapp import send_whatsapp_premium_report

from app.db import get_supabase_client
from app.services.ai_service import generate_premium_report_ai


def run_async(coro):
    """Helper per eseguire coroutine async dentro Celery (sincrono)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def task_premium_report(self, lead_id: str):
    """
    Pipeline completa per generare e inviare il report premium.

    Steps:
    1. Recupera lead + analisi gratuita da DB
    2. Analisi premium aggiuntive (deep site + AI opportunities)
    3. Generazione report AI premium (Claude, 40-50 pagine)
    4. Generazione PDF premium
    5. Invio email + WhatsApp
    6. Aggiornamento status
    """
    print(f"\n{'='*60}")
    print(f"[START] INIZIO PIPELINE DIAGNOSI PREMIUM")
    print(f"   Lead ID: {lead_id}")
    print(f"{'='*60}\n")

    try:
        # Step 1: Recupera lead e analisi gratuita
        print(f"[STEP 1] Recupero dati lead e analisi gratuita...")
        supabase = get_supabase_client()

        response = supabase.table("leads").select("*").eq("id", lead_id).execute()

        if not response.data:
            raise Exception(f"Lead {lead_id} non trovato")

        lead = response.data[0]
        print(f"   [OK] Lead trovato: {lead['nome_azienda']}")

        free_analysis = {
            "analysis_pagespeed": lead.get("analysis_pagespeed"),
            "analysis_serp": lead.get("analysis_serp"),
            "analysis_gmb": lead.get("analysis_gmb"),
            "analysis_social": lead.get("analysis_social"),
            "analysis_competitors": lead.get("analysis_competitors")
        }

        scores = {
            "score_sito_web": lead.get("score_sito_web"),
            "score_seo": lead.get("score_seo"),
            "score_gmb": lead.get("score_gmb"),
            "score_social": lead.get("score_social"),
            "score_competitivo": lead.get("score_competitivo"),
            "score_totale": lead.get("score_totale")
        }

        supabase.table("leads").update({"status": "premium_processing"}).eq("id", lead_id).execute()

        # Step 2: Analisi premium
        print(f"\n[STEP 2] Analisi premium...")

        site_deep_data = None
        ai_opportunities_data = None

        try:
            if lead.get("sito_web"):
                site_deep_data = run_async(scrape_site_deep(lead["sito_web"], max_pages=10))
        except Exception as e:
            print(f"   [WARN] Errore deep site: {e}")

        try:
            ai_opportunities_data = run_async(analyze_ai_opportunities(
                lead["nome_azienda"],
                lead["settore_attivita"],
                lead["citta"],
                {"analysis": free_analysis, "scores": scores}
            ))
        except Exception as e:
            print(f"   [WARN] Errore AI opportunities: {e}")

        premium_analysis = {
            "analysis_site_deep": site_deep_data,
            "analysis_ai_opportunities": ai_opportunities_data
        }

        supabase.table("leads").update(premium_analysis).eq("id", lead_id).execute()
        print(f"   [OK] Analisi premium completate")

        # Step 3: Generazione report AI premium
        print(f"\n[STEP 3] Generazione report AI premium...")

        ai_result = run_async(
            generate_premium_report_ai(lead, free_analysis, premium_analysis, scores)
        )

        if not ai_result.get("success"):
            raise Exception(f"Errore generazione AI: {ai_result.get('error')}")

        sections = ai_result["sections"]
        ai_metadata = ai_result["metadata"]
        print(f"   [OK] Report AI premium generato")

        # Step 4: Generazione PDF premium
        print(f"\n[STEP 4] Generazione PDF premium...")

        pdf_result = generate_pdf_premium(sections, lead, scores)

        if not pdf_result.get("success"):
            raise Exception(f"Errore generazione PDF: {pdf_result.get('error')}")

        pdf_path = pdf_result["filepath"]
        print(f"   [OK] PDF premium generato: {pdf_path}")

        report_data = {
            "lead_id": lead_id,
            "report_type": "premium",
            "pdf_path": pdf_path,
            "ai_model_used": ai_metadata["model"],
            "ai_tokens_used": ai_metadata["total_tokens"],
            "ai_cost_estimated": ai_metadata["cost_usd"],
            "status": "generated"
        }

        supabase.table("reports").insert(report_data).execute()

        # Step 5: Invio email + WhatsApp
        print(f"\n[STEP 5] Invio email e WhatsApp premium...")

        email_result = None
        whatsapp_result = None

        try:
            email_result = run_async(
                send_email_premium_report(
                    lead["email"],
                    lead["nome_contatto"],
                    lead["nome_azienda"],
                    pdf_path
                )
            )
        except Exception as e:
            print(f"   [WARN] Errore email: {e}")
            email_result = {"success": False, "error": str(e)}

        try:
            whatsapp_result = run_async(
                send_whatsapp_premium_report(
                    lead["telefono"],
                    lead["nome_contatto"],
                    lead["nome_azienda"]
                )
            )
        except Exception as e:
            print(f"   [WARN] Errore WhatsApp: {e}")
            whatsapp_result = {"success": False, "error": str(e)}

        if email_result and email_result.get("success"):
            print(f"   [OK] Email premium inviata")

        if whatsapp_result and whatsapp_result.get("success"):
            print(f"   [OK] WhatsApp premium inviato")

        # Step 6: Aggiorna status finale
        from datetime import datetime

        supabase.table("leads").update({
            "status": "converted",
            "premium_sent_at": datetime.now().isoformat()
        }).eq("id", lead_id).execute()

        print(f"\n{'='*60}")
        print(f"[SUCCESS] PIPELINE PREMIUM COMPLETATA!")
        print(f"   Lead: {lead['nome_azienda']}")
        print(f"   Costo AI: ${ai_metadata['cost_usd']:.4f}")
        print(f"   PDF: {pdf_result['file_size_mb']} MB")
        print(f"{'='*60}\n")

        return {
            "success": True,
            "lead_id": lead_id,
            "ai_cost": ai_metadata["cost_usd"],
            "pdf_path": pdf_path
        }

    except Exception as e:
        error_msg = str(e)
        print(f"\n[ERROR] ERRORE PIPELINE PREMIUM: {error_msg}\n")

        try:
            supabase = get_supabase_client()
            supabase.table("leads").update({"status": "error"}).eq("id", lead_id).execute()
        except:
            pass

        if self.request.retries < self.max_retries:
            print(f"[RETRY] Retry {self.request.retries + 1}/{self.max_retries} tra 120s...")
            raise self.retry(exc=e)

        raise
