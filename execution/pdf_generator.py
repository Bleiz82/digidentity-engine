"""
DigIdentity Engine — Generazione PDF dai report Markdown.

Converte i report Markdown in PDF professionali con branding DigIdentity.
"""

import logging
import re
from pathlib import Path

from weasyprint import HTML, CSS
import markdown

logger = logging.getLogger(__name__)

# CSS Premium per WeasyPrint
REPORT_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@700;800;900&display=swap');

@page {
    size: A4;
    margin: 20mm;
    @bottom-right {
        content: "DigIdentity Agency — " counter(page);
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

/* Cover Page */
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

.cover-page h1 {
    font-family: 'Poppins', sans-serif;
    font-weight: 900;
    font-size: 42pt;
    margin: 0;
    text-transform: uppercase;
    color: white;
}

.cover-page .subtitle {
    font-size: 18pt;
    color: #F90100;
    margin: 10px 0 40px 0;
    font-weight: 700;
}

.cover-page .client-name {
    font-size: 24pt;
    font-weight: 600;
}

.cover-page .badge {
    margin-top: 20px;
    padding: 5px 20px;
    border: 2px solid #F90100;
    border-radius: 30px;
    font-size: 12pt;
    font-weight: 700;
    letter-spacing: 2px;
}

/* Typography */
h1 {
    font-family: 'Poppins', sans-serif;
    font-weight: 900;
    font-size: 26pt;
    color: #000;
    margin-top: 30px;
    border-bottom: 5px solid #F90100;
    padding-bottom: 10px;
}

h2 {
    font-family: 'Poppins', sans-serif;
    font-weight: 800;
    font-size: 20pt;
    color: #1a1a1a;
    margin-top: 25px;
}

h3 {
    font-family: 'Poppins', sans-serif;
    font-weight: 700;
    font-size: 15pt;
    color: #F90100;
}

/* Score Badges */
.score-row {
    display: flex;
    justify-content: space-around;
    margin: 30px 0;
}

.score-badge-container {
    text-align: center;
}

.score-circle {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    border: 5px solid #eee;
    line-height: 80px;
    font-size: 22px;
    font-weight: 900;
    margin-bottom: 5px;
    font-family: 'Poppins', sans-serif;
}

.score-circle.high { border-color: #10B981; color: #10B981; }
.score-circle.medium { border-color: #F59E0B; color: #F59E0B; }
.score-circle.low { border-color: #EF4444; color: #EF4444; }

.score-label {
    font-size: 9pt;
    font-weight: 700;
    text-transform: uppercase;
}

/* Progress Bars */
.progress-section {
    margin: 20px 0;
}

.progress-info {
    display: flex;
    justify-content: space-between;
    font-weight: 700;
    margin-bottom: 5px;
}

.progress-container {
    width: 100%;
    height: 20px;
    background: #eee;
    border-radius: 10px;
    overflow: hidden;
    position: relative;
}

.progress-fill {
    height: 100%;
}

.progress-fill.high { background: #10B981; }
.progress-fill.medium { background: #F59E0B; }
.progress-fill.low { background: #EF4444; }

/* Boxes */
.custom-box {
    padding: 15px;
    margin: 20px 0;
    border-radius: 6px;
    border-left: 5px solid;
}

.critical-box { background: #fff5f5; border-color: #F90100; color: #c53030; }
.success-box { background: #f0fff4; border-color: #38a169; color: #276749; }
.tip-box { background: #fffff0; border-color: #ecc94b; color: #744210; }

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
}

th {
    background: #F90100;
    color: white;
    padding: 12px;
    text-align: left;
}

td {
    padding: 10px;
    border-bottom: 1px solid #eee;
}

tr:nth-child(even) { background: #f9f9f9; }

/* Button */
.cta-button {
    display: block;
    width: 300px;
    margin: 40px auto;
    background: #F90100;
    color: white;
    text-align: center;
    padding: 15px 30px;
    border-radius: 8px;
    font-size: 14pt;
    font-weight: 800;
    text-decoration: none;
    text-transform: uppercase;
}

footer {
    margin-top: 50px;
    padding-top: 20px;
    border-top: 1px solid #eee;
    font-size: 9pt;
    color: #666;
    text-align: center;
}
"""

def markdown_to_pdf(markdown_text: str, output_path: str, company_name: str = "", report_type: str = "free") -> str:
    """
    Converte il report Markdown in PDF con stile premium.
    """
    import datetime
    
    logger.info(f"🎨 Generando PDF Premium per {company_name}")

    # 1. Parsing Punteggi per Badges
    scores = {"Sito": 0, "SEO": 0, "Social": 0, "Google Business": 0}
    for key in scores.keys():
        match = re.search(fr"{key}:\s*(\d+)/100", markdown_text)
        if match:
            scores[key] = int(match.group(1))

    # Generazione HTML Badges
    badges_html = '<div class="score-row">'
    for label, val in scores.items():
        cls = "high" if val >= 70 else "medium" if val >= 40 else "low"
        badges_html += f'''
        <div class="score-badge-container">
            <div class="score-circle {cls}">{val}</div>
            <div class="score-label">{label}</div>
        </div>
        '''
    badges_html += '</div>'

    # 2. Trasformazione Barre di Progresso
    def repl_bar(match):
        label = match.group(1).strip()
        val = int(match.group(2))
        cls = "high" if val >= 70 else "medium" if val >= 40 else "low"
        return f'''
        <div class="progress-section">
            <div class="progress-info"><span>{label}</span><span>{val}/100</span></div>
            <div class="progress-container"><div class="progress-fill {cls}" style="width: {val}%"></div></div>
        </div>
        '''
    markdown_text = re.sub(r"\[BARRA_PUNTEGGIO:\s*(.*?):\s*(\d+)/100\]", repl_bar, markdown_text)

    # 3. Trasformazione Box Colorati (Pattern user request)
    markdown_text = re.sub(r"^🚨\s*(.*)", r'<div class="custom-box critical-box">🚨 \1</div>', markdown_text, flags=re.MULTILINE)
    markdown_text = re.sub(r"^✅\s*(.*)", r'<div class="custom-box success-box">✅ \1</div>', markdown_text, flags=re.MULTILINE)
    markdown_text = re.sub(r"^💡\s*(.*)", r'<div class="custom-box tip-box">💡 \1</div>', markdown_text, flags=re.MULTILINE)
    
    # 3b. Gestione blockquote boxes (Fix turn precedente)
    def repl_box(match):
        type_ = match.group(1).lower()
        content = match.group(2).strip()
        cls = "critical-box" if type_ == "critical" else "success-box" if type_ == "success" else "tip-box"
        icon = "🚨" if type_ == "critical" else "✅" if type_ == "success" else "💡"
        return f'<div class="custom-box {cls}"><strong>{icon} {type_.upper()}:</strong><br/>{content}</div>'
    
    markdown_text = re.sub(r'>\s*\[!(CRITICAL|SUCCESS|SUGGESTION)\]\s*(.*?)(?=\n\n|\n$|\Z)', repl_box, markdown_text, flags=re.DOTALL)

    # 4. Emojis nei titoli (se non già presenti)
    title_emojis = {
        "LA TUA FOTOGRAFIA DIGITALE": "📊",
        "COME TI TROVANO I CLIENTI": "🔍",
        "TU VS I TUOI CONCORRENTI": "⚔️",
        "I TUOI CONCORRENTI": "⚔️",
        "5 AZIONI CHE PUOI FARE": "✅",
        "IL TUO PROSSIMO PASSO": "🚀"
    }
    for title, emoji in title_emojis.items():
        markdown_text = re.sub(fr"^#\s*{title}", f"# {emoji} {title}", markdown_text, flags=re.MULTILINE)
        markdown_text = re.sub(fr"^##\s*{title}", f"## {emoji} {title}", markdown_text, flags=re.MULTILINE)

    # 5. CTA Button
    cta_html = '<a href="#" class="cta-button">OTTIENI IL REPORT PREMIUM A 99€</a>'
    markdown_text = markdown_text.replace("{{CHECKOUT_PLACEHOLDER}}", cta_html)

    # 6. Conversione Markdown -> HTML
    html_content = markdown.markdown(markdown_text, extensions=['tables', 'fenced_code', 'nl2br'])

    # 7. Layout Finale
    today = datetime.date.today().strftime("%d/%m/%Y")
    logo_url = "https://digidentityagency.it/wp-content/uploads/2023/05/digidentity_agency_light_removebg.png"
    
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>{REPORT_CSS}</style>
    </head>
    <body class="report-body">
        <div class="cover-page">
            <img src="{logo_url}" style="width: 250px; margin-bottom: 50px;">
            <h1>Diagnosi Digitale</h1>
            <div class="subtitle">Strategia AI & Automazioni</div>
            <div class="client-name">{company_name}</div>
            <div class="badge">VERSIONE GRATUITA</div>
            <div style="margin-top: 80px; font-size: 10pt; opacity: 0.8;">
                Generato il {today}<br>Samatzai (SU), Sardegna
            </div>
        </div>
        
        <div style="padding: 20mm;">
            {badges_html}
            {html_content}
            
            <footer>
                <strong>Stefano Corda</strong> — Fondatore, DigIdentity Agency<br>
                info@digidentityagency.it | www.digidentityagency.it<br>
                Sede: Via Dettori 3, 09020 Samatzai (SU)
            </footer>
        </div>
    </body>
    </html>
    """

    # Generazione PDF
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    HTML(string=full_html).write_pdf(output_path)
    
    logger.info(f"✅ PDF '{output_path}' generato con successo.")
    return output_path
