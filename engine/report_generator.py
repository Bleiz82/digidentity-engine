"""
DigIdentity Engine — GEO Report Generator
Genera il PDF del GEO Audit e restituisce il percorso del file.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from loguru import logger
from jinja2 import Environment, FileSystemLoader

try:
    from weasyprint import HTML
    WEASYPRINT_DISPONIBILE = True
except ImportError:
    WEASYPRINT_DISPONIBILE = False
    logger.warning("⚠️ WeasyPrint non disponibile — installare con: pip install weasyprint")

# Configurazione Jinja2
TEMPLATE_DIR = Path(__file__).parent / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))

def calcola_barra(score):
    """Filtro Jinja2 per calcolare la larghezza della barra di progresso."""
    return f"width: {max(min(score, 100), 0)}%"

env.filters["calcola_barra"] = calcola_barra

def load_labels():
    """Carica le etichette del report da JSON."""
    labels_path = Path(__file__).parent / "data" / "copy" / "report_labels.json"
    if labels_path.exists():
        try:
            with open(labels_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Errore nel caricamento dei labels: {e}")
    
    # Default fallback
    return {
        "intestazione": {"powered_by": ""},
        "moduli": {
            "citabilita": {"nome": "Citabilità AI", "peso": "25%", "descrizione": "Ottimizzazione per citazioni LLM"},
            "crawler": {"nome": "Accesso Crawler AI", "peso": "15%", "descrizione": "Visibilità per bot AI"},
            "brand": {"nome": "Brand Authority", "peso": "20%", "descrizione": "Presenza brand fonti terze"},
            "schema": {"nome": "Dati Strutturati", "peso": "10%", "descrizione": "Markup semantico"},
            "contenuto": {"nome": "Qualità Contenuto E-E-A-T", "peso": "20%", "descrizione": "Affidabilità e autorevolezza"}
        }
    }

def get_giudizio(score):
    """Restituisce il giudizio visuale in base allo score."""
    if score >= 85:
        return {"colore": "#10B981", "emoji": "🏆", "etichetta": "ECCELLENTE"}
    elif score >= 70:
        return {"colore": "#10B981", "emoji": "✅", "etichetta": "OTTIMO"}
    elif score >= 50:
        return {"colore": "#F59E0B", "emoji": "⚠️", "etichetta": "DISCRETO"}
    elif score >= 30:
        return {"colore": "#F97316", "emoji": "🟠", "etichetta": "SCARSO"}
    else:
        return {"colore": "#EF4444", "emoji": "🚨", "etichetta": "CRITICO"}

def genera_pdf_report(
    risultati: dict,
    output_dir: str = "/app/reports/geo",
    audit_id: str = "",
) -> str:
    """
    Genera il PDF del GEO Audit Report e restituisce il percorso del file.
    """
    logger.info(f"📄 Generazione PDF GEO Report per: {risultati.get('url', 'N/A')}")

    # Crea directory se non esiste
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Nome file
    url = risultati.get("url", "sito")
    import re
    dominio = re.sub(r'^https?://(www\.)?', '', url).split('/')[0]
    dominio = re.sub(r'[^\w\-]', '_', dominio)[:50]
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = f"_{audit_id[:8]}" if audit_id else f"_{timestamp}"
    filename = f"GEO-Report-{dominio}{suffix}.pdf"
    pdf_path = output_path / filename

    # Preparazione dati per Jinja2
    template = env.get_template("report_ita.html")
    
    geo_score = risultati.get("geo_score", 0)
    data_raw = risultati.get("data_analisi", datetime.now().isoformat())
    try:
        data_analisi = datetime.fromisoformat(data_raw).strftime("%d/%m/%Y alle %H:%M")
    except:
        data_analisi = data_raw

    labels = load_labels()
    giudizio = get_giudizio(geo_score)

    render_data = {
        "url_sito": url,
        "data_analisi": data_analisi,
        "email_cliente": risultati.get("email_cliente", "Admin"),
        "geo_score": geo_score,
        "moduli": risultati.get("moduli", {}),
        "priorita": risultati.get("priorita", []),
        "giudizio": giudizio,
        "labels": labels,
        "calcola_barra": calcola_barra
    }

    html_content = template.render(**render_data)

    if WEASYPRINT_DISPONIBILE:
        try:
            HTML(string=html_content).write_pdf(str(pdf_path))
            logger.success(f"✅ PDF generato con template: {pdf_path}")
            return str(pdf_path)
        except Exception as e:
            logger.error(f"❌ Errore WeasyPrint: {e}")
    
    # Fallback: salva HTML
    html_path = pdf_path.with_suffix(".html")
    html_path.write_text(html_content, encoding="utf-8")
    logger.info(f"📄 HTML salvato come fallback: {html_path}")
    return str(html_path)
