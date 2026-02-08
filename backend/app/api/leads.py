"""
DigIdentity Engine — API per la gestione dei lead.

POST /api/leads        → Crea un nuovo lead e avvia la pipeline free
GET  /api/leads/{id}   → Stato del lead
GET  /api/leads        → Lista lead (per dashboard)
"""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from backend.app.core.supabase_client import get_supabase
from backend.app.models.lead import LeadCreate, LeadResponse, LeadStatus
from backend.app.tasks.free_report_task import task_free_report

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.post("/", status_code=201)
async def create_lead(lead: LeadCreate):
    """
    Crea un nuovo lead e avvia automaticamente la pipeline free:
    scraping → AI report → PDF → email con CTA per premium.
    """
    db = get_supabase()
    lead_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    # Normalizza l'URL
    website_url = lead.website_url.strip()
    if not website_url.startswith(("http://", "https://")):
        website_url = f"https://{website_url}"

    lead_data = {
        "id": lead_id,
        "company_name": lead.company_name.strip(),
        "website_url": website_url,
        "email": lead.email,
        "contact_name": lead.contact_name,
        "phone": lead.phone,
        "sector": lead.sector,
        "notes": lead.notes,
        "status": LeadStatus.NEW.value,
        "created_at": now,
    }

    try:
        db.table("leads").insert(lead_data).execute()
        logger.info(f"Lead creato: {lead_id} — {lead.company_name} ({lead.email})")
    except Exception as e:
        logger.error(f"Errore inserimento lead su Supabase: {e}")
        raise HTTPException(status_code=500, detail="Errore salvataggio lead")

    # Lancia il task Celery per la pipeline free
    try:
        task_result = task_free_report.delay(lead_id)
        logger.info(
            f"Task free_report lanciato: task_id={task_result.id} "
            f"per lead_id={lead_id}"
        )

        # Salva il task_id
        db.table("leads").update({
            "status": LeadStatus.SCRAPING.value,
            "celery_free_task_id": task_result.id,
        }).eq("id", lead_id).execute()

    except Exception as e:
        logger.error(f"Errore lancio task free per lead {lead_id}: {e}")
        # Il lead è stato salvato, segna errore
        db.table("leads").update({
            "status": LeadStatus.ERROR.value,
            "error_message": f"Errore lancio task: {str(e)}",
        }).eq("id", lead_id).execute()

    return JSONResponse(
        status_code=201,
        content={
            "id": lead_id,
            "status": "processing",
            "message": (
                f"Lead per {lead.company_name} creato con successo. "
                f"Il report gratuito sarà inviato a {lead.email}."
            ),
        },
    )


@router.get("/{lead_id}")
async def get_lead(lead_id: str):
    """Restituisce lo stato corrente di un lead."""
    db = get_supabase()

    try:
        result = db.table("leads").select("*").eq("id", lead_id).execute()
    except Exception as e:
        logger.error(f"Errore lettura lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Errore database")

    if not result.data:
        raise HTTPException(status_code=404, detail="Lead non trovato")

    return result.data[0]


@router.get("/")
async def list_leads(limit: int = 50, offset: int = 0):
    """Lista dei lead (per dashboard), ordinati per data creazione desc."""
    db = get_supabase()

    try:
        result = (
            db.table("leads")
            .select("*")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return {"leads": result.data, "count": len(result.data)}
    except Exception as e:
        logger.error(f"Errore lista lead: {e}")
        raise HTTPException(status_code=500, detail="Errore database")
