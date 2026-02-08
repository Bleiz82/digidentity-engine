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


# CSS professionale per i report
REPORT_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

@page {
    size: A4;
    margin: 25mm 20mm 25mm 20mm;

    @top-right {
        content: "DigIdentity Engine";
        font-family: 'Inter', sans-serif;
        font-size: 8pt;
        color: #94a3b8;
    }

    @bottom-center {
        content: counter(page) " / " counter(pages);
        font-family: 'Inter', sans-serif;
        font-size: 8pt;
        color: #94a3b8;
    }
}

@page :first {
    margin-top: 0;
    @top-right { content: none; }
    @bottom-center { content: none; }
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 10.5pt;
    line-height: 1.7;
    color: #1e293b;
    max-width: 100%;
}

/* Cover Page */
.cover-page {
    page-break-after: always;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    text-align: center;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
    color: white;
    margin: -25mm -20mm;
    padding: 40mm 30mm;
}

.cover-page h1 {
    font-size: 28pt;
    font-weight: 700;
    margin-bottom: 8mm;
    color: white;
    border: none;
}

.cover-page .subtitle {
    font-size: 14pt;
    color: #94a3b8;
    margin-bottom: 15mm;
}

.cover-page .company-name {
    font-size: 20pt;
    font-weight: 600;
    color: #818cf8;
    margin-bottom: 5mm;
}

.cover-page .date {
    font-size: 11pt;
    color: #64748b;
    margin-top: 20mm;
}

.cover-page .badge {
    display: inline-block;
    background: rgba(99, 102, 241, 0.2);
    border: 1px solid rgba(99, 102, 241, 0.4);
    color: #a5b4fc;
    padding: 4mm 8mm;
    border-radius: 20px;
    font-size: 10pt;
    font-weight: 500;
    margin-top: 5mm;
}

/* Headings */
h1 {
    font-size: 22pt;
    font-weight: 700;
    color: #0f172a;
    margin-top: 20mm;
    margin-bottom: 6mm;
    padding-bottom: 3mm;
    border-bottom: 2px solid #6366f1;
    page-break-after: avoid;
}

h2 {
    font-size: 16pt;
    font-weight: 600;
    color: #1e293b;
    margin-top: 12mm;
    margin-bottom: 4mm;
    page-break-after: avoid;
}

h3 {
    font-size: 13pt;
    font-weight: 600;
    color: #334155;
    margin-top: 8mm;
    margin-bottom: 3mm;
    page-break-after: avoid;
}

h4 {
    font-size: 11pt;
    font-weight: 600;
    color: #475569;
    margin-top: 5mm;
    margin-bottom: 2mm;
}

/* Paragraphs */
p {
    margin-bottom: 4mm;
    text-align: justify;
    orphans: 3;
    widows: 3;
}

/* Lists */
ul, ol {
    margin-left: 6mm;
    margin-bottom: 4mm;
}

li {
    margin-bottom: 2mm;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 5mm 0;
    font-size: 9.5pt;
    page-break-inside: avoid;
}

th {
    background: #1e293b;
    color: white;
    padding: 3mm 4mm;
    text-align: left;
    font-weight: 600;
    font-size: 9pt;
}

td {
    padding: 2.5mm 4mm;
    border-bottom: 1px solid #e2e8f0;
}

tr:nth-child(even) {
    background: #f8fafc;
}

/* Score boxes */
.score-box {
    display: inline-block;
    padding: 2mm 4mm;
    border-radius: 4px;
    font-weight: 600;
    font-size: 10pt;
}

.score-high { background: #dcfce7; color: #166534; }
.score-medium { background: #fef3c7; color: #92400e; }
.score-low { background: #fecaca; color: #991b1b; }

/* Blockquotes (used for callouts) */
blockquote {
    background: #eff6ff;
    border-left: 4px solid #6366f1;
    padding: 4mm 5mm;
    margin: 4mm 0;
    font-style: normal;
    color: #1e40af;
    page-break-inside: avoid;
}

/* Code blocks (for technical details) */
code {
    background: #f1f5f9;
    padding: 1mm 2mm;
    border-radius: 3px;
    font-size: 9pt;
    font-family: 'JetBrains Mono', monospace;
}

pre {
    background: #1e293b;
    color: #e2e8f0;
    padding: 4mm;
    border-radius: 6px;
    overflow-x: auto;
    font-size: 8.5pt;
    page-break-inside: avoid;
}

pre code {
    background: none;
    padding: 0;
    color: inherit;
}

/* Horizontal rule */
hr {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 8mm 0;
}

/* Strong/Bold for emphasis */
strong {
    font-weight: 600;
    color: #0f172a;
}

/* Links */
a {
    color: #6366f1;
    text-decoration: none;
}

/* CTA Box (for free report) */
.cta-box {
    background: linear-gradient(135deg, #eff6ff, #e0e7ff);
    border: 2px solid #6366f1;
    border-radius: 8px;
    padding: 6mm;
    margin: 8mm 0;
    text-align: center;
    page-break-inside: avoid;
}

.cta-box h3 {
    color: #4338ca;
    margin-top: 0;
}
"""


def markdown_to_pdf(
    markdown_text: str,
    output_path: str,
    report_type: str = "free",
    company_name: str = "",
) -> str:
    """
    Converte un report Markdown in PDF professionale.

    Args:
        markdown_text: Il testo del report in formato Markdown
        output_path: Percorso dove salvare il PDF
        report_type: "free" o "premium"
        company_name: Nome dell'azienda per la cover page

    Returns:
        Il percorso del file PDF generato
    """
    import datetime

    logger.info(f"Generazione PDF {report_type} per {company_name}: {output_path}")

    # Converti Markdown → HTML
    md_extensions = [
        "tables",
        "fenced_code",
        "codehilite",
        "toc",
        "nl2br",
        "sane_lists",
    ]
    html_body = markdown.markdown(markdown_text, extensions=md_extensions)

    # Badge per tipo report
    badge = "DIAGNOSI GRATUITA" if report_type == "free" else "REPORT PREMIUM"
    subtitle = (
        "Diagnosi della Presenza Digitale"
        if report_type == "free"
        else "Piano Strategico Digitale Completo"
    )

    today = datetime.date.today().strftime("%d/%m/%Y")

    # HTML completo con cover page
    full_html = f"""
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <title>DigIdentity — {subtitle} — {company_name}</title>
    </head>
    <body>
        <div class="cover-page">
            <h1>DigIdentity Engine</h1>
            <p class="subtitle">{subtitle}</p>
            <p class="company-name">{company_name}</p>
            <span class="badge">{badge}</span>
            <p class="date">Generato il {today}</p>
        </div>

        {html_body}
    </body>
    </html>
    """

    # Genera PDF con WeasyPrint
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    html_doc = HTML(string=full_html)
    css = CSS(string=REPORT_CSS)
    html_doc.write_pdf(output_path, stylesheets=[css])

    file_size = Path(output_path).stat().st_size
    logger.info(f"PDF generato: {output_path} ({file_size / 1024:.1f} KB)")

    return output_path
