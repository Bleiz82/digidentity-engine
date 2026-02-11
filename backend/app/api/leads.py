import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from backend.app.core.supabase_client import get_supabase
from backend.app.models.lead import LeadCreate, LeadStatus
from backend.app.tasks.free_report_task import task_free_report

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.post("/", status_code=201)
async def create_lead(lead: LeadCreate):
    db = get_supabase()
    lead_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    website_url = lead.website_url.strip()
    if not website_url.startswith(("http://", "https://")):
        website_url = f"https://{website_url}"

    lead_data = {
        "id": lead_id,
        "nome_azienda": lead.company_name.strip(),
        "sito_web": website_url,
        "email": lead.email,
        "nome_contatto": lead.contact_name or "",
        "telefono": getattr(lead, "telefono", "") or lead.phone or "",
        "settore_attivita": lead.sector or "",
        "citta": getattr(lead, "citta", "") or "",
        "provincia": getattr(lead, "provincia", "") or "",
        "status": LeadStatus.NEW.value,
        "created_at": now,
    }

    # Rimuovi campi vuoti che non sono obbligatori
    for key in ["nome_contatto", "telefono", "settore_attivita", "citta", "provincia"]:
        if not lead_data[key]:
            lead_data[key] = None

    try:
        db.table("leads").insert(lead_data).execute()
        logger.info(f"Lead creato: {lead_id} - {lead.company_name} ({lead.email})")
    except Exception as e:
        logger.error(f"Errore inserimento lead su Supabase: {e}")
        raise HTTPException(status_code=500, detail="Errore salvataggio lead")

    try:
        task_result = task_free_report.delay(lead_id)
        logger.info(f"Task free_report lanciato: task_id={task_result.id} per lead_id={lead_id}")
        db.table("leads").update({"status": LeadStatus.SCRAPING.value}).eq("id", lead_id).execute()
    except Exception as e:
        logger.error(f"Errore lancio task free per lead {lead_id}: {e}")
        db.table("leads").update({"status": LeadStatus.ERROR.value}).eq("id", lead_id).execute()

    return JSONResponse(status_code=201, content={
        "id": lead_id,
        "status": "processing",
        "message": f"Lead per {lead.company_name} creato. Report gratuito in arrivo a {lead.email}.",
    })


@router.get("/{lead_id}")
async def get_lead(lead_id: str):
    db = get_supabase()
    try:
        result = db.table("leads").select("*").eq("id", lead_id).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Errore database")
    if not result.data:
        raise HTTPException(status_code=404, detail="Lead non trovato")
    return result.data[0]


@router.get("/")
async def list_leads(limit: int = 50, offset: int = 0):
    db = get_supabase()
    try:
        result = db.table("leads").select("*").order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        return {"leads": result.data, "count": len(result.data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Errore database")
