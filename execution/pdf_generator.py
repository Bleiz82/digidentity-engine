import logging
import re
import json
from pathlib import Path
import markdown
from weasyprint import HTML

logger = logging.getLogger(__name__)


def _add_visual_elements(html_content, scraping_data):
    """Aggiunge barre di progresso e icone visive al report HTML"""
    import re
    
    # Sostituisci i punteggi con barre di progresso visive
    def score_to_bar(score):
        try:
            s = int(float(score))
        except:
            return score
        color = "#e74c3c" if s < 40 else "#f39c12" if s < 70 else "#27ae60"
        return f'<span style="font-weight:bold;color:{color}">{s}/100</span> <span style="display:inline-block;width:120px;height:12px;background:#e0e0e0;border-radius:6px;vertical-align:middle"><span style="display:inline-block;width:{s}%;height:100%;background:{color};border-radius:6px"></span></span>'
    
    # Aggiungi icone alle intestazioni se non hanno emoji
    icon_map = {
        "FOTOGRAFIA DIGITALE": "📊",
        "COME I CLIENTI": "🔍", 
        "COMPETITOR": "🏆",
        "SITO WEB": "🌐",
        "INTELLIGENZA ARTIFICIALE": "🤖",
        "5 AZIONI": "✅",
        "CONCLUSIONE": "📈"
    }
    
    # Box informativi colorati per dati chiave
    html_content = html_content.replace(
        '<blockquote>',
        '<blockquote style="border-left:4px solid #1a73e8;background:#e8f0fe;padding:12px 16px;margin:16px 0;border-radius:0 8px 8px 0;font-style:normal">'
    )
    
    return html_content



def _generate_score_gauge(score, label, size=80):
    try:
        s = int(float(score))
    except:
        s = 0
    if s < 50:
        color = "#e74c3c"
    elif s < 90:
        color = "#f39c12"
    else:
        color = "#27ae60"
    circumference = 2 * 3.14159 * 35
    offset = circumference - (s / 100) * circumference
    return f"""<div style="display:inline-block;text-align:center;margin:8px 12px">
        <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
            <circle cx="{size//2}" cy="{size//2}" r="35" fill="none" stroke="#e0e0e0" stroke-width="6"/>
            <circle cx="{size//2}" cy="{size//2}" r="35" fill="none" stroke="{color}" stroke-width="6"
                stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"
                transform="rotate(-90 {size//2} {size//2})" stroke-linecap="round"/>
            <text x="{size//2}" y="{size//2 + 2}" text-anchor="middle" dominant-baseline="middle"
                font-size="18" font-weight="bold" fill="{color}">{s}</text>
        </svg>
        <div style="font-size:10px;color:#555;margin-top:2px;font-weight:600">{label}</div>
    </div>"""


def _generate_pagespeed_detail(scraping_data):
    ps = scraping_data.get("pagespeed", {})
    mobile = ps.get("mobile", {}).get("scores", {})
    desktop = ps.get("desktop", {}).get("scores", {})
    html = '<div style="background:#f8f9fa;border-radius:12px;padding:20px;margin:20px 0;border:1px solid #e0e0e0">'
    html += '<div style="font-size:15px;font-weight:700;color:#1a237e;margin-bottom:15px;text-align:center">Punteggi PageSpeed Insights</div>'
    for device, scores in [("MOBILE", mobile), ("DESKTOP", desktop)]:
        html += f'<div style="margin-bottom:12px"><div style="font-size:12px;font-weight:700;color:#555;margin-bottom:6px;text-align:center">{device}</div>'
        html += '<div style="display:flex;justify-content:center;flex-wrap:wrap">'
        for key, label in [("performance","Performance"),("accessibility","Accessibilita"),("best-practices","Best Practices"),("seo","SEO")]:
            val = scores.get(key, 0)
            html += _generate_score_gauge(val, label, 70)
        html += '</div></div>'
    html += '</div>'
    return html


def _generate_final_score(scraping_data):
    ps = scraping_data.get("pagespeed", {})
    desktop = ps.get("desktop", {}).get("scores", {})
    mobile = ps.get("mobile", {}).get("scores", {})
    site_score = int((desktop.get("performance", 0) + desktop.get("seo", 0)) / 2) if desktop else 0
    seo_score = desktop.get("seo", 0) if desktop else 0
    social_score = scraping_data.get("social_score", 50)
    gb = scraping_data.get("google_business", {})
    gb_score = 10 if gb.get("found") and not gb.get("rating") else (70 if gb.get("found") and gb.get("rating") else 0)
    scores = {"site": site_score, "seo": seo_score, "social": social_score, "google_business": gb_score}
    vals = [v for v in scores.values() if isinstance(v, (int, float)) and v > 0]
    avg = int(sum(vals) / len(vals)) if vals else 0
    if avg < 40:
        color = "#e74c3c"
        giudizio = "Critica"
    elif avg < 55:
        color = "#f39c12"
        giudizio = "Da migliorare"
    elif avg < 70:
        color = "#2196f3"
        giudizio = "Sufficiente"
    else:
        color = "#27ae60"
        giudizio = "Buona"
    circumference = 2 * 3.14159 * 55
    offset = circumference - (avg / 100) * circumference
    return f"""<div style="text-align:center;margin:30px 0;padding:25px;background-color:#8B0000;border-radius:16px">
        <div style="color:white;font-size:18px;font-weight:700;margin-bottom:15px">PUNTEGGIO FINALE PRESENZA DIGITALE</div>
        <div style="width:120px;height:120px;border-radius:50%;border:8px solid {color};margin:0 auto;display:flex;align-items:center;justify-content:center;flex-direction:column">
            <div style="color:white;font-size:36px;font-weight:bold;line-height:1">{avg}</div>
            <div style="color:rgba(255,255,255,0.8);font-size:12px">/100</div>
        </div>
        <div style="color:{color};font-size:16px;font-weight:700;margin-top:10px">{giudizio}</div>
        <div style="color:rgba(255,255,255,0.7);font-size:11px;margin-top:8px">Media: Sito Web, SEO, Social Media, Google Business</div>
    </div>"""



