"""
DigIdentity Engine — Lead Workflow API
Endpoint per ricevere lead dal form e avviare la pipeline di diagnosi gratuita.
"""

from fastapi import APIRouter, HTTPException, Request
from app.models.lead import LeadInput, LeadResponse
from app.services.lead_service import create_lead, update_lead_status
from app.config import get_settings

router = APIRouter()


@router.post("/lead-workflow", response_model=LeadResponse)
async def submit_lead(lead: LeadInput, request: Request):
    """
    Riceve i dati del lead dal form a 4 step e avvia la pipeline di diagnosi gratuita.
    
    Flusso:
    1. Validazione automatica tramite Pydantic (LeadInput)
    2. Deduplicazione: controlla se email già esistente
    3. Salvataggio in Supabase con status = "new"
    4. Trigger task Celery per pipeline gratuita (TODO: implementare in Fase 2)
    5. Aggiorna status a "processing"
    6. Restituisce workflow_id e redirect URL
    
    Args:
        lead: Dati del lead validati
        request: Request FastAPI per estrarre IP e user agent
        
    Returns:
        LeadResponse: Conferma accettazione con workflow_id e redirect
        
    Raises:
        HTTPException: 422 se validazione fallisce, 503 se Supabase non raggiungibile
    """
    settings = get_settings()
    
    try:
        # Aggiungi tracking info dal request
        lead.ip_address = request.client.host if request.client else None
        lead.user_agent = request.headers.get("user-agent")
        
        print(f"[LEAD] Ricevuto nuovo lead: {lead.email} ({lead.nome_azienda})")
        
        # Salva lead in database (con deduplicazione automatica)
        saved_lead = await create_lead(lead)
        lead_id = saved_lead["id"]
        
        print(f"[DB] Lead salvato con ID: {lead_id}")
        
        # Trigger Celery task per pipeline gratuita
        from app.tasks.free_report_task import task_free_report
        task = task_free_report.delay(lead_id)
        print(f"   Celery Task ID: {task.id}")
        
        print(f"[PIPELINE] Pipeline gratuita avviata per lead {lead_id}")
        
        # Restituisci risposta
        return LeadResponse(
            status="accepted",
            workflow_id=lead_id,
            redirect=f"/diagnosi-completata?id={lead_id}",
            message="Diagnosi in elaborazione. Riceverai il report via email tra pochi minuti."
        )
    
    except Exception as e:
        print(f"[ERROR] Errore nel processing del lead: {str(e)}")
        
        # Se errore Supabase, 503
        if "supabase" in str(e).lower() or "connection" in str(e).lower():
            raise HTTPException(
                status_code=503,
                detail="Servizio temporaneamente non disponibile. Riprova tra qualche minuto."
            )
        
        # Altri errori, 500
        raise HTTPException(
            status_code=500,
            detail=f"Errore interno del server: {str(e)}"
        )
