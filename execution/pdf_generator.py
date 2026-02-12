"""
DigIdentity Engine — Generazione PDF dai report Markdown.

Converte i report Markdown in PDF professionali con branding DigIdentity.
"""

import logging
import re
import tempfile
from pathlib import Path

from weasyprint import HTML, CSS
import markdown

logger = logging.getLogger(__name__)


# CSS professionale e premium per i report DigIdentity
REPORT_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@700;800;900&display=swap');

@page {
    size: A4;
    margin: 20mm;
    @bottom-right {
        content: "DigIdentity Agency — Pagina " counter(page);
        font-family: 'Inter', sans-serif;
        font-size: 8pt;
        color: #999;
    }
}

@page :first {
    margin: 0;
    @bottom-right { content: none; }
}

body {
    font-family: 'Inter', sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #333;
    margin: 0;
    padding: 0;
}

/* Cover Page Premium */
.cover-page {
    background: linear-gradient(135deg, #000000 0%, #1a1a1a 40%, #F90100 100%);
    color: white;
    height: 297mm;
    width: 210mm;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    page-break-after: always;
}

.cover-page .logo-container {
    margin-bottom: 30mm;
}

.cover-page img.logo {
    width: 250px;
}

.cover-page h1 {
    font-family: 'Poppins', sans-serif;
    font-weight: 900;
    font-size: 38pt;
    margin: 0;
    line-height: 1.1;
    color: white;
    border: none;
    text-transform: uppercase;
}

.cover-page .subtitle {
    font-family: 'Poppins', sans-serif;
    font-weight: 700;
    font-size: 18pt;
    color: #F90100;
    margin: 5mm 0 20mm 0;
}

.cover-page .client-name {
    font-size: 22pt;
    font-weight: 600;
    margin-bottom: 10mm;
}

.cover-page .badge-premium {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid #F90100;
    padding: 3mm 8mm;
    border-radius: 50px;
    font-weight: 700;
    font-size: 10pt;
    letter-spacing: 2px;
}

/* Content Styles */
.content-wrapper {
    padding: 20mm;
}

h1 {
    font-family: 'Poppins', sans-serif;
    font-weight: 900;
    font-size: 24pt;
    color: #000;
    margin-top: 15mm;
    margin-bottom: 8mm;
    border-bottom: 4px solid #F90100;
    padding-bottom: 5px;
    page-break-before: always;
}

h2 {
    font-family: 'Poppins', sans-serif;
    font-weight: 800;
    font-size: 18pt;
    color: #000;
    margin-top: 10mm;
    margin-bottom: 5mm;
}

h3 {
    font-family: 'Poppins', sans-serif;
    font-weight: 700;
    font-size: 14pt;
    color: #F90100;
    margin-top: 8mm;
}

p, li {
    margin-bottom: 4mm;
    text-align: justify;
}

strong {
    font-weight: 700;
    color: #000;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 8mm 0;
    page-break-inside: avoid;
}

th {
    background-color: #F90100;
    color: white;
    padding: 4mm;
    text-align: left;
    font-family: 'Poppins', sans-serif;
    font-size: 10pt;
}

td {
    padding: 3mm 4mm;
    border-bottom: 1px solid #eee;
    font-size: 10pt;
}

tr:nth-child(even) {
    background-color: #f9f9f9;
}

/* Score Badges */
.score-badge {
    display: inline-block;
    padding: 1mm 3mm;
    border-radius: 4px;
    font-weight: 700;
    font-size: 9pt;
    color: white;
}
.score-high { background-color: #10B981; }
.score-medium { background-color: #F59E0B; }
.score-low { background-color: #EF4444; }

/* Callout Boxes */
.tip-box {
    background-color: #fff9e6;
    border-left: 5px solid #F59E0B;
    padding: 5mm;
    margin: 5mm 0;
    page-break-inside: avoid;
}

.ai-box {
    background-color: #fdf2f2;
    border-left: 5px solid #F90100;
    padding: 5mm;
    margin: 5mm 0;
    page-break-inside: avoid;
}

/* Page Breaks */
.page-break { page-break-after: always; }
"""

def markdown_to_pdf(
    markdown_text: str,
    output_path: str,
    report_type: str = "free",
    company_name: str = "",
) -> str:
    """
    Converte un report Markdown in PDF professionale DigIdentity.
    """
    import datetime
    
    logger.info(f"🎨 Generazione PDF {report_type} per {company_name}: {output_path}")

    # Converti Markdown → HTML
    md_extensions = ["tables", "fenced_code", "nl2br", "sane_lists"]
    html_body = markdown.markdown(markdown_text, extensions=md_extensions)

    # Titoli basati sul tipo
    report_title = "DIAGNOSI DIGITALE" if report_type == "free" else "PIANO STRATEGICO AI"
    report_badge = "VERSIONE GRATUITA" if report_type == "free" else "REPORT PREMIUM"
    
    logo_url = "https://digidentityagency.it/wp-content/uploads/2023/05/digidentity_agency_light_removebg.png"
    today = datetime.date.today().strftime("%d/%m/%Y")

    # Gestione Score Badges nel testo HTML (sostituzione dinamica se presente)
    # Esempio: cercate Punteggio: 85/100 e trasformate in badge
    def repl_score(match):
        score = int(match.group(1))
        cls = "score-high" if score >= 70 else "score-medium" if score >= 40 else "score-low"
        return f'<span class="score-badge {cls}">{score}/100</span>'
    
    html_body = re.sub(r'Punteggio:\s*(\d+)/100', repl_score, html_body)

    # HTML completo
    full_html = f"""
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <style>{REPORT_CSS}</style>
    </head>
    <body>
        <div class="cover-page">
            <div class="logo-container">
                <img src="{logo_url}" class="logo" alt="DigIdentity Agency">
            </div>
            <h1>{report_title}</h1>
            <div class="subtitle">Strategia AI & Automazioni</div>
            <div class="client-name">{company_name}</div>
            <div class="badge-premium">{report_badge}</div>
            <div style="margin-top: 40mm; font-size: 10pt; opacity: 0.7;">
                Samatzai (SU) | Generato il {today}
            </div>
        </div>

        <div class="content-wrapper">
            {html_body}
        </div>
    </body>
    </html>
    """

    # Genera PDF
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        html_doc = HTML(string=full_html)
        css_obj = CSS(string=REPORT_CSS)
        html_doc.write_pdf(output_path, stylesheets=[css_obj])
        
        logger.info(f"✅ PDF generato con successo: {output_path}")
    except Exception as e:
        logger.error(f"❌ Errore critico durante write_pdf: {e}")
        raise

    return output_path
