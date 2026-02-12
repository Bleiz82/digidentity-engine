"""
DigIdentity Engine — Generazione PDF Premium.
Genera PDF professionali con cover page, score badges, barre di progresso e contenuto formattato.
"""

import logging
import re
from pathlib import Path

from weasyprint import HTML
import markdown

logger = logging.getLogger(__name__)


def _get_score_color(score: int) -> str:
    """Ritorna la classe colore basata sul punteggio."""
    if score >= 70:
        return "high"
    elif score >= 40:
        return "medium"
    return "low"


def _get_color_hex(score: int) -> str:
    """Ritorna il colore hex basato sul punteggio."""
    if score >= 70:
        return "#22c55e"
    elif score >= 40:
        return "#f59e0b"
    return "#ef4444"


def _calculate_social_score(scraping_data: dict) -> int:
    """Calcola un punteggio social basato sui dati disponibili."""
    score = 0
    apify = scraping_data.get("apify", {})
    
    ig = apify.get("instagram", {})
    if ig.get("found"):
        score += 20  # presente
        followers = ig.get("followers", 0) or 0
        if followers > 500:
            score += 15
        elif followers > 100:
            score += 10
        elif followers > 0:
            score += 5
        engagement = ig.get("engagement_rate", 0) or 0
        if engagement > 3:
            score += 15
        elif engagement > 1:
            score += 10
    
    fb = apify.get("facebook", {})
    if fb.get("found"):
        score += 20
        fb_followers = fb.get("followers", 0) or 0
        if fb_followers > 500:
            score += 15
        elif fb_followers > 100:
            score += 10
        elif fb_followers > 0:
            score += 5
        fb_engagement = fb.get("avg_engagement_per_post", 0) or 0
        if fb_engagement > 10:
            score += 15
        elif fb_engagement > 1:
            score += 10
    
    return min(score, 100)


def _calculate_gb_score(scraping_data: dict) -> int:
    """Calcola punteggio Google Business."""
    gb = scraping_data.get("google_business", {})
    if not gb.get("found"):
        return 0
    rating = gb.get("rating")
    if rating:
        return min(int(float(rating) * 20), 100)
    return 30  # esiste ma senza rating


def _extract_scores(scraping_data: dict) -> dict:
    """Estrae i 4 punteggi principali dai dati di scraping."""
    ps = scraping_data.get("pagespeed", {})
    desktop = ps.get("desktop", {})
    
    return {
        "sito": desktop.get("performance", 0) or 0,
        "seo": desktop.get("seo", 0) or 0,
        "social": _calculate_social_score(scraping_data),
        "google_business": _calculate_gb_score(scraping_data),
    }


def _generate_cover(company_name: str, date_str: str, location: str) -> str:
    """Genera la cover page HTML."""
    return f'''
    <div class="cover-page">
        <div class="cover-badge">VERSIONE GRATUITA</div>
        <div class="cover-content">
            <div class="cover-subtitle">DIAGNOSI DIGITALE</div>
            <div class="cover-title">{company_name}</div>
            <div class="cover-meta">Strategia AI & Automazioni</div>
            <div class="cover-location">{location} | Generato il {date_str}</div>
        </div>
        <div class="cover-footer">
            <div class="cover-agency">DigIdentity Agency</div>
            <div class="cover-website">www.digidentityagency.it</div>
        </div>
    </div>
    '''


def _generate_scores_section(scores: dict) -> str:
    """Genera la sezione punteggi con badge circolari e barre."""
    labels = {
        "sito": "Sito Web",
        "seo": "SEO", 
        "social": "Social",
        "google_business": "Google Business"
    }
    
    # Badge circolari
    badges_html = '<div class="scores-row">'
    for key, label in labels.items():
        score = scores[key]
        color_class = _get_score_color(score)
        color_hex = _get_color_hex(score)
        badges_html += f'''
        <div class="score-item">
            <div class="score-circle {color_class}" style="border-color: {color_hex}; color: {color_hex};">{score}</div>
            <div class="score-label">{label}</div>
        </div>'''
    badges_html += '</div>'
    
    # Barre di progresso
    bars_html = ''
    for key, label in labels.items():
        score = scores[key]
        color_class = _get_score_color(score)
        bars_html += f'''
        <div class="progress-section">
            <div class="progress-info">
                <span class="progress-label">{label}</span>
                <span class="progress-value">{score}/100</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill {color_class}" style="width: {score}%"></div>
            </div>
        </div>'''
    
    return f'''
    <div class="scores-container">
        <h2 class="scores-title">I Tuoi Punteggi</h2>
        {badges_html}
        {bars_html}
    </div>
    '''


# CSS completo
REPORT_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@600;700;800;900&display=swap');

@page {
    size: A4;
    margin: 18mm 15mm;
    @bottom-center {
        content: "DigIdentity Agency — " counter(page);
        font-family: 'Inter', sans-serif;
        font-size: 8pt;
        color: #999;
    }
}

@page :first {
    margin: 0;
    @bottom-center { content: none; }
}

* { box-sizing: border-box; }

body {
    font-family: 'Inter', sans-serif;
    font-size: 11pt;
    line-height: 1.7;
    color: #333;
    margin: 0;
    padding: 0;
}

/* ===== COVER PAGE ===== */
.cover-page {
    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 40%, #F90100 100%);
    width: 210mm;
    height: 297mm;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    color: white;
    page-break-after: always;
    position: relative;
}

.cover-badge {
    position: absolute;
    top: 40px;
    right: 40px;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.3);
    padding: 8px 20px;
    border-radius: 20px;
    font-size: 10pt;
    letter-spacing: 2px;
    text-transform: uppercase;
}

.cover-content { padding: 0 40px; }

.cover-subtitle {
    font-family: 'Poppins', sans-serif;
    font-size: 14pt;
    letter-spacing: 6px;
    text-transform: uppercase;
    opacity: 0.8;
    margin-bottom: 20px;
}

.cover-title {
    font-family: 'Poppins', sans-serif;
    font-size: 32pt;
    font-weight: 800;
    line-height: 1.2;
    margin-bottom: 15px;
}

.cover-meta {
    font-size: 12pt;
    opacity: 0.7;
    margin-bottom: 10px;
}

.cover-location {
    font-size: 10pt;
    opacity: 0.6;
}

.cover-footer {
    position: absolute;
    bottom: 40px;
    text-align: center;
}

.cover-agency {
    font-family: 'Poppins', sans-serif;
    font-size: 12pt;
    font-weight: 700;
    letter-spacing: 3px;
}

.cover-website {
    font-size: 9pt;
    opacity: 0.6;
    margin-top: 5px;
}

/* ===== SCORES ===== */
.scores-container {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 25px 30px;
    margin: 20px 0 30px;
}

.scores-title {
    font-family: 'Poppins', sans-serif;
    font-size: 16pt;
    font-weight: 700;
    color: #1a1a2e;
    text-align: center;
    margin-bottom: 20px;
}

.scores-row {
    display: flex;
    justify-content: center;
    gap: 25px;
    margin-bottom: 25px;
}

.score-item { text-align: center; }

.score-circle {
    width: 75px;
    height: 75px;
    border-radius: 50%;
    border: 5px solid;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Poppins', sans-serif;
    font-size: 24pt;
    font-weight: 800;
    margin: 0 auto 8px;
    background: white;
}

.score-label {
    font-size: 9pt;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 600;
}

.progress-section { margin: 10px 0; }

.progress-info {
    display: flex;
    justify-content: space-between;
    margin-bottom: 4px;
}

.progress-label {
    font-size: 10pt;
    font-weight: 600;
    color: #444;
}

.progress-value {
    font-size: 10pt;
    font-weight: 700;
    color: #333;
}

.progress-bar {
    background: #e5e7eb;
    border-radius: 10px;
    height: 14px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    border-radius: 10px;
    transition: width 0.3s;
}

.progress-fill.high { background: linear-gradient(90deg, #22c55e, #16a34a); }
.progress-fill.medium { background: linear-gradient(90deg, #f59e0b, #d97706); }
.progress-fill.low { background: linear-gradient(90deg, #ef4444, #dc2626); }

/* ===== CONTENT ===== */
h1 {
    font-family: 'Poppins', sans-serif;
    font-size: 20pt;
    font-weight: 800;
    color: #1a1a2e;
    border-bottom: 3px solid #F90100;
    padding-bottom: 8px;
    margin-top: 35px;
    margin-bottom: 15px;
    page-break-after: avoid;
}

h2 {
    font-family: 'Poppins', sans-serif;
    font-size: 14pt;
    font-weight: 700;
    color: #333;
    margin-top: 25px;
    margin-bottom: 10px;
    page-break-after: avoid;
}

h3 {
    font-family: 'Poppins', sans-serif;
    font-size: 12pt;
    font-weight: 600;
    color: #555;
    margin-top: 15px;
}

p {
    margin: 8px 0;
    text-align: justify;
}

strong { color: #1a1a2e; }

blockquote {
    border-left: 4px solid #F90100;
    background: #fff5f5;
    padding: 12px 18px;
    margin: 15px 0;
    border-radius: 0 8px 8px 0;
    font-style: italic;
}

ul, ol {
    margin: 10px 0;
    padding-left: 25px;
}

li { margin: 5px 0; }

/* Tabelle */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
    font-size: 10pt;
}

thead th {
    background: #F90100;
    color: white;
    padding: 10px 12px;
    text-align: left;
    font-weight: 600;
}

tbody td {
    padding: 8px 12px;
    border-bottom: 1px solid #e5e7eb;
}

tbody tr:nth-child(even) { background: #f9fafb; }

/* CTA Button */
.cta-button {
    display: block;
    background: #F90100;
    color: white !important;
    text-decoration: none;
    text-align: center;
    padding: 16px 40px;
    border-radius: 8px;
    font-family: 'Poppins', sans-serif;
    font-size: 14pt;
    font-weight: 700;
    margin: 25px auto;
    max-width: 400px;
}

.cta-subtext {
    text-align: center;
    font-size: 9pt;
    color: #999;
    margin-top: -15px;
}

/* Footer firma */
.report-footer {
    margin-top: 30px;
    padding-top: 20px;
    border-top: 2px solid #e5e7eb;
    text-align: center;
    color: #666;
    font-size: 10pt;
}

.report-footer strong {
    display: block;
    font-size: 12pt;
    color: #1a1a2e;
    margin-bottom: 5px;
}
"""


def generate_pdf(markdown_text: str, output_path: str, scraping_data: dict = None, 
                 company_name: str = "", date_str: str = "", location: str = "") -> str:
    """
    Genera un PDF premium dalla diagnosi markdown e dai dati di scraping.
    """
    import datetime
    
    if not date_str:
        date_str = datetime.date.today().strftime("%d/%m/%Y")
    
    # Pulisci eventuali tag HTML dal markdown (protezione)
    clean_md = re.sub(r'<div[^>]*>.*?</div>', '', markdown_text, flags=re.DOTALL)
    clean_md = re.sub(r'<[^>]+>', '', clean_md)
    
    # Converti Markdown → HTML
    md_extensions = ['tables', 'fenced_code', 'nl2br']
    content_html = markdown.markdown(clean_md, extensions=md_extensions)
    
    # Sostituisci {{CHECKOUT_PLACEHOLDER}} con bottone CTA
    checkout_button = '''
    <div class="cta-button">OTTIENI IL REPORT PREMIUM A 99€</div>
    <p class="cta-subtext">Pagamento sicuro con Stripe. Consegna immediata.</p>
    '''
    content_html = content_html.replace('{{CHECKOUT_PLACEHOLDER}}', checkout_button)
    # Anche versione HTML-escaped
    content_html = content_html.replace('&#123;&#123;CHECKOUT_PLACEHOLDER&#125;&#125;', checkout_button)
    
    # Genera cover page
    cover_html = _generate_cover(company_name or "Azienda", date_str, location or "Italia")
    
    # Genera sezione punteggi
    scores_html = ""
    if scraping_data:
        scores = _extract_scores(scraping_data)
        scores_html = _generate_scores_section(scores)
    
    # Assembla HTML completo
    full_html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <style>{REPORT_CSS}</style>
</head>
<body>
    {cover_html}
    {scores_html}
    {content_html}
</body>
</html>"""
    
    # Genera PDF
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    HTML(string=full_html).write_pdf(output_path)
    
    logger.info(f"✅ PDF generato con successo: {output_path}")
    return output_path
