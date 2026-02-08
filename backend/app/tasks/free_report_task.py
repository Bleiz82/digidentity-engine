"""
DigIdentity Engine — Free Report Task
Celery task per orchestrare la pipeline completa della diagnosi gratuita.
"""

import sys
import os
import asyncio
from celery import shared_task
from typing import Dict, Any

# Aggiungi execution/ al path per importare gli script
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../execution"))

from scrape_pagespeed import scrape_pagespeed
from scrape_serp import scrape_serp
from scrape_gmb import scrape_gmb
from scrape_social import scrape_social
from scrape_competitors import analyze_competitors
from calculate_scores import calculate_scores
from generate_pdf import generate_pdf_free
from send_email import send_email_free_report
from send_whatsapp import send_whatsapp_free_report

from app.db import get_supabase_client
from app.services.ai_service import generate_free_report_ai


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


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def task_free_report(self, lead_id: str):
    """
    Pipeline completa per generare e inviare il report gratuito.

    Steps:
    1. Recupera dati lead da Supabase
    2. Scraping parallelo (PageSpeed, SERP, GMB, Social)
    3. Analisi competitor (riusa dati SERP)
    4. Calcolo score
    5. Generazione report AI con Claude
    6. Generazione PDF
    7. Invio email + WhatsApp
    8. Aggiornamento status lead
    """
    print(f"\n{'='*60}")
    print(f"[START] INIZIO PIPELINE DIAGNOSI GRATUITA")
    print(f"   Lead ID: {lead_id}")
    print(f"{'='*60}\n")

    try:
        # Step 1: Recupera lead da Supabase
        print(f"[STEP 1] Recupero dati lead...")
        supabase = get_supabase_client()

        response = supabase.table("leads").select("*").eq("id", lead_id).execute()

        if not response.data:
            raise Exception(f"Lead {lead_id} non trovato")

        lead = response.data[0]
        print(f"   [OK] Lead trovato: {lead['nome_azienda']}")

        # Aggiorna status
        supabase.table("leads").update({"status": "processing"}).eq("id", lead_id).execute()

        # Step 2: Scraping parallelo
        print(f"\n[STEP 2] Scraping dati...")

        pagespeed_data = None
        serp_data = None
        gmb_data = None
        social_data = None

        # Esegui scraping uno alla volta per evitare problemi asyncio
        try:
            if lead.get("sito_web"):
                pagespeed_data = run_async(scrape_pagespeed(lead["sito_web"]))
        except Exception as e:
            print(f"   [WARN] Errore PageSpeed: {e}")

        try:
            serp_data = run_async(scrape_serp(lead["nome_azienda"], lead["settore_attivita"], lead["citta"]))
        except Exception as e:
            print(f"   [WARN] Errore SERP: {e}")

        try:
            gmb_data = run_async(scrape_gmb(lead["nome_azienda"], lead["citta"]))
        except Exception as e:
            print(f"   [WARN] Errore GMB: {e}")

        try:
            social_data = run_async(scrape_social(
                lead.get("piattaforme_social", []),
                lead["nome_azienda"],
                lead.get("sito_web")
            ))
        except Exception as e:
            print(f"   [WARN] Errore Social: {e}")

        print(f"   [OK] Scraping completato")

        # Step 3: Analisi competitor (riusa dati SERP)
        print(f"\n[STEP 3] Analisi competitor...")
        competitors_data = analyze_competitors(serp_data, gmb_data, lead["nome_azienda"])
        print(f"   [OK] Competitor analysis completata")

        # Salva analisi in DB
        analysis_data = {
            "analysis_pagespeed": pagespeed_data,
            "analysis_serp": serp_data,
            "analysis_gmb": gmb_data,
            "analysis_social": social_data,
            "analysis_competitors": competitors_data
        }

        supabase.table("leads").update(analysis_data).eq("id", lead_id).execute()

        # Step 4: Calcolo score
        print(f"\n[STEP 4] Calcolo score...")
        scores = calculate_scores(
            pagespeed_data,
            serp_data,
            gmb_data,
            social_data,
            competitors_data
        )

        supabase.table("leads").update(scores).eq("id", lead_id).execute()
        print(f"   [OK] Score calcolati e salvati")

        # Aggiorna status
        supabase.table("leads").update({"status": "analysis_complete"}).eq("id", lead_id).execute()

        # Step 5: Generazione report AI
        print(f"\n[STEP 5] Generazione report AI...")

        ai_result = run_async(
            generate_free_report_ai(lead, analysis_data, scores)
        )

        if not ai_result.get("success"):
            raise Exception(f"Errore generazione AI: {ai_result.get('error')}")

        sections = ai_result["sections"]
        ai_metadata = ai_result["metadata"]

        print(f"   [OK] Report AI generato")

        # Step 6: Generazione PDF
        print(f"\n[STEP 6] Generazione PDF...")

        pdf_result = generate_pdf_free(sections, lead, scores)

        if not pdf_result.get("success"):
            raise Exception(f"Errore generazione PDF: {pdf_result.get('error')}")

        pdf_path = pdf_result["filepath"]
        print(f"   [OK] PDF generato: {pdf_path}")

        # Salva metadata report in DB
        report_data = {
            "lead_id": lead_id,
            "report_type": "free",
            "pdf_path": pdf_path,
            "pdf_filename": pdf_result.get("filename", ""),
            "pdf_size_bytes": pdf_result.get("size_bytes", 0),
            "ai_model": ai_metadata.get("model", "unknown"),
            "ai_tokens_input": ai_metadata.get("input_tokens", 0),
            "ai_tokens_output": ai_metadata.get("output_tokens", 0),
            "ai_total_tokens": ai_metadata.get("total_tokens", 0),
            "ai_cost_usd": ai_metadata.get("cost_usd", 0.0),
            "status": "generated"
        }

        supabase.table("reports").insert(report_data).execute()

        # Aggiorna status lead
        supabase.table("leads").update({
            "status": "free_report_generated",
            "report_sent_at": None
        }).eq("id", lead_id).execute()

        # Step 7: Invio email + WhatsApp
        print(f"\n[STEP 7] Invio email e WhatsApp...")

        email_result = None
        whatsapp_result = None

        try:
            email_result = run_async(
                send_email_free_report(
                    lead["email"],
                    lead["nome_contatto"],
                    lead["nome_azienda"],
                    pdf_path,
                    lead_id
                )
            )
        except Exception as e:
            print(f"   [WARN] Errore email: {e}")
            email_result = {"success": False, "error": str(e)}

        try:
            whatsapp_result = run_async(
                send_whatsapp_free_report(
                    lead["telefono"],
                    lead["nome_contatto"],
                    lead["nome_azienda"]
                )
            )
        except Exception as e:
            print(f"   [WARN] Errore WhatsApp: {e}")
            whatsapp_result = {"success": False, "error": str(e)}

        if email_result and email_result.get("success"):
            print(f"   [OK] Email inviata")
        else:
            print(f"   [WARN] Errore email: {email_result.get('error') if email_result else 'N/A'}")

        if whatsapp_result and whatsapp_result.get("success"):
            print(f"   [OK] WhatsApp inviato")
        else:
            print(f"   [WARN] Errore WhatsApp: {whatsapp_result.get('error') if whatsapp_result else 'N/A'}")

        # Step 8: Aggiorna status finale
        from datetime import datetime

        supabase.table("leads").update({
            "status": "free_report_sent",
            "report_sent_at": datetime.now().isoformat()
        }).eq("id", lead_id).execute()

        print(f"\n{'='*60}")
        print(f"[SUCCESS] PIPELINE COMPLETATA CON SUCCESSO!")
        print(f"   Lead: {lead['nome_azienda']}")
        print(f"   Costo AI: ${ai_metadata['cost_usd']:.4f}")
        print(f"   PDF: {pdf_result['file_size_mb']} MB")
        print(f"{'='*60}\n")

        return {
            "success": True,
            "lead_id": lead_id,
            "nome_azienda": lead["nome_azienda"],
            "ai_cost": ai_metadata["cost_usd"],
            "pdf_path": pdf_path,
            "email_sent": email_result.get("success") if email_result else False,
            "whatsapp_sent": whatsapp_result.get("success") if whatsapp_result else False
        }

    except Exception as e:
        error_msg = str(e)
        print(f"\n[ERROR] ERRORE PIPELINE: {error_msg}\n")

        # Aggiorna status a error
        try:
            supabase = get_supabase_client()
            supabase.table("leads").update({
                "status": "error"
            }).eq("id", lead_id).execute()
        except:
            pass

        # Retry se possibile
        if self.request.retries < self.max_retries:
            print(f"[RETRY] Retry {self.request.retries + 1}/{self.max_retries} tra 60s...")
            raise self.retry(exc=e)

        raise
