from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from uuid import uuid4

from app.core.supabase_client import get_supabase
from app.models.lead import LeadStatus
from app.tasks.free_report_task import task_free_report

import logging
logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/api/lead-workflow")
async def lead_workflow(request: Request):
    data = await request.json()
    db = get_supabase()
    lead_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    website_url = (data.get("sito_web") or "").strip()
    if website_url and not website_url.startswith(("http://", "https://")):
        website_url = f"https://{website_url}"

    # Estrai città e provincia dall'indirizzo completo
    # Es. "Via Roma 15, Sestu, CA" → città="Sestu", provincia="CA"
    indirizzo = (data.get("indirizzo") or "").strip()
    citta = (data.get("citta") or "").strip()
    provincia = (data.get("provincia") or "").strip()
    if indirizzo and not citta:
        parti = [p.strip() for p in indirizzo.split(",")]
        if len(parti) >= 3:
            citta = parti[-2].strip()
            provincia = parti[-1].strip().upper()[:2]
        elif len(parti) == 2:
            citta = parti[-1].strip()
        # Pulisci città: rimuovi CAP (5 cifre) e sigla provincia (2 lettere maiuscole)
        import re
        if citta:
            citta = re.sub(r'\d{5}', '', citta).strip()
            citta = re.sub(r'[A-Z]{2}$', '', citta).strip()

    lead_data = {
        "id": lead_id,
        "nome_azienda": (data.get("nome_azienda") or "").strip(),
        "sito_web": website_url,
        "email": (data.get("email") or "").strip(),
        "nome_contatto": data.get("nome_contatto") or None,
        "telefono": data.get("telefono") or None,
        "settore_attivita": data.get("settore_attivita") or None,
        "indirizzo": indirizzo or None,
        "citta": citta or None,
        "provincia": provincia or "ND",
        "status": LeadStatus.NEW.value,
        "created_at": now,
    }

    try:
        db.table("leads").insert(lead_data).execute()
        logger.info(f"Lead creato: {lead_id} - {lead_data['nome_azienda']} ({lead_data['email']})")
    except Exception as e:
        logger.error(f"Errore inserimento lead su Supabase: {e}")
        raise HTTPException(status_code=500, detail="Errore salvataggio lead")

    try:
        task_result = task_free_report.delay(lead_id)
        logger.info(f"Task free_report lanciato: {task_result.id} per {lead_id}")
        db.table("leads").update({"status": LeadStatus.SCRAPING.value}).eq("id", lead_id).execute()
    except Exception as e:
        logger.error(f"Errore lancio task: {e}")
        db.table("leads").update({"status": LeadStatus.ERROR.value}).eq("id", lead_id).execute()

    return JSONResponse(status_code=201, content={
        "id": lead_id,
        "status": "processing",
        "message": f"Lead per {lead_data['nome_azienda']} creato. Report gratuito in arrivo a {lead_data['email']}.",
    })
