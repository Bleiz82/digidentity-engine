import logging
import re
import json
from pathlib import Path
import markdown
from weasyprint import HTML

logger = logging.getLogger(__name__)

def generate_pdf(markdown_text: str, output_path: str, scraping_data: dict = None, 
                 company_name: str = "", date_str: str = "", location: str = "") -> str:
    """
    Genera un report PDF professionale con branding DigIdentity.
    Include Cover Page, Dashboard Punteggi e contenuto dinamico.
    """
    try:
        if scraping_data is None:
            scraping_data = {}

        # 1. Estrazione e Calcolo Punteggi
        scores = _calculate_all_scores(scraping_data)
        
        # 2. Generazione CSS e Componenti HTML
        css = _get_report_css()
        cover_html = _generate_cover(company_name, date_str, location)
        dashboard_html = _generate_dashboard(scores)
        
        # 3. Conversione Markdown in HTML
        content_html = _convert_markdown_to_html(markdown_text, scraping_data)
        
        # 4. Assemblaggio Finale
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>{css}</style>
        </head>
        <body>
            {cover_html}
            {dashboard_html}
            <div class="report-content">
                {content_html}
            </div>
            <div class="footer">
                DigIdentity Agency — Stefano Corda | info@digidentityagency.it | digidentityagency.it
            </div>
        </body>
        </html>
        """
        
        # 5. Generazione PDF con WeasyPrint
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        HTML(string=full_html, base_url=".").write_pdf(output_path)
        
        file_size = Path(output_path).stat().st_size / 1024
        logger.info(f"✅ PDF Generato: {output_path} ({file_size:.1f} KB)")
        return output_path

    except Exception as e:
        logger.error(f"❌ Errore generazione PDF: {str(e)}")
        raise

def _calculate_all_scores(data: dict) -> dict:
    """Estrae e calcola i 4 punteggi per la dashboard."""
    # SITO
    ps = data.get("pagespeed", {}).get("desktop", {})
    ps_scores = ps.get("scores", ps)
    site_score = ps_scores.get("performance", 0) or 0
    if site_score > 0 and site_score < 1: site_score *= 100 # gestisce 0.85 vs 85
    
    # SEO
    seo_score = ps_scores.get("seo", 0) or 0
    if seo_score > 0 and seo_score < 1: seo_score *= 100

    # SOCIAL
    apify = data.get("apify", {})
    ig = apify.get("instagram", {})
    fb = apify.get("facebook", {})
    
    ig_f = ig.get("followers", 0) or 0
    fb_f = fb.get("followers", 0) or 0
    ig_e = ig.get("engagement_rate", 0) or 0
    social_score = min(100, int((ig_f + fb_f) / 5 + ig_e * 10))
    if social_score == 0 and (ig_f > 0 or fb_f > 0): social_score = 25

    # GOOGLE BUSINESS
    gb = data.get("google_business", {})
    gb_score = 0
    if gb.get("found"):
        gb_score = 10
        rating = gb.get("rating")
        reviews = gb.get("reviews_count", 0) or 0
        if rating and rating != "null":
            gb_score = 50
            if reviews > 5: gb_score = 80
            if float(rating) > 4 and reviews > 10: gb_score = 100
    
    return {
        "SITO WEB": int(site_score),
        "SEO": int(seo_score),
        "SOCIAL": int(social_score),
        "GOOGLE BUSINESS": int(gb_score)
    }

def _get_report_css() -> str:
    return """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Poppins:wght@700&display=swap');

    @page {
        size: A4;
        margin: 20mm;
        @bottom-right {
            content: counter(page);
            font-family: 'Inter', sans-serif;
            font-size: 10px;
            color: #666;
        }
    }

    body {
        font-family: 'Inter', sans-serif;
        color: #333;
        line-height: 1.6;
        margin: 0;
        padding: 0;
    }

    /* Copertina */
    .cover {
        height: 250mm;
        background: linear-gradient(135deg, #1A1A1A 0%, #F90100 100%);
        color: white;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        padding: 40px;
        page-break-after: always;
        position: relative;
    }
    .cover-logo {
        position: absolute;
        top: 20mm;
        left: 20mm;
        font-size: 14px;
        font-weight: bold;
    }
    .cover h1 {
        font-family: 'Poppins', sans-serif;
        font-size: 42px;
        text-transform: uppercase;
        letter-spacing: 3px;
        margin: 0;
    }
    .cover h2 {
        font-size: 28px;
        margin: 20px 0;
    }
    .cover h3 {
        font-size: 18px;
        font-style: italic;
        font-weight: normal;
        margin-bottom: 40px;
    }
    .cover-meta {
        font-size: 14px;
        margin-top: 100px;
    }
    .badge-free {
        margin-top: 50px;
        border: 2px solid white;
        padding: 8px 24px;
        border-radius: 20px;
        font-weight: bold;
        text-transform: uppercase;
    }

    /* Dashboard */
    .dashboard {
        page-break-after: always;
        padding-top: 20mm;
    }
    .dashboard h1 {
        font-family: 'Poppins', sans-serif;
        font-size: 28px;
        border-bottom: 3px solid #F90100;
        padding-bottom: 15px;
        margin-bottom: 40px;
    }
    .badges-container {
        display: flex;
        justify-content: space-around;
        margin-bottom: 60px;
    }
    .badge-item {
        text-align: center;
    }
    .circle {
        width: 110px;
        height: 110px;
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        background: white;
        margin-bottom: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .circle-score {
        font-size: 32px;
        font-weight: bold;
        font-family: 'Poppins', sans-serif;
    }
    .badge-label {
        font-size: 12px;
        color: #666;
        font-weight: bold;
        text-transform: uppercase;
    }
    
    .progress-container {
        margin: 10px 0;
    }
    .progress-row {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
    }
    .progress-label {
        width: 150px;
        font-weight: bold;
        font-size: 13px;
    }
    .progress-bar-bg {
        flex-grow: 1;
        height: 14px;
        background: #E0E0E0;
        border-radius: 7px;
        margin: 0 15px;
        position: relative;
    }
    .progress-bar-fill {
        height: 100%;
        border-radius: 7px;
    }
    .progress-value {
        width: 50px;
        font-weight: bold;
        font-size: 13px;
        text-align: right;
    }

    /* Contenuto Report */
    .report-content {
        padding: 0;
    }
    h1 {
        font-family: 'Poppins', sans-serif;
        font-size: 26px;
        color: #1A1A1A;
        border-bottom: 3px solid #F90100;
        padding-bottom: 10px;
        margin-top: 40px;
    }
    h2 {
        font-family: 'Poppins', sans-serif;
        font-size: 20px;
        color: #F90100;
        margin-top: 30px;
    }
    h3 {
        font-family: 'Poppins', sans-serif;
        font-size: 17px;
        color: #1A1A1A;
        margin-top: 20px;
    }
    p {
        font-size: 14px;
        line-height: 1.8;
        margin-bottom: 15px;
        text-align: justify;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 25px 0;
        font-size: 13px;
    }
    th {
        background: #F90100;
        color: white;
        padding: 12px;
        text-align: left;
    }
    td {
        padding: 10px 12px;
        border-bottom: 1px solid #E0E0E0;
    }
    tr:nth-child(even) {
        background: #F9F9F9;
    }
    blockquote {
        border-left: 5px solid #F90100;
        background: #FFF5F5;
        padding: 20px;
        margin: 25px 0;
        font-style: italic;
    }
    
    /* Box Colorati */
    .info-box {
        padding: 20px;
        margin: 20px 0;
        border-radius: 8px;
        border-left: 5px solid;
    }
    .box-critical { background: #FFF0F0; border-color: #E74C3C; }
    .box-success { background: #F0FFF4; border-color: #27AE60; }
    .box-warning { background: #FFFBF0; border-color: #F39C12; }
    .box-ai { background: #F0F4FF; border-color: #3498DB; }

    /* CTA */
    .cta-container {
        text-align: center;
        margin: 50px 0;
        padding: 40px;
        background: #fdfdfd;
        border: 1px dashed #F90100;
        border-radius: 12px;
    }
    .cta-button {
        background: #F90100;
        color: white;
        padding: 20px 50px;
        border-radius: 8px;
        font-size: 18px;
        font-weight: bold;
        text-decoration: none;
        display: inline-block;
        text-transform: uppercase;
        box-shadow: 0 4px 15px rgba(249, 1, 0, 0.3);
    }
    
    .footer {
        position: fixed;
        bottom: -10mm;
        left: 0;
        right: 0;
        text-align: center;
        font-size: 10px;
        color: #999;
        border-top: 1px solid #EEE;
        padding-top: 10px;
    }
    """

def _generate_cover(company_name: str, date_str: str, location: str) -> str:
    from datetime import datetime
    date_val = date_str if date_str else datetime.now().strftime("%d/%m/%Y")
    return f'''
    <div class="cover">
        <div class="cover-logo">DigIdentity Agency</div>
        <h1>Diagnosi Digitale</h1>
        <h2>{company_name}</h2>
        <h3>Strategia AI & Automazioni</h3>
        <div class="cover-meta">
            {location}<br>
            Data: {date_val}
        </div>
        <div class="badge-free">Versione Gratuita</div>
    </div>
    '''

def _generate_dashboard(scores: dict) -> str:
    badges_html = ""
    bars_html = ""
    
    for label, value in scores.items():
        color = "#E74C3C" if value < 40 else "#F39C12" if value < 70 else "#27AE60"
        
        badges_html += f'''
        <div class="badge-item">
            <div class="circle" style="border: 6px solid {color}">
                <span class="circle-score" style="color: {color}">{value}</span>
            </div>
            <div class="badge-label">{label}</div>
        </div>
        '''
        
        bars_html += f'''
        <div class="progress-row">
            <div class="progress-label">{label}</div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width: {value}%; background-color: {color}"></div>
            </div>
            <div class="progress-value">{value}/100</div>
        </div>
        '''
        
    return f'''
    <div class="dashboard">
        <h1>I Tuoi Punteggi</h1>
        <div class="badges-container">
            {badges_html}
        </div>
        <div class="progress-container">
            {bars_html}
        </div>
    </div>
    '''

def _convert_markdown_to_html(md_text: str, data: dict) -> str:
    # 1. Pulisci tag HTML residui (sanificazione)
    # Rimuove div, span, section e attributi class o style
    md_text = re.sub(r'<(div|span|section|p|h1|h2|h3|table|tr|td|th)[^>]*>', '', md_text)
    md_text = re.sub(r'</(div|span|section|p|h1|h2|h3|table|tr|td|th)>', '', md_text)
    
    # 2. Converti in HTML
    html = markdown.markdown(md_text, extensions=['tables', 'fenced_code', 'nl2br'])
    
    # 3. Applica Box Emojis
    box_patterns = [
        (r'<p>🚨(.*?)</p>', 'box-critical'),
        (r'<p>✅(.*?)</p>', 'box-success'),
        (r'<p>💡(.*?)</p>', 'box-warning'),
        (r'<p>🤖(.*?)</p>', 'box-ai'),
    ]
    for pattern, css_class in box_patterns:
        html = re.sub(pattern, f'<div class="info-box {css_class}">\\1</div>', html, flags=re.DOTALL)
    
    # 4. Sostituisci CTA Placeholder
    checkout_url = data.get("checkout_url", "#")
    cta_html = f'''
    <div class="cta-container">
        <a href="{checkout_url}" class="cta-button">Ottieni il Report Premium a 99€</a>
        <p style="font-size: 11px; margin-top: 15px; color: #666;">Include piano 90 giorni, calendario social e analisi AI ROI.</p>
    </div>
    '''
    html = html.replace("{{CHECKOUT_PLACEHOLDER}}", cta_html)
    
    return html
