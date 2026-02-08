"""
DigIdentity Engine — PDF Generator
Converte HTML in PDF usando WeasyPrint.
Versione 3.0 — Template professionali con grafici CSS, page-break per sezione.
"""

import os
from typing import Dict, Any
from weasyprint import HTML
from datetime import datetime


# ══════════════════════════════════════════════════════════════
# CSS CONDIVISO — Componenti visivi riutilizzabili
# ══════════════════════════════════════════════════════════════

SHARED_CSS = """
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800;900&family=Inter:wght@300;400;500;600;700&display=swap');

    * { box-sizing: border-box; }

    body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #1a1a1a;
        margin: 0;
        padding: 0;
        font-size: 11pt;
        line-height: 1.7;
    }

    h1, h2, h3, h4 {
        font-family: 'Poppins', sans-serif;
        color: #F90100;
        font-weight: 800;
        page-break-after: avoid;
    }
    h1 { font-size: 26pt; margin-bottom: 10pt; }
    h2 { font-size: 19pt; margin-top: 25pt; margin-bottom: 12pt; border-bottom: 3px solid #F90100; padding-bottom: 8pt; }
    h3 { font-size: 14pt; margin-top: 18pt; margin-bottom: 8pt; color: #333; }
    h4 { font-size: 12pt; margin-top: 12pt; margin-bottom: 6pt; color: #444; }

    p { margin-bottom: 8pt; text-align: justify; orphans: 3; widows: 3; }

    /* ── Tabelle ── */
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 12pt 0;
        font-size: 10pt;
        page-break-inside: avoid;
    }
    th {
        background: #F90100;
        color: white;
        padding: 10pt;
        text-align: left;
        font-weight: 700;
        font-size: 9.5pt;
    }
    td {
        padding: 9pt 10pt;
        border-bottom: 1px solid #eee;
    }
    tr:nth-child(even) td { background: #fafafa; }

    /* ── Liste ── */
    ul, ol { margin-left: 15pt; margin-bottom: 8pt; }
    li { margin-bottom: 6pt; }

    /* ── Box evidenziati ── */
    .highlight-box {
        background: linear-gradient(135deg, #fff5f5 0%, #ffffff 100%);
        border-left: 4px solid #F90100;
        padding: 15pt 18pt;
        margin: 15pt 0;
        border-radius: 0 8pt 8pt 0;
        page-break-inside: avoid;
    }
    .highlight-box-green {
        background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%);
        border-left: 4px solid #16a34a;
        padding: 15pt 18pt;
        margin: 15pt 0;
        border-radius: 0 8pt 8pt 0;
        page-break-inside: avoid;
    }
    .highlight-box-blue {
        background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%);
        border-left: 4px solid #2563eb;
        padding: 15pt 18pt;
        margin: 15pt 0;
        border-radius: 0 8pt 8pt 0;
        page-break-inside: avoid;
    }
    .highlight-box-yellow {
        background: linear-gradient(135deg, #fefce8 0%, #ffffff 100%);
        border-left: 4px solid #ca8a04;
        padding: 15pt 18pt;
        margin: 15pt 0;
        border-radius: 0 8pt 8pt 0;
        page-break-inside: avoid;
    }

    /* ── Score badge ── */
    .score-badge {
        display: inline-block;
        background: #F90100;
        color: white;
        padding: 4pt 14pt;
        border-radius: 20pt;
        font-weight: 700;
        font-size: 11pt;
    }
    .score-badge-green { background: #16a34a; color: white; padding: 4pt 14pt; border-radius: 20pt; font-weight: 700; display: inline-block; }
    .score-badge-yellow { background: #ca8a04; color: white; padding: 4pt 14pt; border-radius: 20pt; font-weight: 700; display: inline-block; }
    .score-badge-red { background: #dc2626; color: white; padding: 4pt 14pt; border-radius: 20pt; font-weight: 700; display: inline-block; }

    /* ── Barre di progresso ── */
    .progress-bar-container {
        background: #e5e7eb;
        border-radius: 10pt;
        height: 18pt;
        width: 100%;
        margin: 6pt 0;
        overflow: hidden;
    }
    .progress-bar {
        height: 100%;
        border-radius: 10pt;
        display: flex;
        align-items: center;
        padding-left: 8pt;
        color: white;
        font-size: 9pt;
        font-weight: 700;
    }
    .progress-green { background: linear-gradient(90deg, #16a34a, #22c55e); }
    .progress-yellow { background: linear-gradient(90deg, #ca8a04, #eab308); }
    .progress-red { background: linear-gradient(90deg, #dc2626, #ef4444); }

    /* ── CTA Box ── */
    .cta-box {
        background: linear-gradient(135deg, #F90100 0%, #cc0000 100%);
        color: white;
        padding: 25pt;
        border-radius: 10pt;
        text-align: center;
        margin: 25pt 0;
        page-break-inside: avoid;
    }
    .cta-box h3 { color: white; margin-top: 0; font-size: 18pt; }
    .cta-box p { color: rgba(255,255,255,0.9); text-align: center; }

    /* ── Cards ── */
    .card {
        border: 1px solid #e5e7eb;
        border-radius: 8pt;
        padding: 15pt;
        margin: 10pt 0;
        page-break-inside: avoid;
    }
    .card-red { border-left: 4px solid #F90100; }
    .card-green { border-left: 4px solid #16a34a; }
    .card-blue { border-left: 4px solid #2563eb; }

    /* ── Numeri grandi ── */
    .big-number {
        font-family: 'Poppins', sans-serif;
        font-size: 36pt;
        font-weight: 900;
        line-height: 1.1;
    }
    .big-number-red { color: #F90100; }
    .big-number-green { color: #16a34a; }

    /* ── SWOT ── */
    .swot-box {
        padding: 12pt;
        border-radius: 8pt;
        margin: 6pt 0;
        page-break-inside: avoid;
    }
    .swot-strengths { background: #f0fdf4; border: 1px solid #86efac; }
    .swot-weaknesses { background: #fef2f2; border: 1px solid #fca5a5; }
    .swot-opportunities { background: #eff6ff; border: 1px solid #93c5fd; }
    .swot-threats { background: #fefce8; border: 1px solid #fde047; }

    /* ── Checklist ── */
    .checklist-ok { color: #16a34a; font-weight: 600; }
    .checklist-warn { color: #ca8a04; font-weight: 600; }
    .checklist-fail { color: #dc2626; font-weight: 600; }

    /* ── Bold rosso brand ── */
    strong { color: #F90100; }
"""


