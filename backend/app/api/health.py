"""
DigIdentity Engine — Health Check Endpoint
Endpoint per verificare lo stato dell'applicazione e delle dipendenze.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.config import get_settings
from app.db import get_supabase_client

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    Verifica che l'applicazione sia in esecuzione e che Supabase sia raggiungibile.
    
    Returns:
        dict: Status dell'applicazione e timestamp
    """
    settings = get_settings()
    
    # Test connessione Supabase
    try:
        supabase = get_supabase_client()
        # Prova una query semplice per verificare la connessione
        result = supabase.table("leads").select("id").limit(1).execute()
        supabase_status = "connected"
    except Exception as e:
        supabase_status = f"error: {str(e)}"
    
    return {
        "status": "healthy" if supabase_status == "connected" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "app_name": settings.app_name,
        "version": "1.0.0",
        "services": {
            "supabase": supabase_status,
        }
    }


@router.get("/")
async def root():
    """
    Root endpoint.
    
    Returns:
        dict: Messaggio di benvenuto
    """
    return {
        "message": "DigIdentity Engine API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }
