"""
DigIdentity Engine — GEO Report Generator
Genera il PDF del GEO Audit e restituisce il percorso del file.
(L'invio email è gestito dal task Celery tramite execution/send_email.py)
"""

import os
import json
from pathlib import Path
from datetime import datetime
from loguru import logger

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_DISPONIBILE = True
except ImportError:
    WEASYPRINT_DISPONIBILE = False
    logger.warning("⚠️ WeasyPrint non disponibile — installare con: pip install weasyprint")


def genera_pdf_report(
    risultati: dict,
    output_dir: str = "/app/reports/geo",
    audit_id: str = "",
) -> str:
    """
    Genera il PDF del GEO Audit Report e restituisce il percorso del file.

    Args:
        risultati: Dizionario con i risultati dell'audit (output di esegui_audit_completo)
        output_dir: Directory dove salvare il PDF
        audit_id: UUID dell'audit (usato nel nome file)

    Returns:
        str: Percorso assoluto del file PDF generato
    """
    logger.info(f"📄 Generazione PDF GEO Report per: {risultati.get('url', 'N/A')}")

    # Crea directory se non esiste
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Nome file
    url = risultati.get("url", "sito")
    dominio = _estrai_dominio(url)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = f"_{audit_id[:8]}" if audit_id else f"_{timestamp}"
    filename = f"GEO-Report-{dominio}{suffix}.pdf"
    pdf_path = output_path / filename

    # Genera HTML del report
    html_content = _genera_html_report(risultati)

    if WEASYPRINT_DISPONIBILE:
        try:
            HTML(string=html_content).write_pdf(str(pdf_path))
            logger.success(f"✅ PDF generato: {pdf_path}")
        except Exception as e:
            logger.error(f"❌ Errore WeasyPrint: {e}")
            # Fallback: salva HTML
            html_path = pdf_path.with_suffix(".html")
            html_path.write_text(html_content, encoding="utf-8")
            logger.info(f"📄 HTML salvato come fallback: {html_path}")
            return str(html_path)
    else:
        # Salva HTML se WeasyPrint non disponibile
        html_path = pdf_path.with_suffix(".html")
        html_path.write_text(html_content, encoding="utf-8")
        logger.warning(f"⚠️ WeasyPrint non disponibile. HTML salvato: {html_path}")
        return str(html_path)

    return str(pdf_path)


def _estrai_dominio(url: str) -> str:
    """Estrae il dominio dall'URL per usarlo nel nome file."""
    import re
    url = re.sub(r'^https?://(www\.)?', '', url)
    url = url.split('/')[0]
    url = re.sub(r'[^\w\-]', '_', url)
    return url[:50]  # limita lunghezza


def _colore_score(score: int) -> str:
    """Restituisce il colore CSS in base allo score."""
    if score >= 70:
        return "#22c55e"   # verde
    elif score >= 50:
        return "#f59e0b"   # giallo
    else:
        return "#ef4444"   # rosso


def _label_score(score: int) -> str:
    """Restituisce un'etichetta testuale per lo score."""
    if score >= 70:
        return "BUONO"
    elif score >= 50:
        return "DISCRETO"
    elif score >= 30:
        return "SCARSO"
    else:
        return "CRITICO"


