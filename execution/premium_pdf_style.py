"""
DigIdentity Premium PDF — Dark Theme Style
Stile identico all'HTML della diagnosi premium.
"""

def get_premium_css():
    """CSS dark theme per il PDF premium — identico all'HTML."""
    return """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    @page {
        size: A4;
        margin: 15mm 18mm 20mm 18mm;
        background: #0e0e0e;
        @bottom-center {
            content: none;
        }
    }
    @page :first { margin: 0; }

    :root {
        --bg-primary: #0e0e0e;
        --bg-card: #1a1a1a;
        --bg-card-alt: #141414;
        --text-primary: #e0e0e0;
        --text-secondary: #999999;
        --text-muted: #666666;
        --accent: #F90100;
        --accent-dark: #c70100;
        --green: #00c853;
        --orange: #ff8c00;
        --yellow: #f5c518;
        --red: #F90100;
        --border: #2a2a2a;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
        font-family: 'Inter', -apple-system, sans-serif;
        background: #0e0e0e;
        color: #e0e0e0;
        font-size: 10pt;
        line-height: 1.7;
    }

    /* ── COVER ── */
    .premium-cover {
        page-break-after: always;
        background: linear-gradient(160deg, #0a0a0a 0%, #1a0000 40%, #2d0000 100%);
        color: white;
        text-align: center;
        padding: 60mm 25mm 40mm 25mm;
        min-height: 297mm;
        position: relative;
    }
    .premium-cover::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: radial-gradient(ellipse at 30% 20%, rgba(249,1,0,0.08) 0%, transparent 70%);
    }
    .cover-logo {
        position: relative;
        z-index: 1;
        margin-bottom: 15mm;
    }
    .cover-logo img {
        max-width: 200px;
        opacity: 0.9;
    }
    .cover-badge {
        display: inline-block;
        border: 2px solid rgba(249,1,0,0.6);
        color: #F90100;
        padding: 6px 24px;
        border-radius: 20px;
        font-size: 9pt;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 12mm;
    }
    .cover-title {
        font-size: 32pt;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 3px;
        color: white;
        margin-bottom: 5mm;
        line-height: 1.2;
    }
    .cover-subtitle {
        font-size: 10pt;
        color: rgba(255,255,255,0.5);
        text-transform: uppercase;
        letter-spacing: 4px;
        margin-bottom: 15mm;
    }
    .cover-company {
        font-size: 22pt;
        font-weight: 700;
        color: #F90100;
        margin-bottom: 8mm;
    }
    .cover-meta {
        font-size: 9pt;
        color: rgba(255,255,255,0.5);
        line-height: 2;
    }
    .cover-score {
        margin-top: 12mm;
    }
    .cover-score-number {
        font-size: 54pt;
        font-weight: 800;
        color: #F90100;
        line-height: 1;
    }
    .cover-score-label {
        font-size: 9pt;
        color: rgba(255,255,255,0.5);
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-top: 3mm;
    }
    .cover-line {
        width: 60px;
        height: 3px;
        background: #F90100;
        margin: 8mm auto;
    }

    /* ── SOMMARIO ── */
    .toc-page {
        page-break-after: always;
        padding: 15mm 0;
    }
    .toc-title {
        font-size: 18pt;
        font-weight: 800;
        color: #F90100;
        text-transform: uppercase;
        letter-spacing: 2px;
        border-bottom: 2px solid #2a2a2a;
        padding-bottom: 4mm;
        margin-bottom: 8mm;
    }
    .toc-item {
        padding: 3mm 0;
        border-bottom: 1px solid #1a1a1a;
        font-size: 10pt;
        color: #e0e0e0;
    }
    .toc-item-sub {
        padding: 2mm 0 2mm 8mm;
        font-size: 9pt;
        color: #999;
        border-bottom: 1px solid #141414;
    }

    /* ── DASHBOARD ── */
    .dashboard-page {
        page-break-after: always;
        padding: 10mm 0;
    }
    .dashboard-title {
        font-size: 14pt;
        font-weight: 800;
        color: #F90100;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-align: center;
        margin-bottom: 8mm;
    }
    .score-ring-container {
        text-align: center;
        margin-bottom: 10mm;
    }
    .metric-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 4mm;
        justify-content: center;
    }
    .metric-card {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 8px;
        padding: 5mm;
        width: 48%;
        text-align: center;
    }
    .metric-card-label {
        font-size: 7pt;
        color: #999;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 2mm;
    }
    .metric-card-value {
        font-size: 20pt;
        font-weight: 800;
    }
    .metric-card-desc {
        font-size: 7pt;
        color: #666;
        margin-top: 1mm;
    }
    .color-red { color: #F90100; }
    .color-green { color: #00c853; }
    .color-orange { color: #ff8c00; }
    .color-yellow { color: #f5c518; }

    /* ── PROGRESS BARS ── */
    .bar-row {
        display: flex;
        align-items: center;
        margin-bottom: 3mm;
    }
    .bar-label {
        width: 35%;
        font-size: 8pt;
        font-weight: 600;
        color: #e0e0e0;
    }
    .bar-track {
        flex: 1;
        height: 8px;
        background: #2a2a2a;
        border-radius: 4px;
        margin: 0 3mm;
        overflow: hidden;
    }
    .bar-fill {
        height: 100%;
        border-radius: 4px;
    }
    .bar-fill-red { background: linear-gradient(90deg, #F90100, #ff4444); }
    .bar-fill-orange { background: linear-gradient(90deg, #ff8c00, #ffaa33); }
    .bar-fill-yellow { background: linear-gradient(90deg, #f5c518, #ffe066); }
    .bar-fill-green { background: linear-gradient(90deg, #00c853, #69f0ae); }
    .bar-value {
        width: 12%;
        text-align: right;
        font-size: 8pt;
        font-weight: 700;
    }

    /* ── SECTIONS ── */
    .section {
        page-break-before: always;
        padding: 8mm 0;
    }
    .section:first-of-type {
        page-break-before: avoid;
    }
    .section-header {
        border-bottom: 2px solid #F90100;
        padding-bottom: 4mm;
        margin-bottom: 6mm;
    }
    .section-number {
        font-size: 8pt;
        color: #F90100;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 600;
    }
    .section-title {
        font-size: 16pt;
        font-weight: 800;
        color: #ffffff;
        margin-top: 2mm;
    }

    /* ── MINI RING (in sections) ── */
    .section-score-box {
        display: flex;
        align-items: center;
        gap: 5mm;
        margin: 5mm 0;
        background: #141414;
        border: 1px solid #2a2a2a;
        border-radius: 8px;
        padding: 4mm 6mm;
    }
    .section-score-label {
        font-size: 8pt;
        color: #999;
        line-height: 1.5;
    }
    .section-score-label strong {
        color: #e0e0e0;
    }

    /* ── CONTENT TYPOGRAPHY ── */
    .report-content h1 {
        font-size: 16pt;
        font-weight: 800;
        color: #ffffff;
        border-bottom: 2px solid #F90100;
        padding-bottom: 3mm;
        margin-top: 10mm;
        margin-bottom: 5mm;
        page-break-after: avoid;
    }
    .report-content h2 {
        font-size: 13pt;
        font-weight: 700;
        color: #F90100;
        margin-top: 8mm;
        margin-bottom: 3mm;
        page-break-after: avoid;
    }
    .report-content h3 {
        font-size: 11pt;
        font-weight: 700;
        color: #e0e0e0;
        margin-top: 6mm;
        margin-bottom: 2mm;
        padding: 3mm 4mm;
        background: #1a1a1a;
        border-left: 3px solid #F90100;
        border-radius: 0 4px 4px 0;
        page-break-after: avoid;
    }
    .report-content p {
        font-size: 10pt;
        line-height: 1.8;
        margin-bottom: 3mm;
        text-align: justify;
        color: #e0e0e0;
    }
    .report-content strong {
        color: #ffffff;
        font-weight: 700;
    }
    .report-content a {
        color: #F90100;
        text-decoration: none;
    }

    /* ── TABLES ── */
    .report-content table {
        width: 100%;
        border-collapse: collapse;
        margin: 5mm 0;
        font-size: 8pt;
        border-radius: 6px;
        overflow: hidden;
    }
    .report-content th {
        background: #F90100;
        color: white;
        padding: 3mm 4mm;
        text-align: left;
        font-weight: 600;
        font-size: 8pt;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .report-content td {
        padding: 3mm 4mm;
        border-bottom: 1px solid #2a2a2a;
        color: #e0e0e0;
        background: #1a1a1a;
    }
    .report-content tr:nth-child(even) td {
        background: #141414;
    }

    /* ── BLOCKQUOTES ── */
    .report-content blockquote {
        border-left: 3px solid #F90100;
        background: #1a1a1a;
        padding: 4mm 5mm;
        margin: 4mm 0;
        border-radius: 0 6px 6px 0;
        font-style: italic;
        color: #999;
    }

    /* ── LISTS ── */
    .report-content ul {
        padding-left: 0;
        list-style: none;
        margin: 3mm 0;
    }
    .report-content ul li {
        padding: 2mm 0 2mm 6mm;
        position: relative;
        line-height: 1.7;
        font-size: 10pt;
    }
    .report-content ul li::before {
        content: '';
        position: absolute;
        left: 0;
        top: 5mm;
        width: 5px;
        height: 5px;
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
        margin-bottom: 4mm;
        padding: 4mm 5mm 4mm 14mm;
        background: #1a1a1a;
        border-radius: 6px;
        border-left: 3px solid #F90100;
        position: relative;
        font-size: 10pt;
    }
    .report-content ol > li::before {
        content: counter(item);
        position: absolute;
        left: 4mm;
        top: 4mm;
        background: #F90100;
        color: white;
        font-weight: 700;
        font-size: 8pt;
        width: 18px;
        height: 18px;
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    /* ── INFO BOXES ── */
    .info-box {
        padding: 4mm 5mm;
        margin: 4mm 0;
        border-radius: 6px;
        border-left: 4px solid;
        font-size: 9pt;
        background: #1a1a1a;
    }
    .box-critical { border-color: #F90100; }
    .box-success { border-color: #00c853; }
    .box-warning { border-color: #ff8c00; }

    /* ── COMPETITOR CARDS ── */
    .competitor-card {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 8px;
        padding: 5mm;
        margin: 4mm 0;
        page-break-inside: avoid;
    }
    .competitor-name {
        font-size: 11pt;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 2mm;
    }
    .competitor-rating {
        font-size: 9pt;
        color: #f5c518;
        margin-bottom: 2mm;
    }

    /* ── FOOTER ── */
    .page-footer {
        font-size: 7pt;
        color: #666;
        text-align: center;
        padding-top: 5mm;
        border-top: 1px solid #2a2a2a;
        margin-top: 10mm;
    }

    /* ── CTA BOX ── */
    .cta-box {
        background: linear-gradient(135deg, #1a0000, #2d0000);
        border: 2px solid #F90100;
        border-radius: 12px;
        padding: 8mm;
        text-align: center;
        margin: 8mm 0;
        page-break-inside: avoid;
    }
    .cta-box h3 {
        color: #F90100;
        font-size: 14pt;
        background: none;
        border: none;
        padding: 0;
        margin-bottom: 3mm;
    }
    .cta-box p {
        color: #999;
        text-align: center;
        font-size: 9pt;
    }
    .cta-price {
        font-size: 28pt;
        font-weight: 800;
        color: #F90100;
        margin: 4mm 0;
    }
    .cta-whatsapp {
        display: inline-block;
        background: #F90100;
        color: white;
        padding: 3mm 8mm;
        border-radius: 6px;
        font-weight: 700;
        font-size: 10pt;
        text-decoration: none;
        margin-top: 3mm;
    }

    /* ── KEYWORD GROUPS ── */
    .keyword-group {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 8px;
        padding: 5mm;
        margin: 4mm 0;
        page-break-inside: avoid;
    }
    .keyword-group-title {
        font-size: 9pt;
        font-weight: 700;
        color: #F90100;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 3mm;
    }
    .keyword-tag {
        display: inline-block;
        background: #0e0e0e;
        border: 1px solid #2a2a2a;
        color: #e0e0e0;
        padding: 1mm 3mm;
        border-radius: 4px;
        font-size: 8pt;
        margin: 1mm;
    }

    /* ── CHI SIAMO ── */
    .chi-siamo {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 8px;
        padding: 6mm;
        margin: 6mm 0;
    }
    .chi-siamo h2 {
        color: #F90100;
    }
    .chi-siamo p {
        color: #999;
        font-size: 9pt;
    }

    /* ── PRINT HELPERS ── */
    .page-break { page-break-after: always; }
    .avoid-break { page-break-inside: avoid; }
    """