# ══════════════════════════════════════════════════════════════
# PDF FREE — 6 sezioni, 8-10 pagine
# ══════════════════════════════════════════════════════════════

def generate_pdf_free(
    sections: Dict[str, str],
    lead_data: Dict[str, Any],
    scores: Dict[str, int],
    output_dir: str = "./reports/free"
) -> Dict[str, Any]:
    """
    Genera PDF del report gratuito da 6 sezioni HTML.
    Footer solo nell'ultima pagina.
    """
    print(f"📄 Generazione PDF report gratuito...")

    try:
        os.makedirs(output_dir, exist_ok=True)

        lead_id = lead_data.get("id", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{lead_id}_diagnosi_gratuita_{timestamp}.pdf"
        filepath = os.path.join(output_dir, filename)

        # Score overview per la pagina 2
        score_totale = scores.get("score_totale", 0)
        score_color = "#dc2626" if score_totale < 50 else "#ca8a04" if score_totale < 75 else "#16a34a"

        scores_overview = ""
        score_items = [
            ("score_sito_web", "Sito Web"),
            ("score_seo", "SEO"),
            ("score_gmb", "Google My Business"),
            ("score_social", "Social Media"),
            ("score_competitivo", "Competitività")
        ]
        for key, label in score_items:
            val = scores.get(key, 0)
            bar_class = "progress-green" if val >= 70 else "progress-yellow" if val >= 40 else "progress-red"
            scores_overview += f'''
            <div style="margin: 8pt 0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 3pt;">
                    <span style="font-weight: 600; font-size: 10pt;">{label}</span>
                    <span style="font-weight: 700; font-size: 10pt;">{val}/100</span>
                </div>
                <div class="progress-bar-container">
                    <div class="progress-bar {bar_class}" style="width: {val}%;">{val}</div>
                </div>
            </div>'''

        # Genera sezioni HTML con page-break
        sections_html = ""
        for i in range(1, 7):
            key = f"section_{i}"
            content = sections.get(key, "")
            if content:
                sections_html += f'''
    <div class="section-container">
        {content}
    </div>
'''
                # Page break dopo ogni sezione TRANNE l'ultima
                if i < 6:
                    sections_html += '    <div class="page-break"></div>\n'

        full_html = f"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <title>Diagnosi Strategica Digitale - {lead_data.get('nome_azienda')}</title>
    <style>
        {SHARED_CSS}

        @page {{
            size: A4;
            margin: 20mm 18mm 25mm 18mm;
            @bottom-center {{
                content: counter(page) " / " counter(pages);
                font-family: 'Inter', sans-serif;
                font-size: 8pt;
                color: #999;
            }}
        }}
        @page :first {{
            margin: 0;
            @bottom-center {{ content: none; }}
        }}

        .page-break {{ page-break-after: always; }}

        /* Copertina */
        .cover {{
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            background: linear-gradient(135deg, #F90100 0%, #000000 100%);
            color: white;
            padding: 40pt;
        }}
        .cover h1 {{
            font-size: 32pt;
            color: white;
            margin-bottom: 5pt;
            letter-spacing: -0.5pt;
        }}
        .cover .subtitle {{
            font-size: 15pt;
            color: rgba(255,255,255,0.85);
            margin-bottom: 30pt;
        }}
        .cover .company-name {{
            font-size: 24pt;
            font-weight: 900;
            color: #F90100;
            background: white;
            padding: 12pt 35pt;
            border-radius: 8pt;
            margin-bottom: 20pt;
        }}
        .cover .date {{
            font-size: 11pt;
            color: rgba(255,255,255,0.6);
            margin-top: 25pt;
        }}
        .cover .badge {{
            background: rgba(255,255,255,0.15);
            border: 2px solid rgba(255,255,255,0.4);
            color: white;
            padding: 6pt 20pt;
            border-radius: 30pt;
            font-weight: 700;
            font-size: 11pt;
            letter-spacing: 2pt;
            text-transform: uppercase;
            margin-top: 10pt;
        }}

        /* Score overview page */
        .score-overview {{
            text-align: center;
            padding: 25pt 15pt;
        }}
        .score-total {{
            font-size: 52pt;
            font-weight: 900;
            font-family: 'Poppins', sans-serif;
            margin-bottom: 3pt;
        }}
        .score-label {{
            font-size: 13pt;
            color: #666;
            margin-bottom: 25pt;
        }}

        /* Sezioni */
        .section-container {{
            padding: 10pt 0;
        }}

        /* Footer ultimo foglio */
        .doc-footer {{
            text-align: center;
            padding: 20pt 15pt;
            border-top: 3px solid #F90100;
            margin-top: 25pt;
            font-size: 10pt;
            color: #666;
        }}
    </style>
</head>
<body>

    <!-- COPERTINA -->
    <div class="cover">
        <h1>Diagnosi Strategica Digitale</h1>
        <div class="subtitle">Analisi della Presenza Digitale</div>
        <div class="company-name">{lead_data.get('nome_azienda', 'Azienda')}</div>
        <div class="badge">Diagnosi Gratuita</div>
        <div class="date">Generato il {datetime.now().strftime('%d/%m/%Y')} | {lead_data.get('citta', '')} ({lead_data.get('provincia', '')})</div>
    </div>
    <div class="page-break"></div>

    <!-- SCORE OVERVIEW -->
    <div class="score-overview">
        <div class="score-total" style="color:{score_color};">{score_totale}/100</div>
        <div class="score-label">Score Digitale Complessivo</div>
        <div style="max-width: 400pt; margin: 0 auto; text-align: left;">
            {scores_overview}
        </div>
    </div>
    <div class="page-break"></div>

    <!-- SEZIONI 1-6 -->
    {sections_html}

    <!-- FOOTER — solo ultima pagina -->
    <div class="doc-footer">
        <p><strong style="color:#F90100;">DigIdentity Agency</strong> | Specialisti AI & Automazioni per MPMI</p>
        <p>📧 info@digidentityagency.it | 📱 +39 392 199 0215 | 🌐 digidentityagency.it</p>
        <p style="margin-top:8pt;font-size:9pt;">
            © {datetime.now().year} DigIdentity Agency — Tutti i diritti riservati.
        </p>
    </div>

</body>
</html>
"""

        print(f"   Rendering PDF...")
        HTML(string=full_html).write_pdf(filepath)

        file_size = os.path.getsize(filepath)
        file_size_mb = file_size / (1024 * 1024)

        print(f"✅ PDF generato: {filename}")
        print(f"   Path: {filepath}")
        print(f"   Dimensione: {file_size_mb:.2f} MB")

        return {
            "success": True,
            "filepath": filepath,
            "filename": filename,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size_mb, 2)
        }

    except Exception as e:
        error_msg = f"Errore generazione PDF: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}


# ══════════════════════════════════════════════════════════════
# PDF PREMIUM — 11 sezioni, 40-50 pagine
# ══════════════════════════════════════════════════════════════

def generate_pdf_premium(
    sections: Dict[str, str],
    lead_data: Dict[str, Any],
    scores: Dict[str, int],
    output_dir: str = "./reports/premium"
) -> Dict[str, Any]:
    """
    Genera PDF del report premium (40-50 pagine) da 11 sezioni HTML.
    Ogni sezione inizia su una nuova pagina.
    """
    print(f"📄 Generazione PDF report PREMIUM...")

    try:
        os.makedirs(output_dir, exist_ok=True)

        lead_id = lead_data.get("id", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{lead_id}_diagnosi_premium_{timestamp}.pdf"
        filepath = os.path.join(output_dir, filename)

        # Score overview
        score_totale = scores.get("score_totale", 0)
        score_color = "#dc2626" if score_totale < 50 else "#ca8a04" if score_totale < 75 else "#16a34a"

        scores_html = ""
        score_items = [
            ("score_sito_web", "Sito Web"),
            ("score_seo", "SEO"),
            ("score_gmb", "Google My Business"),
            ("score_social", "Social Media"),
            ("score_competitivo", "Competitività")
        ]
        for key, label in score_items:
            val = scores.get(key, 0)
            bar_class = "progress-green" if val >= 70 else "progress-yellow" if val >= 40 else "progress-red"
            scores_html += f'''
            <div style="margin: 10pt 0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 3pt;">
                    <span style="font-weight: 600; font-size: 11pt;">{label}</span>
                    <span style="font-weight: 700; font-size: 11pt;">{val}/100</span>
                </div>
                <div class="progress-bar-container" style="height: 22pt;">
                    <div class="progress-bar {bar_class}" style="width: {max(val, 5)}%; height: 100%;">{val}</div>
                </div>
            </div>'''

        # Indice
        section_titles = {
            1: "Executive Summary",
            2: "Analisi Identità Digitale",
            3: "Audit Sito Web Completo",
            4: "Analisi SEO & Posizionamento",
            5: "Google My Business Audit",
            6: "Social Media Audit",
            7: "Analisi Concorrenza",
            8: "Opportunità AI & Automazioni",
            9: "Piano Strategico 90 Giorni",
            10: "Quanto Ti Costa Restare Fermo",
            11: "Proposta di Collaborazione"
        }

        toc_html = ""
        for i, title in section_titles.items():
            toc_html += f'''
            <div style="padding: 11pt 0; border-bottom: 1px solid #eee; display: flex; align-items: center;">
                <span style="display: inline-block; width: 35pt; color: #F90100; font-weight: 800; font-family: 'Poppins', sans-serif; font-size: 14pt;">{i:02d}</span>
                <span style="font-size: 12pt; color: #333;">{title}</span>
            </div>'''

        # Sezioni con page-break tra ciascuna
        sections_html = ""
        for i in range(1, 12):
            key = f"section_{i}"
            content = sections.get(key, "")
            if content:
                sections_html += f'''
    <div class="section-container">
        {content}
    </div>
    <div class="page-break"></div>
'''

        full_html = f"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <title>Diagnosi Strategica Digitale PREMIUM - {lead_data.get('nome_azienda')}</title>
    <style>
        {SHARED_CSS}

        @page {{
            size: A4;
            margin: 22mm 18mm 28mm 18mm;
            @bottom-center {{
                content: counter(page) " / " counter(pages);
                font-family: 'Inter', sans-serif;
                font-size: 9pt;
                color: #999;
            }}
        }}
        @page :first {{
            margin: 0;
            @bottom-center {{ content: none; }}
        }}

        .page-break {{ page-break-after: always; }}

        /* Copertina Premium */
        .cover {{
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            background: linear-gradient(160deg, #000000 0%, #1a0000 40%, #F90100 100%);
            color: white;
            padding: 40pt;
        }}
        .cover h1 {{
            font-size: 34pt;
            color: white;
            margin-bottom: 5pt;
            letter-spacing: -0.5pt;
        }}
        .cover .subtitle {{
            font-size: 15pt;
            color: rgba(255,255,255,0.85);
            margin-bottom: 35pt;
            font-weight: 400;
        }}
        .cover .company-name {{
            font-size: 26pt;
            font-weight: 900;
            color: #F90100;
            background: white;
            padding: 14pt 40pt;
            border-radius: 8pt;
            margin-bottom: 20pt;
        }}
        .cover .date {{
            font-size: 11pt;
            color: rgba(255,255,255,0.6);
            margin-top: 30pt;
        }}
        .cover .badge {{
            background: #F90100;
            color: white;
            padding: 8pt 25pt;
            border-radius: 30pt;
            font-weight: 700;
            font-size: 13pt;
            margin-top: 15pt;
            letter-spacing: 2pt;
            text-transform: uppercase;
        }}

        /* Score overview */
        .score-overview {{
            text-align: center;
            padding: 30pt 20pt;
        }}
        .score-total {{
            font-size: 56pt;
            font-weight: 900;
            font-family: 'Poppins', sans-serif;
            margin-bottom: 3pt;
        }}
        .score-label {{
            font-size: 14pt;
            color: #666;
            margin-bottom: 30pt;
        }}

        /* Indice */
        .toc {{
            padding: 25pt 15pt;
        }}
        .toc h2 {{
            text-align: center;
            font-size: 22pt;
            margin-bottom: 25pt;
        }}

        /* Sezioni */
        .section-container {{
            padding: 10pt 0;
        }}

        /* DigIdentity Card finale */
        .did-card-cta {{
            background: linear-gradient(135deg, #000 0%, #1a0000 100%);
            border: 2px solid #F90100;
            color: white;
            padding: 25pt;
            border-radius: 10pt;
            text-align: center;
            margin: 25pt 0;
            page-break-inside: avoid;
        }}
        .did-card-cta h3 {{
            color: #F90100;
            margin-top: 0;
        }}
        .did-card-cta p {{
            color: rgba(255,255,255,0.85);
            text-align: center;
        }}

        /* Footer documento */
        .doc-footer {{
            text-align: center;
            padding: 20pt 15pt;
            border-top: 3px solid #F90100;
            margin-top: 25pt;
            font-size: 10pt;
            color: #666;
        }}
    </style>
</head>
<body>

    <!-- COPERTINA -->
    <div class="cover">
        <h1>Diagnosi Strategica Digitale</h1>
        <div class="subtitle">Analisi Completa & Piano Operativo AI-Driven</div>
        <div class="company-name">{lead_data.get('nome_azienda', 'Azienda')}</div>
        <div class="badge">★ Report Premium</div>
        <div class="date">Generato il {datetime.now().strftime('%d/%m/%Y')} | {lead_data.get('citta', '')} ({lead_data.get('provincia', '')})</div>
    </div>
    <div class="page-break"></div>

    <!-- SCORE OVERVIEW -->
    <div class="score-overview">
        <div class="score-total" style="color:{score_color};">{score_totale}/100</div>
        <div class="score-label">Score Digitale Complessivo</div>
        <div style="max-width: 450pt; margin: 0 auto; text-align: left;">
            {scores_html}
        </div>
    </div>
    <div class="page-break"></div>

    <!-- INDICE -->
    <div class="toc">
        <h2>Indice</h2>
        {toc_html}
    </div>
    <div class="page-break"></div>

    <!-- SEZIONI 1-11 -->
    {sections_html}

    <!-- DIGIDENTITY CARD -->
    <div class="did-card-cta">
        <h3>🪪 DigIdentity Card</h3>
        <p>La tua identità digitale completa, gestita e ottimizzata.</p>
        <p>Sito, SEO, Social, AI, Automazioni — tutto in un unico ecosistema.</p>
        <p style="font-size:13pt;font-weight:700;color:#F90100;margin-top:15pt;">
            Chiedi informazioni: info@digidentityagency.it
        </p>
    </div>

    <!-- FOOTER DOCUMENTO -->
    <div class="doc-footer">
        <p><strong style="color:#F90100;">DigIdentity Agency</strong> | Specialisti AI & Automazioni per MPMI</p>
        <p>📧 info@digidentityagency.it | 📱 +39 392 199 0215 | 🌐 digidentityagency.it</p>
        <p style="margin-top:8pt;font-size:9pt;">
            Questo documento è riservato e destinato esclusivamente al destinatario indicato.
            La riproduzione o distribuzione non autorizzata è vietata.
            © {datetime.now().year} DigIdentity Agency — Tutti i diritti riservati.
        </p>
    </div>

</body>
</html>
"""

        print(f"   Rendering PDF premium...")
        HTML(string=full_html).write_pdf(filepath)

        file_size = os.path.getsize(filepath)
        file_size_mb = file_size / (1024 * 1024)

        print(f"✅ PDF PREMIUM generato: {filename}")
        print(f"   Path: {filepath}")
        print(f"   Dimensione: {file_size_mb:.2f} MB")

        return {
            "success": True,
            "filepath": filepath,
            "filename": filename,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size_mb, 2)
        }

    except Exception as e:
        error_msg = f"Errore generazione PDF premium: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}
