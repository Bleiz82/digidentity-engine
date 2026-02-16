"""DigIdentity Engine — API per download PDF report."""

import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.core.supabase_client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/reports", tags=["reports"])

REPORTS_DIR = Path("/app/reports")


@router.get("/{report_id}/pdf")
async def download_report_pdf(report_id: str):
    """Scarica il PDF di un report dato il report_id."""
    db = get_supabase()
    
    try:
        result = db.table("reports").select("pdf_path,pdf_filename,report_type,lead_id").eq("id", report_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Report non trovato")
        
        report = result.data[0]
        pdf_filename = report.get("pdf_filename", "")
        report_type = report.get("report_type", "free")
        lead_id = report.get("lead_id", "")
        
        # Cerca il PDF nel volume persistente
        possible_paths = [
            REPORTS_DIR / report_type / pdf_filename,
            REPORTS_DIR / report_type / f"{report_type}_{lead_id}.pdf",
            REPORTS_DIR / pdf_filename,
        ]
        
        for pdf_path in possible_paths:
            if pdf_path.exists():
                return FileResponse(
                    path=str(pdf_path),
                    filename=pdf_filename or f"{report_type}_{lead_id}.pdf",
                    media_type="application/pdf",
                )
        
        raise HTTPException(status_code=404, detail="File PDF non trovato sul server")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore download PDF {report_id}: {e}")
        raise HTTPException(status_code=500, detail="Errore interno")