def generate_premium_cover(company_name, date_str, location, global_score):
    """Genera la cover page premium dark."""
    score_color = "#F90100" if global_score < 40 else "#ff8c00" if global_score < 60 else "#f5c518" if global_score < 75 else "#00c853"
    return f'''
    <div class="premium-cover">
        <div class="cover-logo">
            <img src="/app/assets/logo_light.png" alt="DigIdentity Agency">
        </div>
        <div class="cover-badge">Diagnosi Premium</div>
        <div class="cover-title">DIAGNOSI DIGITALE<br>PREMIUM</div>
        <div class="cover-subtitle">Report Completo</div>
        <div class="cover-line"></div>
        <div class="cover-company">{company_name}</div>
        <div class="cover-meta">
            {location}<br>
            {date_str}
        </div>
        <div class="cover-score">
            <div class="cover-score-number" style="color:{score_color}">{global_score}</div>
            <div class="cover-score-label">Punteggio DigIdentity &bull; /100</div>
        </div>
    </div>
    '''


def generate_premium_dashboard(scores):
    """Genera la pagina dashboard con ring e barre — stile dark."""
    if not scores:
        return ""

    globale = scores.get("globale", 0)
    g_color = "#F90100" if globale < 40 else "#ff8c00" if globale < 60 else "#f5c518" if globale < 75 else "#00c853"

    # SVG ring per punteggio globale
    circumference = 2 * 3.14159 * 45
    offset = circumference - (globale / 100) * circumference
    ring_svg = f'''
    <svg width="120" height="120" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r="45" fill="none" stroke="#2a2a2a" stroke-width="8"/>
        <circle cx="60" cy="60" r="45" fill="none" stroke="{g_color}" stroke-width="8"
            stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"
            transform="rotate(-90 60 60)" stroke-linecap="round"/>
        <text x="60" y="55" text-anchor="middle" font-size="28" font-weight="800" fill="{g_color}">{globale}</text>
        <text x="60" y="72" text-anchor="middle" font-size="9" fill="#999">/100</text>
    </svg>
    '''

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

    # Metric cards
    cards_html = ''
    for label, key, icon in score_map:
        val = scores.get(key, 0)
        if val < 40:
            color_class = "color-red"
            bar_class = "bar-fill-red"
        elif val < 60:
            color_class = "color-orange"
            bar_class = "bar-fill-orange"
        elif val < 75:
            color_class = "color-yellow"
            bar_class = "bar-fill-yellow"
        else:
            color_class = "color-green"
            bar_class = "bar-fill-green"

        cards_html += f'''
        <div class="metric-card">
            <div class="metric-card-label">{icon} {label}</div>
            <div class="metric-card-value {color_class}">{val}</div>
            <div style="margin-top:2mm;">
                <div class="bar-track"><div class="bar-fill {bar_class}" style="width:{val}%"></div></div>
            </div>
        </div>'''

    # Giudizio
    if globale < 30:
        giudizio = "Critico — Intervento urgente necessario"
    elif globale < 50:
        giudizio = "Insufficiente — ma con potenziale di crescita enorme"
    elif globale < 65:
        giudizio = "Sufficiente — con ampio margine di crescita"
    elif globale < 80:
        giudizio = "Buono — con margine per eccellere"
    else:
        giudizio = "Eccellente — mantieni e ottimizza"

    return f'''
    <div class="dashboard-page">
        <div class="dashboard-title">Dashboard — I Tuoi Numeri</div>
        <div class="score-ring-container">
            {ring_svg}
            <div style="font-size:9pt;color:{g_color};font-weight:700;margin-top:3mm;">{giudizio}</div>
        </div>
        <div class="metric-grid">
            {cards_html}
        </div>
    </div>
    '''


def generate_section_score_svg(score, size=60):
    """Genera un mini SVG ring per il punteggio di sezione."""
    if score < 40:
        color = "#F90100"
    elif score < 60:
        color = "#ff8c00"
    elif score < 75:
        color = "#f5c518"
    else:
        color = "#00c853"

    circumference = 2 * 3.14159 * 22
    offset = circumference - (score / 100) * circumference

    return f'''
    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
        <circle cx="{size//2}" cy="{size//2}" r="22" fill="none" stroke="#2a2a2a" stroke-width="5"/>
        <circle cx="{size//2}" cy="{size//2}" r="22" fill="none" stroke="{color}" stroke-width="5"
            stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"
            transform="rotate(-90 {size//2} {size//2})" stroke-linecap="round"/>
        <text x="{size//2}" y="{size//2 + 3}" text-anchor="middle" font-size="15" font-weight="800" fill="{color}">{score}</text>
    </svg>
    '''
