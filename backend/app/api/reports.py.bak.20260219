"""DigIdentity Engine — API per download PDF e visualizzazione HTML report."""

import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
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


# ── NUOVI ENDPOINT: Pagine HTML interattive ──

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


def _generating_page(company_name: str) -> str:
    """Pagina di attesa durante la generazione."""
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Generazione in corso — {company_name} | DigIdentity Agency</title>
<meta http-equiv="refresh" content="15">
<style>
  body {{
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: #0a0a0a;
    color: #e0e0e0;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    margin: 0;
    text-align: center;
  }}
  .loader {{
    width: 60px; height: 60px;
    border: 4px solid #222;
    border-top: 4px solid #F90100;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 2rem;
  }}
  @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
  h1 {{ font-size: 1.5rem; color: #F90100; margin-bottom: 0.5rem; }}
  p {{ color: #999; font-size: 0.95rem; line-height: 1.6; }}
  .company {{ color: #fff; font-weight: 700; }}
</style>
</head>
<body>
<div>
  <div class="loader"></div>
  <h1>Stiamo generando la tua diagnosi</h1>
  <p>La Diagnosi Digitale Premium per <span class="company">{company_name}</span><br>
  è in fase di generazione. Ci vogliono circa 2-3 minuti.</p>
  <p style="margin-top: 1rem; font-size: 0.8rem; color: #666;">Questa pagina si aggiorna automaticamente.</p>
</div>
</body>
</html>"""