def generate_pdf(markdown_text: str, output_path: str, scraping_data: dict = None, 
                 company_name: str = "", date_str: str = "", location: str = "",
                 checkout_url: str = "") -> str:
    try:
        if scraping_data is None:
            scraping_data = {}
        if checkout_url:
            scraping_data["checkout_url"] = checkout_url

        scores = _calculate_all_scores(scraping_data)
        css = _get_report_css()
        cover_html = _generate_cover(company_name, date_str, location)
        dashboard_html = _generate_dashboard(scores, scraping_data)
        content_html = _convert_markdown_to_html(markdown_text, scraping_data)
        # Grafici PageSpeed dopo sezione sito web
        pagespeed_detail_html = _generate_pagespeed_detail(scraping_data)
        for marker in ['COSA TROVA CHI', 'LA SEDE DIGITALE', 'SITO WEB:']:
            pos = content_html.upper().find(marker.upper())
            if pos > 0:
                next_h = -1
                for tag in ['<h1', '<h2']:
                    p = content_html.find(tag, pos + len(marker))
                    if p > 0 and (next_h < 0 or p < next_h):
                        next_h = p
                if next_h > 0:
                    content_html = content_html[:next_h] + pagespeed_detail_html + content_html[next_h:]
                break
        # Punteggio finale alla fine del report
        final_score_html = _generate_final_score(scraping_data)
        content_html = content_html + final_score_html
        
        full_html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>{css}</style></head>
