"""DigIdentity Engine — API per download PDF e visualizzazione HTML report."""

import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from app.core.supabase_client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/reports", tags=["reports"])

REPORTS_DIR = Path("/app/reports")


@router.get("/diagnosi/premium/{lead_id}", response_class=HTMLResponse)
async def view_premium_report(lead_id: str):
    """Visualizza il report premium HTML interattivo."""
    # Cerca il file HTML
    html_paths = [
        REPORTS_DIR / "premium_html" / f"premium_{lead_id}.html",
    ]

    for html_path in html_paths:
        if html_path.exists():
            html_content = html_path.read_text(encoding="utf-8")
            return HTMLResponse(content=html_content)

    # Se non esiste l'HTML, verifica che il lead esista
    db = get_supabase()
    try:
        result = db.table("leads").select("id,nome_azienda,status").eq("id", lead_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Report non trovato")

        lead = result.data[0]
        status = lead.get("status", "")

        if status in ("generating_premium", "scraping"):
            return HTMLResponse(content=_generating_page(lead.get("nome_azienda", "")), status_code=200)
        else:
            raise HTTPException(status_code=404, detail="Report HTML non ancora generato")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore visualizzazione report premium {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Errore interno")


@router.get("/diagnosi/free/{lead_id}", response_class=HTMLResponse)
async def view_free_report(lead_id: str):
    """Visualizza il report free HTML interattivo."""
    html_paths = [
        REPORTS_DIR / "free_html" / f"free_{lead_id}.html",
    ]

    for html_path in html_paths:
        if html_path.exists():
            html_content = html_path.read_text(encoding="utf-8")
            return HTMLResponse(content=html_content)

    db = get_supabase()
    try:
        result = db.table("leads").select("id,nome_azienda,status").eq("id", lead_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Report non trovato")

        lead = result.data[0]
        status = lead.get("status", "")

        if status in ("generating_free", "scraping"):
            return HTMLResponse(content=_generating_page(lead.get("nome_azienda", "")), status_code=200)
        else:
            raise HTTPException(status_code=404, detail="Report HTML non ancora generato")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore visualizzazione report free {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Errore interno")


@router.get("/diagnosi/free/{lead_id}/pdf")
async def download_free_pdf(lead_id: str):
    pdf_path = REPORTS_DIR / "free" / f"free_{lead_id}.pdf"
    if pdf_path.exists():
        return FileResponse(path=str(pdf_path), filename=f"Diagnosi-Digitale-{lead_id}.pdf", media_type="application/pdf")
    raise HTTPException(status_code=404, detail="PDF non trovato")

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


# ── NUOVI ENDPOINT: GEO Audit ──

@router.get("/geo", tags=["geo"])
async def list_geo_audits():
    """Lista tutti i record della tabella geo_audits."""
    db = get_supabase()
    result = db.table("geo_audits").select("*").order("created_at", desc=True).execute()
    return result.data

@router.get("/geo/{audit_id}", tags=["geo"])
async def get_geo_audit(audit_id: str):
    """Dettaglio singolo geo_audit."""
    db = get_supabase()
    result = db.table("geo_audits").select("*").eq("id", audit_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Audit non trovato")
    return result.data[0]

@router.get("/geo/{audit_id}/pdf", tags=["geo"])
async def download_geo_pdf(audit_id: str):
    """FileResponse del PDF del report GEO."""
    db = get_supabase()
    result = db.table("geo_audits").select("pdf_path,url_sito").eq("id", audit_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Audit non trovato")
    
    audit = result.data[0]
    pdf_path = audit.get("pdf_path")
    if not pdf_path or not Path(pdf_path).exists():
        raise HTTPException(status_code=404, detail="File PDF non trovato")
    
    url_sito = audit.get("url_sito", "sito").replace("https://", "").replace("http://", "").replace("/", "_")
    return FileResponse(
        path=pdf_path,
        filename=f"GEO-Report-{url_sito}.pdf",
        media_type="application/pdf"
    )


@router.get("/geo/{audit_id}/view")
async def view_geo_report_html(audit_id: str):
    """Visualizza il report GEO come pagina HTML interattiva."""
    # Cerca il file su disco — non serve Supabase
    geo_html = REPORTS_DIR / "geo" / f"geo_{audit_id}.html"
    if geo_html.exists():
        from fastapi.responses import HTMLResponse
        html_content = geo_html.read_text(encoding="utf-8")
        return HTMLResponse(content=html_content)
    raise HTTPException(status_code=404, detail="Report GEO HTML non trovato")
