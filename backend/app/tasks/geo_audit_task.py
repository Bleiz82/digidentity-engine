import asyncio
import logging
from datetime import datetime
from pathlib import Path
from app.core.celery_app import celery_app

from app.core.config import settings
from app.core.supabase_client import get_supabase
from engine.geo_audit import esegui_audit_completo
from engine.report_generator import genera_pdf_report
from execution.send_email import send_geo_report_email

logger = logging.getLogger(__name__)

@celery_app.task(name="app.tasks.geo_audit_task.task_geo_audit", bind=True, max_retries=2, default_retry_delay=60, acks_late=True)
def task_geo_audit(self, audit_id: str):
    """
    Task Celery per eseguire l'audit GEO completo.
    """
    logger.info(f"📋 Avvio task_geo_audit per ID: {audit_id}")
    supabase = get_supabase()
    
    try:
        # 1. Recupero record da Supabase
        result = supabase.table("geo_audits").select("*").eq("id", audit_id).execute()
        if not result.data:
            logger.error(f"❌ Audit {audit_id} non trovato in DB.")
            return {"status": "error", "message": "Audit non trovato"}
            
        audit_data = result.data[0]
        url_sito = audit_data.get("url_sito")
        email_cliente = audit_data.get("email_cliente")
        piano = audit_data.get("piano", "singolo")
        
        # Aggiorno stato in DB
        supabase.table("geo_audits").update({
            "status": "in_progress",
            "started_at": datetime.now().isoformat()
        }).eq("id", audit_id).execute()

        # 2. Esecuzione Audit GEO (Asyncio Loop separato)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            risultati = loop.run_until_complete(esegui_audit_completo(url_sito))
        finally:
            loop.close()
            
        geo_score = risultati.get("geo_score", 0)
        
        # 3. Generazione Report PDF
        pdf_path = genera_pdf_report(
            risultati=risultati,
            output_dir=settings.GEO_REPORT_DIR,
            audit_id=audit_id
        )
        
        pdf_file = Path(pdf_path)
        pdf_size = pdf_file.stat().st_size if pdf_file.exists() else 0

        # 4. Invio Email
        success_email = send_geo_report_email(
            to_email=email_cliente,
            url_sito=url_sito,
            pdf_path=pdf_path,
            piano=piano,
            geo_score=geo_score
        )

        # 5. Aggiornamento finale record su Supabase
        supabase.table("geo_audits").update({
            "status": "completed",
            "geo_score": geo_score,
            "pdf_path": pdf_path,
            "pdf_size_bytes": pdf_size,
            "risultati_json": risultati,
            "email_sent": success_email,
            "completed_at": datetime.now().isoformat()
        }).eq("id", audit_id).execute()
        
        logger.info(f"✅ Audit {audit_id} completato con successo (Score: {geo_score})")
        return {"status": "completed", "score": geo_score}

    except Exception as e:
        logger.error(f"❌ Errore nel task_geo_audit {audit_id}: {str(e)}")
        # Aggiornamento stato di errore su Supabase
        try:
            supabase.table("geo_audits").update({
                "status": "error",
                "error_message": str(e)
            }).eq("id", audit_id).execute()
        except:
            pass
        # Retry logic Celery
        raise self.retry(exc=e)