<body>
{cover_html}
{dashboard_html}
<div class="report-content">{content_html}</div>
</body></html>"""
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        HTML(string=full_html, base_url=".").write_pdf(output_path)
        
        file_size = Path(output_path).stat().st_size / 1024
        logger.info(f"PDF Generato: {output_path} ({file_size:.1f} KB)")
        return output_path
    except Exception as e:
        logger.error(f"Errore generazione PDF: {str(e)}")
        raise


def _calculate_social_score(scraping_data):
    apify = scraping_data.get("apify", {})
    ig = apify.get("instagram", {})
    fb = apify.get("facebook", {})
    ig_followers = ig.get("followers", 0) or 0
    fb_followers = fb.get("followers", 0) or 0
    ig_engagement = ig.get("engagement_rate", 0) or 0
    ig_posts = ig.get("posts_count", 0) or 0
    fb_posts = len(fb.get("recent_posts", [])) if isinstance(fb.get("recent_posts"), list) else 0
    follower_total = ig_followers + fb_followers
    follower_score = min(40, (follower_total / 1000) * 40)
    engagement_score = min(30, (ig_engagement / 5) * 30)
    total_posts = ig_posts + fb_posts
    activity_score = min(30, (total_posts / 20) * 30)
    return round(follower_score + engagement_score + activity_score)


def _calculate_all_scores(data: dict) -> dict:
    ps = data.get("pagespeed", {})
    ps_d = ps.get("desktop", {})
    ps_d_scores = ps_d.get("scores", ps_d)
    desktop_perf = ps_d_scores.get("performance", 0) or 0
    if 0 < desktop_perf < 1: desktop_perf *= 100
    ps_m = ps.get("mobile", {})
    ps_m_scores = ps_m.get("scores", ps_m)
    mobile_perf = ps_m_scores.get("performance", 0) or 0
    if 0 < mobile_perf < 1: mobile_perf *= 100
    site_score = round((mobile_perf + desktop_perf) / 2) if (mobile_perf or desktop_perf) else 0
    seo_score = ps_d_scores.get("seo", 0) or 0
    if 0 < seo_score < 1: seo_score *= 100
    social_score = _calculate_social_score(data)
    gb = data.get("google_business", {})
    gb_score = 0
    if gb.get("found"):
        gb_score = 10
        rating = gb.get("rating")
        reviews = gb.get("reviews_count", 0) or 0
        if rating and str(rating) != "null":
            gb_score = 50
            if reviews > 5: gb_score = 80
            if float(rating) > 4 and reviews > 10: gb_score = 100
    return {
        "SITO WEB": int(site_score),
        "SEO": int(seo_score),
        "SOCIAL": int(social_score),
        "GOOGLE BUSINESS": int(gb_score),
        "DETAILS": {
            "Mobile": int(mobile_perf),
            "Desktop": int(desktop_perf)
        }
    }


def _get_report_css() -> str:
    return """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Poppins:wght@600;700;800&display=swap');
    
    @page { size: A4; margin: 18mm 20mm 25mm 20mm; }
    @page :first { margin: 0; }
    
    body {
        font-family: 'Inter', sans-serif;
        color: #2D2D2D;
        line-height: 1.7;
        font-size: 13px;
    }

    /* === COVER === */
    .cover {
        height: 297mm;
        background: #8B0000;
        color: white;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        padding: 40px;
        page-break-after: always;
        position: relative;
        overflow: hidden;
    }
    .cover::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 100%;
        height: 100%;
        background: rgba(249,1,0,0.15);
    }
    .cover-logo {
        position: absolute;
        top: 25mm;
        left: 25mm;
        font-family: 'Poppins', sans-serif;
        font-size: 16px;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        opacity: 0.9;
    }
    .cover-badge {
        position: absolute;
        top: 25mm;
        right: 25mm;
        border: 2px solid rgba(255,255,255,0.5);
        padding: 6px 18px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .cover-content { position: relative; z-index: 1; }
    .cover-content h1 {
        font-family: 'Poppins', sans-serif;
        font-size: 44px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 4px;
        margin: 0;
        border: none;
        color: white;
    }
    .cover-content .company-name {
        font-family: 'Poppins', sans-serif;
        font-size: 30px;
        font-weight: 700;
        margin: 25px 0;
        color: #FF6B6B;
    }
    .cover-content .subtitle {
        font-size: 16px;
        font-weight: 300;
        letter-spacing: 3px;
        text-transform: uppercase;
        opacity: 0.8;
        margin-bottom: 60px;
    }
    .cover-content .meta {
        font-size: 13px;
        opacity: 0.7;
        line-height: 2;
    }
    .cover-line {
        width: 80px;
        height: 3px;
        background: #F90100;
        margin: 30px auto;
    }

    /* === DASHBOARD === */
    .dashboard {
        page-break-after: always;
        padding: 15mm 0 0 0;
    }
    .dashboard-title {
        font-family: 'Poppins', sans-serif;
        font-size: 26px;
        font-weight: 700;
        color: #1A1A1A;
        border-bottom: 3px solid #F90100;
        padding-bottom: 12px;
        margin-bottom: 35px;
    }
    .badges-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 40px;
    }
    .badge-card {
        text-align: center;
        width: 23%;
        background: #FAFAFA;
        border-radius: 12px;
        padding: 20px 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    }
    .badge-circle {
        width: 90px;
        height: 90px;
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 0 auto 12px auto;
        background: white;
        box-shadow: 0 3px 12px rgba(0,0,0,0.08);
    }
    .badge-number {
        font-family: 'Poppins', sans-serif;
        font-size: 28px;
        font-weight: 800;
    }
    .badge-label {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #666;
    }
    .bars-section {
        margin-top: 30px;
    }
    .bar-row {
        display: flex;
        align-items: center;
        margin-bottom: 14px;
    }
    .bar-label {
        width: 130px;
        font-size: 12px;
        font-weight: 600;
        color: #444;
    }
    .bar-track {
        flex-grow: 1;
        height: 12px;
        background: #EEEEEE;
        border-radius: 6px;
        margin: 0 12px;
        overflow: hidden;
    }
    .bar-fill {
        height: 100%;
        border-radius: 6px;
        transition: width 0.3s;
    }
    .bar-value {
        width: 55px;
        font-size: 12px;
        font-weight: 700;
        text-align: right;
        color: #333;
    }
    .detail-box {
        background: #F5F5F5;
        border-radius: 10px;
        padding: 20px 25px;
        margin-top: 25px;
    }
    .detail-box-title {
        font-family: 'Poppins', sans-serif;
        font-size: 14px;
        font-weight: 700;
        color: #F90100;
        margin-bottom: 15px;
    }

    /* === REPORT CONTENT === */
    .report-content { padding: 0; }
    
    .report-content h1 {
        font-family: 'Poppins', sans-serif;
        font-size: 24px;
        color: #1A1A1A;
        border-bottom: 3px solid #F90100;
        padding-bottom: 10px;
        margin-top: 45px;
        margin-bottom: 20px;
        page-break-after: avoid;
    }
    .report-content h2 {
        font-family: 'Poppins', sans-serif;
        font-size: 18px;
        color: #F90100;
        margin-top: 30px;
        margin-bottom: 12px;
        page-break-after: avoid;
    }
    .report-content h3 {
        font-family: 'Poppins', sans-serif;
        font-size: 15px;
        color: #333;
        margin-top: 22px;
        margin-bottom: 8px;
        padding: 10px 15px;
        background: #F8F8F8;
        border-left: 4px solid #F90100;
        border-radius: 0 6px 6px 0;
        page-break-after: avoid;
    }
    .report-content p {
        font-size: 13px;
        line-height: 1.8;
        margin-bottom: 14px;
        text-align: justify;
    }
    .report-content strong {
        color: #1A1A1A;
    }

    /* === TABLES === */
    .report-content table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin: 20px 0;
        font-size: 12px;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .report-content th {
        background: #F90100;
        color: white;
        padding: 11px 14px;
        text-align: left;
        font-weight: 600;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .report-content td {
        padding: 10px 14px;
        border-bottom: 1px solid #EEE;
        vertical-align: top;
    }
    .report-content tr:nth-child(even) { background: #FAFAFA; }
    .report-content tr:last-child td { border-bottom: none; }

    /* === BLOCKQUOTES === */
    .report-content blockquote {
        border-left: 4px solid #F90100;
        background: linear-gradient(135deg, #FFF5F5, #FFFFFF);
        padding: 18px 22px;
        margin: 22px 0;
        border-radius: 0 8px 8px 0;
        font-style: italic;
        font-size: 13px;
        color: #555;
    }

    /* === INFO BOXES === */
    .info-box {
        padding: 18px 22px;
        margin: 20px 0;
        border-radius: 8px;
        border-left: 5px solid;
        font-size: 13px;
    }
    .box-critical { background: #FFF0F0; border-color: #E74C3C; }
    .box-success { background: #F0FFF4; border-color: #27AE60; }
    .box-warning { background: #FFFBF0; border-color: #F39C12; }
    .box-ai { background: #F0F4FF; border-color: #3498DB; }

    /* === PREMIUM TEASER === */
    .premium-teaser {
        margin: 40px 0;
        padding: 30px;
        background: linear-gradient(135deg, #1A1A1A, #2D2D2D);
        color: white;
        border-radius: 12px;
        text-align: center;
    }
    .premium-teaser h3 {
        font-family: 'Poppins', sans-serif;
        font-size: 20px;
        color: #FF6B6B;
        margin: 0 0 15px 0;
        background: none;
        border: none;
        padding: 0;
    }
    .premium-teaser p {
        color: #CCC;
        font-size: 13px;
        text-align: center;
        margin: 8px 0;
    }
    .premium-features {
        display: flex;
        justify-content: space-around;
        margin: 20px 0;
        flex-wrap: wrap;
    }
    .premium-feat {
        text-align: center;
        width: 30%;
        padding: 10px;
    }
    .premium-feat-icon {
        font-size: 28px;
        margin-bottom: 8px;
    }
    .premium-feat-text {
        font-size: 11px;
        color: #AAA;
        line-height: 1.5;
    }
    .premium-price {
        font-family: 'Poppins', sans-serif;
        font-size: 36px;
        font-weight: 800;
        color: #F90100;
        margin: 15px 0 5px 0;
    }
    .premium-price-note {
        font-size: 12px;
        color: #888;
    }

    /* === LISTS === */
    .report-content ul {
        padding-left: 0;
        list-style: none;
    }
    .report-content ul li {
        padding: 6px 0 6px 22px;
        position: relative;
        line-height: 1.7;
    }
    .report-content ul li::before {
        content: '';
        position: absolute;
        left: 0;
        top: 13px;
        width: 8px;
        height: 8px;
        background: #F90100;
        border-radius: 50%;
    }
    .report-content ol {
        counter-reset: item;
        list-style: none;
        padding-left: 0;
    }
    .report-content ol > li {
        counter-increment: item;
        margin-bottom: 18px;
        padding: 16px 20px 16px 55px;
        background: #FAFAFA;
        border-radius: 8px;
        border-left: 4px solid #F90100;
        position: relative;
    }
    .report-content ol > li::before {
        content: counter(item);
        position: absolute;
        left: 14px;
        top: 14px;
        background: #F90100;
        color: white;
        font-weight: 700;
        font-size: 14px;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    /* === FOOTER === */
    @page {
        @bottom-center {
            content: "DigIdentity Agency | info@digidentityagency.it | digidentityagency.it";
            font-family: 'Inter', sans-serif;
            font-size: 9px;
            color: #BBB;
        }
        @bottom-right {
            content: counter(page);
            font-family: 'Inter', sans-serif;
            font-size: 9px;
            color: #BBB;
        }
    }
    """


def _generate_cover(company_name: str, date_str: str, location: str) -> str:
    from datetime import datetime
    date_val = date_str if date_str else datetime.now().strftime("%d/%m/%Y")
    return f'''
    <div class="cover">
        <div class="cover-logo"><img src="/app/assets/logo_light.png" style="width:200px" alt="DigIdentity Agency"></div>
        <div class="cover-badge">Versione Gratuita</div>
        <div class="cover-content">
            <h1>DIAGNOSI<br>DIGITALE</h1>
            <div class="cover-line"></div>
            <div class="company-name">{company_name}</div>
            <div class="subtitle">Analisi AI della Presenza Digitale</div>
            <div class="meta">
                {location}<br>
                {date_val}<br><br>
                7 Motori AI &bull; Analisi a 360&deg; &bull; Dati Reali
            </div>
        </div>
    </div>
    '''


def _generate_dashboard(scores: dict, scraping_data: dict = None) -> str:
    if scraping_data is None:
        scraping_data = {}
    
    badges_html = ""
    bars_html = ""
    labels = ["SITO WEB", "SEO", "SOCIAL", "GOOGLE BUSINESS"]
    icons = {"SITO WEB": "&#x1F310;", "SEO": "&#x1F50D;", "SOCIAL": "&#x1F4F1;", "GOOGLE BUSINESS": "&#x1F4CD;"}
    
    for label in labels:
        value = scores.get(label, 0)
        color = "#E74C3C" if value < 40 else "#F39C12" if value < 70 else "#27AE60"
        badges_html += f'''
        <div class="badge-card">
            <div class="badge-circle" style="border: 5px solid {color}">
                <span class="badge-number" style="color: {color}">{value}</span>
            </div>
            <div class="badge-label">{label}</div>
        </div>'''

    all_bars = []
    details = scores.get("DETAILS", {})
    for d_label, d_value in details.items():
        all_bars.append((d_label, d_value))
    for label in ["SEO", "SOCIAL", "GOOGLE BUSINESS"]:
        all_bars.append((label, scores.get(label, 0)))
    
    for label, value in all_bars:
        color = "#E74C3C" if value < 40 else "#F39C12" if value < 70 else "#27AE60"
        bars_html += f'''
        <div class="bar-row">
            <div class="bar-label">{label}</div>
            <div class="bar-track"><div class="bar-fill" style="width:{value}%;background:{color}"></div></div>
            <div class="bar-value">{value}/100</div>
        </div>'''

    # Quick stats box
    gb = scraping_data.get("google_business", {})
    apify = scraping_data.get("apify", {})
    ig = apify.get("instagram", {})
    fb = apify.get("facebook", {})
    competitors = scraping_data.get("competitors", [])
    
    ig_followers = ig.get("followers", 0) or 0
    fb_followers = fb.get("followers", 0) or 0
    gb_reviews = gb.get("reviews_count", 0) or 0
    gb_rating = gb.get("rating") or "N/A"
    n_competitors = len(competitors)
    indexed = scraping_data.get("indexed_pages", {}).get("total", 0)

    stats_html = f'''
    <div class="detail-box">
        <div class="detail-box-title">Dati Chiave</div>
        <div style="display:flex;justify-content:space-between;flex-wrap:wrap;">
            <div style="width:30%;margin-bottom:12px;">
                <div style="font-size:22px;font-weight:800;color:#F90100;">{ig_followers + fb_followers}</div>
                <div style="font-size:10px;color:#888;text-transform:uppercase;">Follower Totali</div>
            </div>
            <div style="width:30%;margin-bottom:12px;">
                <div style="font-size:22px;font-weight:800;color:#F90100;">{gb_reviews}</div>
                <div style="font-size:10px;color:#888;text-transform:uppercase;">Recensioni Google</div>
            </div>
            <div style="width:30%;margin-bottom:12px;">
                <div style="font-size:22px;font-weight:800;color:#F90100;">{n_competitors}</div>
                <div style="font-size:10px;color:#888;text-transform:uppercase;">Competitor Trovati</div>
            </div>
            <div style="width:30%;">
                <div style="font-size:22px;font-weight:800;color:#F90100;">{indexed}</div>
                <div style="font-size:10px;color:#888;text-transform:uppercase;">Pagine Indicizzate</div>
            </div>
            <div style="width:30%;">
                <div style="font-size:22px;font-weight:800;color:#F90100;">{gb_rating}</div>
                <div style="font-size:10px;color:#888;text-transform:uppercase;">Rating Google</div>
            </div>
            <div style="width:30%;">
                <div style="font-size:22px;font-weight:800;color:#F90100;">{ig.get("engagement_rate", 0) or 0}%</div>
                <div style="font-size:10px;color:#888;text-transform:uppercase;">Engagement IG</div>
            </div>
        </div>
    </div>'''

    return f'''
    <div class="dashboard">
        <div class="dashboard-title">Dashboard Digitale</div>
        <div class="badges-row">{badges_html}</div>
        <div class="bars-section">{bars_html}</div>
        {stats_html}
    </div>'''


def _replace_emoji_with_badges(html: str) -> str:
    replacements = {
        '📊': '<span style="display:inline-block;background:#F90100;color:white;width:28px;height:28px;border-radius:50%;text-align:center;line-height:28px;font-size:14px;font-weight:700;margin-right:8px;vertical-align:middle;">1</span>',
        '🔍': '<span style="display:inline-block;background:#F90100;color:white;width:28px;height:28px;border-radius:50%;text-align:center;line-height:28px;font-size:14px;font-weight:700;margin-right:8px;vertical-align:middle;">2</span>',
        '⚔️': '<span style="display:inline-block;background:#F90100;color:white;width:28px;height:28px;border-radius:50%;text-align:center;line-height:28px;font-size:14px;font-weight:700;margin-right:8px;vertical-align:middle;">3</span>',
        '⚔': '<span style="display:inline-block;background:#F90100;color:white;width:28px;height:28px;border-radius:50%;text-align:center;line-height:28px;font-size:14px;font-weight:700;margin-right:8px;vertical-align:middle;">3</span>',
        '🤖': '<span style="display:inline-block;background:#2980B9;color:white;width:28px;height:28px;border-radius:50%;text-align:center;line-height:28px;font-size:14px;font-weight:700;margin-right:8px;vertical-align:middle;">4</span>',
        '✅': '<span style="display:inline-block;background:#27AE60;color:white;width:28px;height:28px;border-radius:50%;text-align:center;line-height:28px;font-size:14px;font-weight:700;margin-right:8px;vertical-align:middle;">5</span>',
        '🚀': '<span style="display:inline-block;background:#F90100;color:white;width:28px;height:28px;border-radius:50%;text-align:center;line-height:28px;font-size:14px;font-weight:700;margin-right:8px;vertical-align:middle;">6</span>',
        '📞': '<span style="display:inline-block;background:#666;color:white;width:28px;height:28px;border-radius:50%;text-align:center;line-height:28px;font-size:14px;font-weight:700;margin-right:8px;vertical-align:middle;">7</span>',
    }
    for emoji, badge in replacements.items():
        html = html.replace(emoji, badge)
    return html


def _convert_markdown_to_html(md_text: str, data: dict) -> str:
    # Pulisci solo tag pericolosi
    md_text = re.sub(r'<(div|span|section)[^>]*>', '', md_text)
    md_text = re.sub(r'</(div|span|section)>', '', md_text)
    
    # Converti markdown in HTML
    html = markdown.markdown(md_text, extensions=['tables', 'fenced_code', 'nl2br'])
    
    # Emoji -> Badges
    html = _replace_emoji_with_badges(html)
    
    # Info boxes
    box_patterns = [
        (r'<p>🚨(.*?)</p>', 'box-critical'),
        (r'<p>✅(.*?)</p>', 'box-success'),
        (r'<p>💡(.*?)</p>', 'box-warning'),
        (r'<p>🤖(.*?)</p>', 'box-ai'),
    ]
    for pattern, css_class in box_patterns:
        html = re.sub(pattern, f'<div class="info-box {css_class}">\\1</div>', html, flags=re.DOTALL)
    
    # Premium teaser instead of CTA button
    premium_html = '''
    <div class="premium-teaser">
        <h3>La Diagnosi Premium: 50 Pagine di Strategia</h3>
        <p>Questa analisi gratuita ha fotografato la situazione. La Diagnosi Premium entra nel dettaglio e costruisce la strategia.</p>
        <div class="premium-features">
            <div class="premium-feat">
                <div class="premium-feat-icon">&#x1F4CB;</div>
                <div class="premium-feat-text"><strong>Piano 90 Giorni</strong><br>Settimana per settimana, azione per azione</div>
            </div>
            <div class="premium-feat">
                <div class="premium-feat-icon">&#x1F4C5;</div>
                <div class="premium-feat-text"><strong>Calendario Editoriale</strong><br>30 giorni di post pronti all'uso</div>
            </div>
            <div class="premium-feat">
                <div class="premium-feat-icon">&#x1F4B0;</div>
                <div class="premium-feat-text"><strong>Stima ROI</strong><br>Quanto puoi guadagnare investendo nel digitale</div>
            </div>
        </div>
        <div class="premium-features">
            <div class="premium-feat">
                <div class="premium-feat-icon">&#x1F916;</div>
                <div class="premium-feat-text"><strong>Analisi AI Avanzata</strong><br>Automazioni su misura per il tuo settore</div>
            </div>
            <div class="premium-feat">
                <div class="premium-feat-icon">&#x2694;</div>
                <div class="premium-feat-text"><strong>Mappa Competitiva</strong><br>SWOT digitale vs i tuoi concorrenti</div>
            </div>
            <div class="premium-feat">
                <div class="premium-feat-icon">&#x1F4B3;</div>
                <div class="premium-feat-text"><strong>Preventivo Personalizzato</strong><br>Costruito sulle tue priorita e il tuo budget</div>
            </div>
        </div>
        <div class="premium-price">99&euro;</div>
        <div class="premium-price-note">una tantum &bull; valore di mercato oltre 1.000&euro;</div>
        <p style="margin-top:15px;font-size:12px;color:#999;">Controlla la tua email: troverai il link per sbloccare la versione Premium.</p>
    </div>'''
    
    html = html.replace("{{CHECKOUT_PLACEHOLDER}}", premium_html)
    
    return html


# ══════════════════════════════════════════════════════════
# PREMIUM PDF GENERATOR
# ══════════════════════════════════════════════════════════


def _generate_premium_dashboard(scores: dict) -> str:
    """Genera dashboard grafica per il PDF premium."""
    if not scores:
        return ""
    
    score_map = [
        ("Sito Web", "sito", "🌐"),
        ("Velocità Mobile", "velocita_mobile", "📱"),
        ("Velocità Desktop", "velocita_desktop", "💻"),
        ("SEO", "seo_score", "🔍"),
        ("Accessibilità", "accessibilita", "♿"),
        ("Best Practices", "best_practices", "✅"),
        ("Google Business", "google_business", "📍"),
        ("Facebook", "facebook", "👥"),
        ("Instagram", "instagram", "📸"),
        ("Reputazione AI", "reputazione_ai", "🤖"),
    ]
    
    globale = scores.get("globale", 0)
    g_color = "#E74C3C" if globale < 40 else "#F39C12" if globale < 70 else "#27AE60"
    
    bars = ""
    for label, key, icon in score_map:
        val = scores.get(key, 0)
        color = "#E74C3C" if val < 40 else "#F39C12" if val < 70 else "#27AE60"
        bars += f"""
        <div style="display:flex;align-items:center;margin-bottom:8px;">
            <div style="width:25px;text-align:center;font-size:14px;">{icon}</div>
            <div style="width:140px;font-size:10px;font-weight:600;color:#333;padding-left:8px;">{label}</div>
            <div style="flex:1;background:#e8e8e8;border-radius:8px;height:18px;margin:0 10px;overflow:hidden;">
                <div style="width:{val}%;background:{color};height:100%;border-radius:8px;transition:width 0.3s;"></div>
            </div>
            <div style="width:45px;text-align:right;font-size:11px;font-weight:700;color:{color};">{val}/100</div>
        </div>"""
    
    return f"""
    <div style="page-break-after:always;padding:1.5cm 0;">
        <h1 style="text-align:center;color:#1a1a2e;font-size:22pt;margin-bottom:0.3cm;">PANORAMICA PUNTEGGI</h1>
        <div style="text-align:center;margin-bottom:1cm;">
            <div style="display:inline-block;border:6px solid {g_color};border-radius:50%;width:100px;height:100px;line-height:100px;text-align:center;">
                <span style="font-size:36px;font-weight:800;color:{g_color};">{globale}</span>
            </div>
            <div style="font-size:11px;color:#666;margin-top:8px;font-weight:600;">PUNTEGGIO GLOBALE DIGIDENTITY</div>
        </div>
        <div style="max-width:480px;margin:0 auto;">
            {bars}
        </div>
        <div style="text-align:center;margin-top:1cm;">
            <div style="display:inline-block;padding:8px 20px;border-radius:6px;font-size:10px;font-weight:600;color:white;background:{g_color};">
                {"CRITICO — Intervento urgente" if globale < 40 else "SUFFICIENTE — Margini di miglioramento" if globale < 70 else "BUONO — Ottimizzazione avanzata"}
            </div>
        </div>
    </div>"""

def markdown_to_pdf(markdown_text: str, output_path: str, report_type: str = "free",
                    company_name: str = "", scraping_data: dict = None):
    """
    Genera PDF da markdown. Supporta sia FREE che PREMIUM.
    Per PREMIUM usa un layout esteso con tutte le sezioni.
    """
    import markdown
    from weasyprint import HTML
    from datetime import datetime

    if report_type == "free":
        # Usa la funzione esistente
        return generate_pdf(markdown_text, output_path, scraping_data, company_name)

    # ── PREMIUM ──
    _mesi = ["gennaio","febbraio","marzo","aprile","maggio","giugno",
             "luglio","agosto","settembre","ottobre","novembre","dicembre"]
    _now = datetime.now()
    date_str = f"{_now.day} {_mesi[_now.month-1]} {_now.year}"

    # Estrai punteggio globale dal markdown
    import re as _re
    _score_match = _re.search(r"Punteggio DigIdentity[:\s]*(\d+)/100", markdown_text)
    _global_score = _score_match.group(1) if _score_match else ""

    # Converti markdown in HTML
    md_extensions = [
        'tables', 'fenced_code', 'nl2br', 'sane_lists',
        'smarty', 'toc', 'attr_list'
    ]
    html_body = markdown.markdown(markdown_text, extensions=md_extensions)

    # CSS Premium
    css = _get_report_css()
    premium_css = """
    <style>
    """ + css + """

    /* Premium overrides */
    @page {
        size: A4;
        margin: 2cm 2.5cm;
        @bottom-center {
            content: "Diagnosi Premium — """ + company_name + """ — Pagina " counter(page) " di " counter(pages);
            font-size: 8pt;
            color: #999;
        }
    }

    .premium-cover {
        page-break-after: always;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: 90vh;
        text-align: center;
        background: linear-gradient(135deg, #1a0000 0%, #8B0000 40%, #F90100 100%);
        color: white;
        padding: 3cm;
        margin: -2cm -2.5cm 0 -2.5cm;
    }

    .premium-cover h1 {
        font-size: 32pt;
        font-weight: 800;
        margin-bottom: 0.5cm;
        letter-spacing: 1px;
    }

    .premium-cover h2 {
        font-size: 18pt;
        font-weight: 400;
        opacity: 0.9;
        margin-bottom: 1cm;
    }

    .premium-cover .date {
        font-size: 11pt;
        opacity: 0.7;
        margin-top: 2cm;
    }

    .premium-cover .badge {
        display: inline-block;
        background: #e94560;
        color: white;
        padding: 8px 24px;
        border-radius: 20px;
        font-size: 11pt;
        font-weight: 600;
        margin-top: 1cm;
    }

    .premium-cover img {
        max-width: 180px;
        margin-bottom: 1.5cm;
    }

    h1 { color: #1a1a2e; font-size: 20pt; margin-top: 1.5cm; page-break-after: avoid; }
    h2 { color: #0f3460; font-size: 16pt; margin-top: 1cm; page-break-after: avoid; }
    h3 { color: #e94560; font-size: 13pt; margin-top: 0.8cm; page-break-after: avoid; }
    p { font-size: 10.5pt; line-height: 1.7; text-align: justify; }
    hr { border: none; border-top: 2px solid #e94560; margin: 1.5cm 0; page-break-before: always; }
    table { width: 100%; border-collapse: collapse; margin: 0.5cm 0; font-size: 9.5pt; }
    th { background: #1a1a2e; color: white; padding: 8px 12px; text-align: left; }
    td { padding: 8px 12px; border-bottom: 1px solid #eee; }
    tr:nth-child(even) { background: #f8f9fa; }
    strong { color: #1a1a2e; }
    </style>
    """

    # Logo path
    logo_path = "/app/assets/logo_light.png"

    # Cover page
    cover_html = f"""
    <div class="premium-cover">
        <img src="{logo_path}" alt="DigIdentity">
        <h1>DIAGNOSI DIGITALE PREMIUM</h1>
        <h2>{company_name}</h2>
        <div class="badge">REPORT COMPLETO</div>
        {f'<div style="margin-top:1.5cm;font-size:48pt;font-weight:800;color:#e94560;">{_global_score}<span style="font-size:20pt;opacity:0.7">/100</span></div><div style="font-size:12pt;opacity:0.8;margin-top:0.3cm;">PUNTEGGIO DIGIDENTITY</div>' if _global_score else ''}
        <div class="date">{date_str}</div>
    </div>
    """


    # Genera sommario dalle intestazioni H1/H2
    import re as _re2
    _headings = _re2.findall(r'<(h[12])[^>]*>(.*?)</\1>', html_body, _re2.IGNORECASE)
    _toc_items = []
    for _tag, _title in _headings:
        _clean = _re2.sub(r'<[^>]+>', '', _title).strip()
        if _clean and len(_clean) > 3:
            _indent = 'margin-left:0' if _tag.lower() == 'h1' else 'margin-left:20px'
            _size = '12pt' if _tag.lower() == 'h1' else '10.5pt'
            _weight = '700' if _tag.lower() == 'h1' else '400'
            _toc_items.append(f'<div style="{_indent};font-size:{_size};font-weight:{_weight};padding:4px 0;border-bottom:1px dotted #ddd;">{_clean}</div>')
    _toc_html = ''
    if _toc_items:
        _toc_html = '<div style="page-break-after:always;padding-top:2cm;">'
        _toc_html += '<h1 style="font-size:24pt;color:#1a1a2e;border-bottom:3px solid #e94560;padding-bottom:10px;margin-bottom:25px;">SOMMARIO</h1>'
        _toc_html += ''.join(_toc_items)
        _toc_html += '</div>'


    # Genera dashboard grafica premium
    _premium_scores = {}
    import re as _re3
    for _sk, _sp in [("sito","Sito Web[:\\s]*(\\d+)"),("velocita_mobile","Velocit.*Mobile[:\\s]*(\\d+)"),
                      ("velocita_desktop","Velocit.*Desktop[:\\s]*(\\d+)"),("seo_score","SEO[:\\s]*(\\d+)"),
                      ("accessibilita","Accessibilit.*[:\\s]*(\\d+)"),("best_practices","Best Practices[:\\s]*(\\d+)"),
                      ("google_business","Google Business[:\\s]*(\\d+)"),("facebook","Facebook[:\\s]*(\\d+)"),
                      ("instagram","Instagram[:\\s]*(\\d+)"),("reputazione_ai","Reputazione AI[:\\s]*(\\d+)"),
                      ("globale","PUNTEGGIO COMPLESSIVO.*?(\\d+)")]:
        _sm = _re3.search(_sp, markdown_text)
        if _sm:
            _premium_scores[_sk] = int(_sm.group(1))
    if not _premium_scores.get("globale") and _global_score:
        _premium_scores["globale"] = int(_global_score)
    _dashboard_html = _generate_premium_dashboard(_premium_scores) if _premium_scores else ""

    # Assembla HTML completo
    full_html = f"""<!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="utf-8">
        {premium_css}
    </head>
    <body>
        {cover_html}
        {_toc_html}
        {_dashboard_html}
        <div class="report-content">{html_body}</div>
    </body>
    </html>
    """

    # Genera PDF
    HTML(string=full_html).write_pdf(output_path)
    return output_path