def _genera_html_report(risultati: dict) -> str:
    """Genera l'HTML completo del GEO Report."""
    url = risultati.get("url", "N/A")
    geo_score = risultati.get("geo_score", 0)
    data_analisi = risultati.get("data_analisi", datetime.now().isoformat())
    moduli = risultati.get("moduli", {})
    priorita = risultati.get("priorita", [])

    colore_geo = _colore_score(geo_score)
    label_geo = _label_score(geo_score)

    # Sezioni moduli
    sezioni_html = ""
    moduli_info = [
        ("citabilita", "📝 Citabilità AI", "Quanto il contenuto è ottimizzato per le citazioni AI"),
        ("crawler", "🤖 Accesso Crawler AI", "Robots.txt e file llms.txt"),
        ("brand", "🏷️ Brand Authority", "Presenza sulle piattaforme citate dalle AI"),
        ("schema", "🗂️ Dati Strutturati", "Schema JSON-LD e markup semantico"),
        ("contenuto", "✍️ Qualità Contenuto E-E-A-T", "Experience, Expertise, Authority, Trust"),
    ]

    for chiave, nome, descrizione in moduli_info:
        modulo = moduli.get(chiave, {})
        score = modulo.get("score", 0)
        colore = _colore_score(score)
        label = _label_score(score)
        raccomandazioni = modulo.get("raccomandazioni", [])
        errore = modulo.get("errore", "")

        recs_html = ""
        if errore:
            recs_html = f'<p class="error">⚠️ Errore durante l\'analisi: {errore}</p>'
        elif raccomandazioni:
            recs_items = "".join(f"<li>{r}</li>" for r in raccomandazioni[:5])
            recs_html = f"<ul class='recs'>{recs_items}</ul>"
        else:
            recs_html = '<p class="ok">✅ Nessuna criticità rilevata in questo modulo.</p>'

        sezioni_html += f"""
        <div class="modulo">
            <div class="modulo-header">
                <div>
                    <h3>{nome}</h3>
                    <p class="modulo-desc">{descrizione}</p>
                </div>
                <div class="score-badge" style="background:{colore}20; border-color:{colore}; color:{colore};">
                    <span class="score-num">{score}</span>
                    <span class="score-label">/100 — {label}</span>
                </div>
            </div>
            {recs_html}
        </div>
        """

    # Priorità di intervento
    priorita_html = ""
    if priorita:
        colori_priorita = {"CRITICA": "#ef4444", "ALTA": "#f59e0b", "MEDIA": "#3b82f6", "BASSA": "#22c55e"}
        for p in priorita[:6]:
            colore_p = colori_priorita.get(p.get("priorita", "MEDIA"), "#3b82f6")
            priorita_html += f"""
            <div class="priorita-item" style="border-left: 4px solid {colore_p};">
                <span class="priorita-badge" style="background:{colore_p}20; color:{colore_p};">{p.get("priorita", "")}</span>
                <strong>{p.get("categoria", "")}</strong>
                <p>{p.get("problema", "")}</p>
                <p class="azione">→ {p.get("azione", "")}</p>
                <p class="impatto">📈 Impatto stimato: {p.get("impatto_stimato", "")}</p>
            </div>
            """
    else:
        priorita_html = '<p class="ok">✅ Nessuna priorità critica identificata.</p>'

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <title>GEO Audit Report — {url}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', Arial, sans-serif; background: #0f172a; color: #e2e8f0; font-size: 13px; line-height: 1.6; }}
        .page {{ max-width: 800px; margin: 0 auto; padding: 40px 30px; }}

        /* Header */
        .header {{ background: linear-gradient(135deg, #0f172a, #1e293b); border: 1px solid #0ea5e9; border-radius: 16px; padding: 40px; margin-bottom: 30px; text-align: center; }}
        .header-logo {{ font-size: 12px; letter-spacing: 3px; color: #0ea5e9; font-weight: 700; margin-bottom: 8px; }}
        .header h1 {{ font-size: 26px; font-weight: 800; color: #f8fafc; margin-bottom: 6px; }}
        .header .url {{ font-size: 14px; color: #94a3b8; margin-bottom: 20px; }}
        .data {{ font-size: 11px; color: #64748b; }}

        /* GEO Score centrale */
        .geo-score-box {{ background: #1e293b; border: 2px solid {colore_geo}; border-radius: 16px; padding: 30px; margin-bottom: 30px; text-align: center; }}
        .geo-score-title {{ font-size: 12px; letter-spacing: 2px; color: #94a3b8; margin-bottom: 10px; }}
        .geo-score-num {{ font-size: 72px; font-weight: 800; color: {colore_geo}; line-height: 1; }}
        .geo-score-label {{ font-size: 16px; color: {colore_geo}; font-weight: 600; margin-top: 6px; }}
        .geo-score-sub {{ font-size: 12px; color: #64748b; margin-top: 8px; }}

        /* Sezione */
        .section-title {{ font-size: 11px; letter-spacing: 2px; color: #0ea5e9; font-weight: 700; margin: 30px 0 15px; text-transform: uppercase; }}

        /* Moduli */
        .modulo {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; margin-bottom: 14px; }}
        .modulo-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; gap: 16px; }}
        .modulo-header h3 {{ font-size: 15px; font-weight: 700; color: #f1f5f9; margin-bottom: 3px; }}
        .modulo-desc {{ font-size: 11px; color: #64748b; }}
        .score-badge {{ border: 2px solid; border-radius: 10px; padding: 8px 14px; text-align: center; min-width: 110px; flex-shrink: 0; }}
        .score-num {{ font-size: 24px; font-weight: 800; display: block; }}
        .score-label {{ font-size: 10px; font-weight: 600; }}
        .recs {{ padding-left: 18px; }}
        .recs li {{ font-size: 12px; color: #94a3b8; margin-bottom: 4px; }}
        .ok {{ font-size: 12px; color: #22c55e; }}
        .error {{ font-size: 12px; color: #f59e0b; }}

        /* Priorità */
        .priorita-item {{ background: #1e293b; border-radius: 10px; padding: 16px 16px 16px 20px; margin-bottom: 12px; }}
        .priorita-badge {{ font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 4px; margin-bottom: 6px; display: inline-block; letter-spacing: 1px; }}
        .priorita-item p {{ font-size: 12px; color: #94a3b8; margin-top: 4px; }}
        .azione {{ color: #cbd5e1 !important; font-weight: 500; }}
        .impatto {{ color: #0ea5e9 !important; }}

        /* Footer */
        .footer {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 24px; margin-top: 30px; text-align: center; }}
        .footer p {{ font-size: 11px; color: #64748b; margin-bottom: 4px; }}
        .footer strong {{ color: #0ea5e9; }}
    </style>
</head>
<body>
<div class="page">
    <!-- Header -->
    <div class="header">
        <div class="header-logo">DIGIDENTITY AGENCY — GEO AUDIT</div>
        <h1>GEO Audit Report</h1>
        <div class="url">{url}</div>
        <div class="data">Analisi eseguita il {datetime.fromisoformat(data_analisi).strftime("%d/%m/%Y alle %H:%M")}</div>
    </div>

    <!-- GEO Score Complessivo -->
    <div class="geo-score-box">
        <div class="geo-score-title">GEO SCORE COMPLESSIVO</div>
        <div class="geo-score-num">{geo_score}</div>
        <div class="geo-score-label">{label_geo}</div>
        <div class="geo-score-sub">Su una scala da 0 a 100 — misura quanto il sito è ottimizzato per le AI</div>
    </div>

    <!-- Dettaglio Moduli -->
    <div class="section-title">📊 Analisi per Modulo</div>
    {sezioni_html}

    <!-- Piano di Priorità -->
    <div class="section-title">🎯 Piano di Intervento</div>
    {priorita_html}

    <!-- Footer -->
    <div class="footer">
        <p><strong>DigIdentity Agency</strong> — Specialisti AI & Automazioni per MPMI</p>
        <p>Via Dettori 3, Samatzai (SU), Sardegna | info@digidentityagency.it</p>
        <p>digidentityagency.it | Questo report è generato automaticamente dall'AI DigIdentity Engine</p>
    </div>
</div>
</body>
</html>"""
