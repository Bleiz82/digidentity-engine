"""
DigIdentity — HTML Report Generator
Popola il template HTML dinamico con i dati del lead e le sezioni generate da Claude.
"""
import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "html_templates"


def _score_color(score: int) -> str:
    """Ritorna la classe colore CSS per un punteggio."""
    if score >= 70:
        return "green"
    elif score >= 50:
        return "yellow"
    elif score >= 30:
        return "orange"
    else:
        return "red"


def _score_css_class(score: int) -> str:
    """Ritorna la classe CSS per il badge del punteggio."""
    if score >= 70:
        return "score-high"
    elif score >= 40:
        return "score-mid"
    else:
        return "score-low"


def _progress_class(score: int) -> str:
    """Ritorna la classe CSS per la progress bar."""
    if score >= 70:
        return "progress-high"
    elif score >= 40:
        return "progress-mid"
    elif score > 0:
        return "progress-low"
    else:
        return "progress-na"


def _dashoffset(score: int) -> int:
    """Calcola lo stroke-dashoffset per il mini-ring SVG (226 = vuoto, 0 = pieno)."""
    return max(0, 226 - int(226 * score / 100))


def _ps_ring_svg(value: int, label: str) -> str:
    """Genera un mini-ring SVG per i punteggi PageSpeed."""
    if value is None:
        value = 0
    v = int(value)
    if v >= 70:
        color = "#4caf50"
    elif v >= 50:
        color = "#ffc107"
    else:
        color = "#f44336"
    r = 28
    circ = round(2 * 3.14159 * r, 1)
    offset = round(circ - (v / 100) * circ, 1)
    return f'''<div class="ps-ring-wrap">
      <svg width="70" height="70" viewBox="0 0 70 70">
        <circle cx="35" cy="35" r="{r}" fill="none" stroke="#222" stroke-width="5"/>
        <circle cx="35" cy="35" r="{r}" fill="none" stroke="{color}" stroke-width="5"
          stroke-dasharray="{circ}" stroke-dashoffset="{offset}"
          transform="rotate(-90 35 35)" stroke-linecap="round"/>
        <text x="35" y="35" text-anchor="middle" dominant-baseline="middle"
          font-size="14" font-weight="800" fill="{color}" font-family="monospace">{v}</text>
      </svg>
      <div class="ps-ring-label">{label}</div>
    </div>'''


def _geo_gauge_svg(score: int) -> str:
    """Genera il gauge SVG per il GEO score."""
    if score is None:
        score = 0
    v = int(score)
    if v >= 70:
        color = "#4caf50"
    elif v >= 50:
        color = "#ffc107"
    else:
        color = "#f44336"
    r = 45
    circ = round(2 * 3.14159 * r, 1)
    offset = round(circ - (v / 100) * circ, 1)
    return f'''<svg width="110" height="110" viewBox="0 0 110 110">
      <circle cx="55" cy="55" r="{r}" fill="none" stroke="#222" stroke-width="7"/>
      <circle cx="55" cy="55" r="{r}" fill="none" stroke="{color}" stroke-width="7"
        stroke-dasharray="{circ}" stroke-dashoffset="{offset}"
        transform="rotate(-90 55 55)" stroke-linecap="round"/>
      <text x="55" y="50" text-anchor="middle" dominant-baseline="middle"
        font-size="22" font-weight="800" fill="{color}" font-family="monospace">{v}</text>
      <text x="55" y="68" text-anchor="middle"
        font-size="9" fill="#999">/100</text>
    </svg>'''


def _geo_level_desc(score: int) -> tuple:
    """Ritorna (level, description) per il GEO score."""
    if score >= 80:
        return ("Ottimo", "La tua attività è ben strutturata per apparire anche su ChatGPT, Gemini e Perplexity.")
    elif score >= 60:
        return ("Discreto", "La tua attività è parzialmente visibile sui motori AI. Con pochi interventi puoi migliorare significativamente.")
    elif score >= 40:
        return ("Insufficiente", "La tua attività è quasi invisibile su ChatGPT e Gemini. I clienti che usano questi strumenti non ti trovano.")
    else:
        return ("Critico", "La tua attività è invisibile sui nuovi motori di ricerca AI. Ogni giorno perdi clienti che cercano i tuoi servizi su ChatGPT.")


def _verdict(score: int) -> tuple:
    """Ritorna (css_class, testo, descrizione) per il punteggio globale."""
    if score >= 80:
        return ("score-high", "Ottimo — presenza digitale solida",
                "La tua attività ha una presenza digitale forte. Con interventi mirati puoi consolidare il vantaggio competitivo.")
    elif score >= 60:
        return ("score-mid", "Discreto — buona base con margini di crescita",
                "Hai costruito delle fondamenta. Ora serve una strategia strutturata per trasformare questa base in un vantaggio competitivo misurabile.")
    elif score >= 40:
        return ("score-mid", "Insufficiente — ma con un potenziale di crescita enorme",
                "La qualità della tua attività non si riflette ancora nella presenza digitale. La buona notizia: il potenziale c'è tutto, serve solo la struttura per renderlo visibile.")
    else:
        return ("score-low", "Critico — intervento urgente necessario",
                "La tua attività è quasi invisibile online. Ogni giorno che passa, potenziali clienti cercano i tuoi servizi e trovano i competitor. Serve agire subito.")


def _build_dashboard_card(title: str, emoji: str, score: int, description: str = "") -> str:
    """Genera l'HTML per una singola card della dashboard."""
    if score == -1:  # N/D
        score_html = '<span class="dash-score score-na">N/D</span>'
        progress_html = '<div class="progress-fill progress-na" style="width: 0%;"></div>'
    else:
        css_class = _score_css_class(score)
        prog_class = _progress_class(score)
        score_html = f'<span class="dash-score {css_class}">{score}</span>'
        progress_html = f'<div class="progress-fill {prog_class}" style="width: {score}%;"></div>'

    desc_html = f'<div class="dash-card-text">{description}</div>' if description else ''

    return f'''<div class="dash-card">
        <div class="dash-card-header">
          <span class="dash-card-title">{emoji} {title}</span>
          {score_html}
        </div>
        <div class="progress-bar">{progress_html}</div>
        {desc_html}
      </div>'''


def _build_dashboard(scores: dict) -> str:
    """Genera tutte le card della dashboard."""
    cards = []
    card_defs = [
        ("Sito Web", "🌐", scores.get("sito", 0)),
        ("Velocità Mobile", "📱", scores.get("velocita_mobile", -1)),
        ("Velocità Desktop", "🖥", scores.get("velocita_desktop", -1)),
        ("SEO", "🔍", scores.get("seo_score", 0)),
        ("Accessibilità", "♿", scores.get("accessibilita", -1)),
        ("Best Practices", "⚙", scores.get("best_practices", -1)),
        ("Google Business", "📍", scores.get("google_business", 0)),
        ("Facebook", "📘", scores.get("facebook", 0)),
        ("Instagram", "📸", scores.get("instagram", 0)),
        ("Reputazione AI", "🤖", scores.get("reputazione_ai", 0)),
    ]
    for title, emoji, score in card_defs:
        # Tratta valori None come -1 (N/D)
        if score is None:
            score = -1
        cards.append(_build_dashboard_card(title, emoji, score))
    return "\n".join(cards)


def _markdown_to_html(text: str) -> str:
    """Conversione basica markdown -> HTML per il contenuto delle sezioni."""
    if not text:
        return ""

    # Se il testo contiene già tag HTML significativi, restituiscilo com'è
    if re.search(r'<(div|section|h[1-6]|table|ul|ol)\b', text):
        return text

    lines = text.split('\n')
    html_lines = []
    in_paragraph = False

    for line in lines:
        stripped = line.strip()

        # Heading h1 (# singolo) — render come h2 per navigazione
        if stripped.startswith('# ') and not stripped.startswith('## '):
            html_lines.append(f'<h2>{stripped[2:].strip()}</h2>')
            continue

        # Heading h3
        if stripped.startswith('### '):
            if in_paragraph:
                html_lines.append('</p>')
                in_paragraph = False
            html_lines.append(f'<h3>{stripped[4:]}</h3>')
            continue

        # Heading h2 (raro nelle sezioni, ma possibile)
        if stripped.startswith('## '):
            if in_paragraph:
                html_lines.append('</p>')
                in_paragraph = False
            html_lines.append(f'<h2>{stripped[3:]}</h2>')  # Render as h2 for navigation
            continue

        # Horizontal rule
        if stripped in ('---', '***', '___'):
            if in_paragraph:
                html_lines.append('</p>')
                in_paragraph = False
            html_lines.append('<hr class="sub-divider">')
            continue

        # Empty line
        if not stripped:
            if in_paragraph:
                html_lines.append('</p>')
                in_paragraph = False
            continue

        # Tabella markdown: | col1 | col2 |
        if stripped.startswith('|') and stripped.endswith('|') and stripped.count('|') >= 3:
            if in_paragraph:
                html_lines.append('</p>')
                in_paragraph = False
            # Controlla se è riga separatore |---|---|
            if re.match(r'^[\|\s\-:]+$', stripped):
                continue
            cols = [c.strip() for c in stripped.split('|') if c.strip()]
            # Se la riga successiva è un separatore, questa è l'header
            # Usiamo una euristica: se non abbiamo ancora aperto una table, apriamola
            if not any('<table' in l for l in html_lines[-3:] if isinstance(l, str)):
                html_lines.append('<table class="geo-table" style="width:100%;border-collapse:collapse;margin:12px 0;font-size:11.5px;">')
                html_lines.append('<tr>' + ''.join(f'<th style="background:#8B0000;color:#fff;padding:8px 10px;text-align:left;font-weight:700;font-size:11px;border:1px solid #333;">{c}</th>' for c in cols) + '</tr>')
            else:
                html_lines.append('<tr>' + ''.join(f'<td style="padding:7px 10px;color:#e2e8f0;border:1px solid #222;background:#1a1a2e;font-size:11.5px;">{c}</td>' for c in cols) + '</tr>')
            continue

        # Chiudi tabella aperta se la riga non è una tabella
        if html_lines and '<tr>' in str(html_lines[-1]) and not stripped.startswith('|'):
            html_lines.append('</table>')

        # Bold: **text**
        stripped = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', stripped)
        # Italic: *text*
        stripped = re.sub(r'\*(.+?)\*', r'<em>\1</em>', stripped)
        # Links: [text](url)
        stripped = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2" target="_blank">\1</a>', stripped)

        if not in_paragraph:
            html_lines.append(f'<p>{stripped}')
            in_paragraph = True
        else:
            html_lines.append(f' {stripped}')

    if in_paragraph:
        html_lines.append('</p>')

    return '\n'.join(html_lines)


def _split_section_05(text: str) -> tuple:
    """Divide la sezione 05 in Google Business e Reputazione se possibile."""
    # Cerca un separatore o heading che indica l'inizio della parte reputazione
    patterns = [
        r'(?i)(#{2,3}\s*reputazione)',
        r'(?i)(#{2,3}\s*analisi\s*ai)',
        r'(?i)(#{2,3}\s*cosa\s*dice.*ai)',
        r'(?i)(#{2,3}\s*perplexity)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            idx = match.start()
            return text[:idx].strip(), text[idx:].strip()
    # Se non trova separatore, metti tutto nella prima parte
    return text, ""


def _split_section_08(text: str) -> tuple:
    """Divide la sezione 08 in Branding e AI se possibile."""
    patterns = [
        r'(?i)(#{2,3}\s*analisi\s*ai)',
        r'(?i)(#{2,3}\s*intelligenza\s*artificiale)',
        r'(?i)(#{2,3}\s*opportunit[aà].*ai)',
        r'(?i)(#{2,3}\s*l.opportunit[aà])',
        r'(?i)(#{2,3}\s*come\s*l.ai)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            idx = match.start()
            return text[:idx].strip(), text[idx:].strip()
    return text, ""




def _build_geo_sub_bars(scraping_data: dict) -> str:
    """Costruisce le barre GEO sub-indicatori con dati reali o fallback stimato."""
    geo = scraping_data.get("geo", {})
    geo_score_obj = geo.get("geo_score", {})
    total = int(geo_score_obj.get("score", 0) or 0)

    # Prova a leggere sub-scores se presenti (scraper avanzato)
    sub = geo_score_obj.get("breakdown", {})
    accessibility = int(sub.get("accessibility", 0) or 0)
    structure     = int(sub.get("structure", 0) or 0)
    citability    = int(sub.get("citability", 0) or 0)
    authority     = int(sub.get("authority", 0) or 0)

    # Fallback: stima proporzionale dal total se breakdown mancante
    if not any([accessibility, structure, citability, authority]) and total > 0:
        accessibility = min(100, int(total * 1.2))
        structure     = min(100, int(total * 1.0))
        citability    = min(100, int(total * 0.7))
        authority     = min(100, int(total * 0.9))

    def _bar_color(v):
        if v >= 70: return ("#00c853", "progress-high")
        if v >= 40: return ("#f5c518", "progress-mid")
        return ("#F90100", "progress-low")

    def _bar(label, val, bar_id, val_id):
        color, cls = _bar_color(val)
        display = f"{val}%" if val > 0 else "—"
        return f'''      <div class="compare-bar">
        <span class="compare-label">{label}</span>
        <div class="compare-track"><div class="compare-fill {cls}" id="{bar_id}" style="width:{val}%"></div></div>
        <span class="compare-value" id="{val_id}" style="color:{color}">{display}</span>
      </div>'''

    return "\n".join([
        _bar("Accessibilita AI", accessibility, "geo-bar-access", "geo-val-access"),
        _bar("Struttura Info",   structure,     "geo-bar-struct", "geo-val-struct"),
        _bar("Citabilita",       citability,    "geo-bar-cite",   "geo-val-cite"),
        _bar("Fonti Autorevoli", authority,     "geo-bar-auth",   "geo-val-auth"),
    ])


def _build_competitor_js(scraping_data: dict) -> str:
    """Costruisce la stringa JS con i dati competitor per il grafico premium."""
    competitors = scraping_data.get("competitors", [])
    if not competitors:
        return "const compLabels=[]; const compReviews=[]; const compRatings=[];"
    labels = json.dumps([str(c.get("name", "N/D"))[:20] for c in competitors[:5]])
    reviews = json.dumps([int(c.get("reviews_count", 0) or 0) for c in competitors[:5]])
    ratings = json.dumps([float(c.get("rating", 0) or 0) for c in competitors[:5]])
    return f"const compLabels={labels}; const compReviews={reviews}; const compRatings={ratings};"


def generate_premium_html(
    ctx: dict,
    sections: list,
    consulenza_url: str = "https://buy.stripe.com/3cI3cx3WUaTheOieMgdMI00",
    lead_id: str = "",
) -> str:
    """
    Genera l'HTML completo del report premium.

    Args:
        ctx: contesto dal premium_context.build_context()
        sections: lista di dict con 'id' e 'text' da premium_ai.generate_all_sections()
        consulenza_url: URL Stripe per la consulenza

    Returns:
        HTML completo come stringa
    """
    # Carica template
    template_path = TEMPLATE_DIR / "premium_template.html"
    if not template_path.exists():
        raise FileNotFoundError(f"Template non trovato: {template_path}")
    template = template_path.read_text(encoding="utf-8")

    scores = ctx.get("scores", {})
    punteggio = scores.get("globale", 0)

    # Calcola score_deg per il ring (punteggio/100 * 360)
    score_deg = round(punteggio / 100 * 360)

    # Verdict
    verdict_class, verdict_text, verdict_description = _verdict(punteggio)

    # Dashboard cards
    dashboard_cards = _build_dashboard(scores)

    # Mappa sezioni per ID
    section_map = {}
    for s in sections:
        section_map[s["id"]] = s.get("text", "")

    # Converti markdown delle sezioni in HTML
    sez_01 = _markdown_to_html(section_map.get("01_apertura_dashboard", ""))
    sez_02 = _markdown_to_html(section_map.get("02_sito_web", ""))
    sez_03 = _markdown_to_html(section_map.get("03_pagespeed_seo", ""))
    sez_04 = _markdown_to_html(section_map.get("04_keyword", ""))

    # Sezione 05: split Google Business / Reputazione
    raw_05 = section_map.get("05_google_business_reputazione", "")
    sez_05_gmb, sez_05_rep = _split_section_05(raw_05)
    sez_05 = _markdown_to_html(sez_05_gmb)
    sez_05_rep_html = _markdown_to_html(sez_05_rep) if sez_05_rep else ""

    sez_06 = _markdown_to_html(section_map.get("06_competitor", ""))
    sez_07 = _markdown_to_html(section_map.get("07_social_bio", ""))

    # Sezione 08: split Branding / AI
    raw_08 = section_map.get("08_branding_ai", "")
    sez_08_brand, sez_08_ai = _split_section_08(raw_08)
    sez_08_brand_html = _markdown_to_html(sez_08_brand)
    sez_08_ai_html = _markdown_to_html(sez_08_ai) if sez_08_ai else ""

    sez_09 = _markdown_to_html(section_map.get("09_ads", ""))
    sez_10 = _markdown_to_html(section_map.get("10_piano_90_giorni", ""))
    sez_11 = _markdown_to_html(section_map.get("11_relazione_punteggio", ""))

    # Score individuali
    score_sito = scores.get("sito", 0)
    score_seo = scores.get("seo_score", 0)
    score_gmb = scores.get("google_business", 0)
    score_facebook = scores.get("facebook", 0)
    score_instagram = scores.get("instagram", 0)
    score_reputazione = scores.get("reputazione_ai", 0)

    # Score map per JS (animazione contatori)
    score_map = {
        "mainScore": punteggio,
        "dashScore": punteggio,
        "finalScore": punteggio,
    }

    # PageSpeed rings (stessa logica del FREE)
    ps = ctx.get("scraping_data", {}).get("pagespeed", {})
    ps_mobile = ps.get("mobile", {}).get("scores", {})
    ps_desktop = ps.get("desktop", {}).get("scores", {})
    ps_labels = [
        ("performance", "Performance"),
        ("accessibility", "Accessibilita"),
        ("best-practices", "Best Practices"),
        ("seo", "SEO"),
    ]
    def _norm_ps(v):
        if v is None: return 0
        v = float(v)
        return int(v * 100) if v <= 1 else int(v)

    ps_mobile_rings = "".join(
        _ps_ring_svg(_norm_ps(ps_mobile.get(k, 0)), lbl)
        for k, lbl in ps_labels
    )
    ps_desktop_rings = "".join(
        _ps_ring_svg(_norm_ps(ps_desktop.get(k, 0)), lbl)
        for k, lbl in ps_labels
    )

    # Costruisci il dict di sostituzione
    replacements = {
        "{nome_attivita}": ctx.get("nome_attivita", ""),
        "{settore}": ctx.get("settore", ""),
        "{citta}": ctx.get("citta", ""),
        "{punteggio_globale}": str(punteggio),
        "{score_deg}": str(score_deg),
        "{data_odierna}": ctx.get("data_odierna", ""),
        "{dashboard_cards}": dashboard_cards,
        "{verdict_class}": verdict_class,
        "{verdict_text}": verdict_text,
        "{verdict_description}": verdict_description,
        "{consulenza_url}": consulenza_url,
        "{pdf_download_url}": f"/api/reports/diagnosi/premium/{lead_id}/pdf" if lead_id else "#",
        # Sezioni
        "{sezione_01}": sez_01,
        "{sezione_02}": sez_02,
        "{sezione_03}": sez_03,
        "{sezione_04}": sez_04,
        "{sezione_05}": sez_05,
        "{sezione_05_reputazione}": sez_05_rep_html,
        "{sezione_06}": sez_06,
        "{sezione_07}": sez_07,
        "{sezione_08_branding}": sez_08_brand_html,
        "{sezione_08_ai}": sez_08_ai_html,
        "{sezione_09}": sez_09,
        "{sezione_10}": sez_10,
        "{sezione_11}": sez_11,
        # Score per mini-ring
        "{score_sito}": str(score_sito),
        "{color_sito}": _score_color(score_sito),
        "{dashoffset_sito}": str(_dashoffset(score_sito)),
        "{score_seo}": str(score_seo),
        "{color_seo}": _score_color(score_seo),
        "{dashoffset_seo}": str(_dashoffset(score_seo)),
        "{score_gmb}": str(score_gmb),
        "{color_gmb}": _score_color(score_gmb),
        "{dashoffset_gmb}": str(_dashoffset(score_gmb)),
        "{score_facebook}": str(score_facebook),
        "{color_facebook}": _score_color(score_facebook),
        "{dashoffset_facebook}": str(_dashoffset(score_facebook)),
        "{score_instagram}": str(score_instagram),
        "{color_instagram}": _score_color(score_instagram),
        "{dashoffset_instagram}": str(_dashoffset(score_instagram)),
        "{score_reputazione}": str(score_reputazione),
        "{color_reputazione}": _score_color(score_reputazione),
        "{dashoffset_reputazione}": str(_dashoffset(score_reputazione)),
        # GEO score
        "{score_geo}": str(scores.get("score_geo", scores.get("geo", 0))),
        "{color_geo}": _score_color(scores.get("score_geo", scores.get("geo", 0))),
        "{dashoffset_geo}": str(_dashoffset(scores.get("score_geo", scores.get("geo", 0)))),
        "{sezione_geo}": _markdown_to_html(section_map.get("geo_ai_visibility", "")),
        # Competitor data per grafico JS
        "{competitor_data_js}": _build_competitor_js(ctx.get("scraping_data", {})),
        "{geo_sub_bars}": _build_geo_sub_bars(ctx.get("scraping_data", {})),
        # PageSpeed rings
        "{ps_mobile_rings}": ps_mobile_rings,
        "{ps_desktop_rings}": ps_desktop_rings,
        # JS score map
        "{score_map_json}": json.dumps(score_map),
    }

    # Applica tutte le sostituzioni
    html = template
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, str(value))

    logger.info(f"HTML premium generato: {len(html)} caratteri")
    return html


def save_premium_html(html: str, lead_id: str, output_dir: str = "/app/reports/premium_html") -> str:
    """Salva l'HTML su disco e ritorna il path."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    filepath = out_path / f"premium_{lead_id}.html"
    filepath.write_text(html, encoding="utf-8")
    logger.info(f"HTML premium salvato: {filepath}")
    return str(filepath)


# ══════════════════════════════════════════════════════════
# FREE HTML REPORT GENERATOR
# ══════════════════════════════════════════════════════════

def _split_free_sections(report_text: str) -> dict:
    """
    Divide il testo del report free in 5 sezioni basandosi su heading/pattern.
    Il report free di Claude ha 5 sezioni con heading di livello 2.
    """
    sections = {
        'sezione_01': '',
        'sezione_02': '',
        'sezione_03': '',
        'sezione_04': '',
        'sezione_05': '',
    }

    if not report_text:
        return sections

    # Pattern per identificare le sezioni del report free
    import re
    # Cerca heading che indicano le sezioni
    section_patterns = [
        (r'(?i)(?:##?\s*)?(?:sezione\s*1|panoramica|fotografia\s*digitale|la\s*tua\s*fotografia)', 'sezione_01'),
        (r'(?i)(?:##?\s*)?(?:sezione\s*2|presenza\s*online|come\s*ti\s*vede)', 'sezione_02'),
        (r'(?i)(?:##?\s*)?(?:sezione\s*3|posizionamento|concorrenza|competitor|tu\s*vs)', 'sezione_03'),
        (r'(?i)(?:##?\s*)?(?:sezione\s*4|opportunit[aà]\s*immediate|azioni|cose\s*che\s*puoi)', 'sezione_04'),
        (r'(?i)(?:##?\s*)?(?:sezione\s*5|prossimi\s*passi|quadro\s*completo|vuoi\s*il\s*quadro)', 'sezione_05'),
    ]

    # Trova le posizioni di ogni sezione
    positions = []
    for pattern, key in section_patterns:
        match = re.search(pattern, report_text)
        if match:
            positions.append((match.start(), key))

    if not positions:
        # Se non trova pattern, dividi equamente
        chunk_size = len(report_text) // 5
        for i, key in enumerate(sections.keys()):
            start = i * chunk_size
            end = (i + 1) * chunk_size if i < 4 else len(report_text)
            sections[key] = report_text[start:end].strip()
        return sections

    # Ordina per posizione
    positions.sort(key=lambda x: x[0])

    # Estrai il testo tra una posizione e la successiva
    for i, (pos, key) in enumerate(positions):
        if i + 1 < len(positions):
            next_pos = positions[i + 1][0]
            sections[key] = report_text[pos:next_pos].strip()
        else:
            sections[key] = report_text[pos:].strip()

    # Se sezione_01 è vuota, metti tutto il testo prima della prima sezione trovata
    if not sections['sezione_01'] and positions:
        first_pos = positions[0][0]
        if first_pos > 0:
            sections['sezione_01'] = report_text[:first_pos].strip()

    return sections


def _build_free_dashboard(scores: dict) -> str:
    """Genera le card della dashboard per il report free usando gli score pre-calcolati."""
    cards = []
    
    # Mappa i nomi dei campi degli score verso le card della dashboard
    card_defs = [
        ("Sito Web", "🌐", scores.get("score_sito_web", scores.get("sito", 0))),
        ("SEO", "🔍", scores.get("score_seo", scores.get("seo_score", 0))),
        ("Google Business", "📍", scores.get("score_gmb", scores.get("google_business", 0))),
        ("Social Media", "📱", scores.get("score_social", scores.get("facebook", 0))),
        ("Competitività", "⚔", scores.get("score_competitivo", scores.get("competitivita", 0))),
        ("Visibilità AI", "🤖", scores.get("score_geo", scores.get("geo", 0))),
    ]
    
    for title, emoji, score in card_defs:
        cards.append(_build_dashboard_card(title, emoji, score))

    return "\n".join(cards)


def generate_free_html(
    scraping_data: dict,
    report_markdown: str,
    company_name: str,
    contact_name: str = "",
    sector: str = "",
    city: str = "",
    checkout_url: str = "",
    lead_id: str = "",
) -> str:
    """
    Genera l'HTML completo del report free.
    """
    from datetime import datetime

    # Carica template
    template_path = TEMPLATE_DIR / "free_template.html"
    if not template_path.exists():
        raise FileNotFoundError(f"Template free non trovato: {template_path}")
    template = template_path.read_text(encoding="utf-8")

    # Recupera score pre-calcolati (dal task)
    scores = scraping_data.get("scores", {})
    if not scores:
        # Fallback se mancano (non dovrebbe succedere)
        from execution.calculate_scores import compute_free_scores
        scores = compute_free_scores(scraping_data)

    punteggio = scores.get("punteggio_globale", 0)
    score_deg = round(punteggio / 100 * 360)

    # Verdict
    verdict_class, verdict_text, verdict_description = _verdict(punteggio)

    # Dashboard
    dashboard_cards = _build_free_dashboard(scores)

    # Data
    MESI = ["gennaio","febbraio","marzo","aprile","maggio","giugno",
            "luglio","agosto","settembre","ottobre","novembre","dicembre"]
    now = datetime.now()
    data_odierna = f"{now.day} {MESI[now.month-1]} {now.year}"

    # Rimuovi tabelle markdown pipe-syntax PRIMA della conversione HTML
    import re as _re_md
    # Pattern: header-row + separator-row + data-rows
    _md_table_pat = r'(?m)^\|.+\|[ \t]*\n\|[-| :\t]+\|[ \t]*\n(\|.+\|[ \t]*\n)*'
    report_markdown_clean = _re_md.sub(_md_table_pat, '', report_markdown)
    # Converti tutto il markdown in HTML (stesso contenuto del PDF)
    report_html = _markdown_to_html(report_markdown_clean)

    # Aggiungi id ai titoli h2 per la navigazione
    import re as _re
    def _slugify(text):
        text = _re.sub(r'<[^>]+>', '', text).strip().lower()
        text = _re.sub(r'[^a-z0-9\u00e0\u00e8\u00e9\u00ec\u00f2\u00f9]+', '-', text).strip('-')
        return text[:40]
    _nav_links = []
    def _add_id(m):
        title = m.group(1)
        slug = _slugify(title)
        _nav_links.append((slug, _re.sub(r'<[^>]+>', '', title).strip()))
        return f'<h2 id="{slug}">{title}</h2>'
    # Converti # heading rimasti come testo in <h2>
    report_html = _re.sub(r"<p>#{1,2}\s+(.+?)\s*</p>", r"<h2>\g<1></h2>", report_html)
    report_html = _re.sub(r'<h1>(.*?)</h1>', r'<h2>\1</h2>', report_html)
    report_html = _re.sub(r'<h2>(.*?)</h2>', _add_id, report_html)

    # Inietta tabella competitor stilizzata dai dati reali
    competitors = scraping_data.get("competitors", [])
    if competitors:
        comp_html = '<div style="margin:1.5rem 0;overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:0.9rem;">'
        comp_html += '<thead><tr>'
        comp_html += '<th style="background:var(--di-card);color:var(--accent);text-align:left;padding:0.8rem 1rem;border-bottom:2px solid var(--accent);font-weight:700;text-transform:uppercase;font-size:0.75rem;">Competitor</th>'
        comp_html += '<th style="background:var(--di-card);color:var(--accent);text-align:center;padding:0.8rem 1rem;border-bottom:2px solid var(--accent);font-weight:700;text-transform:uppercase;font-size:0.75rem;">Rating</th>'
        comp_html += '<th style="background:var(--di-card);color:var(--accent);text-align:center;padding:0.8rem 1rem;border-bottom:2px solid var(--accent);font-weight:700;text-transform:uppercase;font-size:0.75rem;">Recensioni</th>'
        comp_html += '<th style="background:var(--di-card);color:var(--accent);text-align:left;padding:0.8rem 1rem;border-bottom:2px solid var(--accent);font-weight:700;text-transform:uppercase;font-size:0.75rem;">Sito Web</th>'
        comp_html += '</tr></thead><tbody>'
        for c in competitors[:5]:
            name = c.get("name", "N/D")
            rating = c.get("rating", "N/D")
            if rating and rating != "N/D":
                rating_str = f"\u2B50 {rating}"
            else:
                rating_str = "N/D"
            reviews = c.get("reviews_count", "N/D") or "N/D"
            website = c.get("website", "")
            if website:
                site_label = "Sito Web" if "facebook.com" not in website else "Facebook"
                site_link = f'<a href="{website}" target="_blank" style="color:var(--accent);text-decoration:none;">{site_label}</a>'
            else:
                site_link = "N/D"
            comp_html += f'<tr><td style="padding:0.7rem 1rem;border-bottom:1px solid var(--di-border);color:var(--di-white);font-weight:600;">{name}</td>'
            comp_html += f'<td style="padding:0.7rem 1rem;border-bottom:1px solid var(--di-border);text-align:center;">{rating_str}</td>'
            comp_html += f'<td style="padding:0.7rem 1rem;border-bottom:1px solid var(--di-border);text-align:center;">{reviews}</td>'
            comp_html += f'<td style="padding:0.7rem 1rem;border-bottom:1px solid var(--di-border);">{site_link}</td></tr>'
        comp_html += '</tbody></table></div>'
        # Rimuovi TUTTE le tabelle esistenti nel report (sia <table> che <table style=...>)
        # prima di iniettare quella stilizzata
        report_html = _re.sub(r'<table[^>]*>.*?</table>', '', report_html, flags=_re.DOTALL)
        # Inserisci dopo il titolo competitor
        for slug, title in _nav_links:
            if 'competitor' in slug.lower():
                report_html = report_html.replace(f'<h2 id="{slug}">{title}</h2>', f'<h2 id="{slug}">{title}</h2>\n{comp_html}')
                break

    # Inietta punteggi PageSpeed dai dati reali
    ps = scraping_data.get("pagespeed", {})
    mobile = ps.get("mobile", {}).get("scores", {})
    desktop = ps.get("desktop", {}).get("scores", {})
    if mobile or desktop:
        ps_html = '<div style="background:var(--di-card);border-radius:12px;padding:1.5rem;margin:1.5rem 0;border:1px solid var(--di-border);">'
        ps_html += '<div style="font-size:1.1rem;font-weight:700;color:var(--accent);margin-bottom:1rem;text-align:center;">Punteggi PageSpeed Insights</div>'
        for device, scores in [("MOBILE", mobile), ("DESKTOP", desktop)]:
            if not scores:
                continue
            ps_html += f'<div style="margin-bottom:1rem;"><div style="font-size:0.75rem;font-weight:700;color:var(--di-gray-400);margin-bottom:0.5rem;text-align:center;text-transform:uppercase;letter-spacing:2px;">{device}</div>'
            ps_html += '<div style="display:flex;justify-content:center;flex-wrap:wrap;gap:1.5rem;">'
            for key, label in [("performance","Performance"),("accessibility","Accessibilita"),("best-practices","Best Practices"),("seo","SEO")]:
                val = scores.get(key, 0)
                if val is None:
                    val = 0
                color = "var(--green)" if val >= 70 else "var(--yellow)" if val >= 50 else "var(--red)"
                ps_html += f'<div style="text-align:center;"><div style="width:60px;height:60px;border-radius:50%;border:4px solid {color};display:flex;align-items:center;justify-content:center;margin:0 auto;"><span style="font-size:1.2rem;font-weight:800;color:{color};font-family:var(--font-mono);">{val}</span></div><div style="font-size:0.7rem;color:var(--di-gray-400);margin-top:0.3rem;">{label}</div></div>'
            ps_html += '</div></div>'
        ps_html += '</div>'
        # Inserisci dopo la sezione sito web
        for slug, title in _nav_links:
            if 'sito' in slug.lower():
                # Trova la fine della sezione sito (prima del prossimo h2)
                marker = f'<h2 id="{slug}">{title}</h2>'
                pos = report_html.find(marker)
                if pos >= 0:
                    # Trova il prossimo <h2 dopo questo
                    next_h2 = report_html.find('<h2 id=', pos + len(marker))
                    if next_h2 >= 0:
                        report_html = report_html[:next_h2] + ps_html + report_html[next_h2:]
                    else:
                        report_html += ps_html
                break

    # Genera nav dinamica
    if _nav_links:
        nav_html = '<a href="#dashboard" class="nav-link active">Dashboard</a>'
        for slug, title in _nav_links:
            short = title[:25] + ('...' if len(title) > 25 else '')
            nav_html += '\n    <a href="#' + slug + '" class="nav-link">' + short + '</a>'
    else:
        nav_html = '<a href="#dashboard" class="nav-link active">Dashboard</a>'
    nav_html += '\n    <a href="#upgrade" class="nav-link" style="color:#FFD700;border-color:rgba(255,215,0,0.4);">Premium</a>'
    # Pulsante download PDF rimosso — PDF inviato solo via email

    # Score map per JS
    score_map = {
        "mainScore": punteggio,
        "dashScore": punteggio,
        "finalScore": punteggio,
    }

    # PageSpeed rings
    ps = scraping_data.get("pagespeed", {})
    ps_mobile = ps.get("mobile", {}).get("scores", {})
    ps_desktop = ps.get("desktop", {}).get("scores", {})
    ps_labels = [
        ("performance", "Performance"),
        ("accessibility", "Accessibilità"),
        ("best-practices", "Best Practices"),
        ("seo", "SEO"),
    ]
    def _norm(v):
        if v is None: return 0
        v = float(v)
        return int(v * 100) if v <= 1 else int(v)

    ps_mobile_rings = "".join(
        _ps_ring_svg(_norm(ps_mobile.get(k, 0)), lbl)
        for k, lbl in ps_labels
    )
    ps_desktop_rings = "".join(
        _ps_ring_svg(_norm(ps_desktop.get(k, 0)), lbl)
        for k, lbl in ps_labels
    )

    # GEO gauge
    geo = scraping_data.get("geo", {})
    geo_score_val = int(geo.get("geo_score", {}).get("score", 0) or 0)
    geo_level, geo_desc = _geo_level_desc(geo_score_val)
    geo_gauge = _geo_gauge_svg(geo_score_val)
    quick_wins = geo.get("quick_wins", [])
    geo_wins_html = "".join(
        f'<div class="geo-win-item"><div class="geo-win-dot"></div><span>{w.get("action", w) if isinstance(w, dict) else w}</span></div>'
        for w in quick_wins[:3]
    ) if quick_wins else '<div class="geo-win-item"><div class="geo-win-dot"></div><span>Analisi GEO non disponibile per questa attività.</span></div>'

    # Sostituzioni
    replacements = {
        "{nome_attivita}": company_name,
        "{settore}": sector or "Attivita Locale",
        "{citta}": city or "",
        "{punteggio_globale}": str(punteggio),
        "{score_deg}": str(score_deg),
        "{data_odierna}": data_odierna,
        "{dashboard_cards}": dashboard_cards,
        "{verdict_class}": verdict_class,
        "{verdict_text}": verdict_text,
        "{verdict_description}": verdict_description,
        "{checkout_url}": checkout_url or "#",
        "{pdf_download_url}": f"/api/reports/diagnosi/free/{lead_id}/pdf" if lead_id else "#",
        "{sezione_01}": report_html,
        "{nav_links}": nav_html,
        "{sezione_02}": "",
        "{sezione_03}": "",
        "{sezione_04}": "",
        "{sezione_05}": "",
        "{score_map_json}": json.dumps(score_map),
        "{ps_mobile_rings}": ps_mobile_rings,
        "{ps_desktop_rings}": ps_desktop_rings,
        "{geo_gauge_svg}": geo_gauge,
        "{geo_level}": geo_level,
        "{geo_desc}": geo_desc,
        "{geo_wins_html}": geo_wins_html,
    }

    html = template
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, str(value))

    logger.info(f"HTML free generato: {len(html)} caratteri per {company_name}")
    return html


def save_free_html(html: str, lead_id: str, output_dir: str = "/app/reports/free_html") -> str:
    """Salva l'HTML free su disco e ritorna il path."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    filepath = out_path / f"free_{lead_id}.html"
    filepath.write_text(html, encoding="utf-8")
    logger.info(f"HTML free salvato: {filepath}")
    return str(filepath)


# ═══════════════════════════════════════════════════════════════
# GEO AUDIT — HTML INTERATTIVO (stile premium)
# ═══════════════════════════════════════════════════════════════

def generate_geo_html(risultati: dict, url_sito: str, audit_id: str, analisi: dict) -> str:
    """Genera il report GEO interattivo in stile premium dark."""
    from datetime import datetime
    from pathlib import Path

    TEMPLATE_DIR = Path(__file__).parent / "html_templates"
    template_path = TEMPLATE_DIR / "geo_template.html"
    if not template_path.exists():
        raise FileNotFoundError(f"Template GEO non trovato: {template_path}")
    template = template_path.read_text(encoding="utf-8")

    geo_score = risultati.get("geo_score", 0)
    moduli = risultati.get("moduli", {})

    # Brand name from URL
    from engine.brand_mentions import estrai_nome_brand
    brand_name = estrai_nome_brand(url_sito)
    
    # City (se disponibile nei risultati)
    city = risultati.get("city", risultati.get("citta", ""))

    # Score per modulo
    scores = {
        "citabilita": moduli.get("citabilita", {}).get("score", 0),
        "crawler": moduli.get("crawler", {}).get("score", 0),
        "brand": moduli.get("brand", {}).get("score", 0),
        "schema": moduli.get("schema", {}).get("score", 0),
        "contenuto": moduli.get("contenuto", {}).get("score", 0),
    }

    # Score color e verdict
    if geo_score >= 70:
        score_color = "#22C55E"
        score_emoji = "✅"
        verdict_text = "BUONO — Ben posizionato per le AI generative"
    elif geo_score >= 50:
        score_color = "#F59E0B"
        score_emoji = "⚠️"
        verdict_text = "DISCRETO — Margini di miglioramento significativi"
    elif geo_score >= 30:
        score_color = "#F97316"
        score_emoji = "🔶"
        verdict_text = "CRITICO — Poco visibile alle AI. Serve intervenire"
    else:
        score_color = "#EF4444"
        score_emoji = "🔴"
        verdict_text = "MOLTO CRITICO — Quasi invisibile alle AI generative"

    # Module cards HTML
    module_defs = [
        ("citabilita", "Citabilità AI", "25%"),
        ("crawler", "Accesso Crawler AI", "15%"),
        ("brand", "Autorità del Brand", "20%"),
        ("schema", "Dati Strutturati", "10%"),
        ("contenuto", "Qualità Contenuto E-E-A-T", "20%"),
    ]
    cards_html = ""
    for key, label, weight in module_defs:
        sc = scores.get(key, 0)
        color = "#22C55E" if sc >= 70 else "#F59E0B" if sc >= 50 else "#EF4444"
        cards_html += f"""<div class="module-card">
        <div class="mod-score" style="color:{color};">{sc}</div>
        <div class="mod-name">{label}</div>
        <div class="mod-weight">Peso: {weight}</div>
      </div>\n"""

    # Data analisi
    data_raw = risultati.get("data_analisi", datetime.now().isoformat())
    try:
        dt = datetime.fromisoformat(data_raw.replace("Z", "+00:00"))
        data_fmt = dt.strftime("%d/%m/%Y alle %H:%M")
    except Exception:
        data_fmt = data_raw[:10] if len(data_raw) >= 10 else data_raw

    # Markdown to HTML per analisi
    analisi_html = {}
    for key in ["executive_summary", "citabilita", "crawler", "brand", "schema", "contenuto", "piano_azione", "benchmark"]:
        raw = analisi.get(key, "")
        if isinstance(raw, str) and raw.strip():
            analisi_html[key] = _markdown_to_html(raw)
        else:
            analisi_html[key] = "<p>Analisi non disponibile.</p>"

    # Robots.txt ottimizzato
    from engine.report_generator import genera_robots_ottimizzato, genera_llmstxt
    crawler_bloccati = moduli.get("crawler", {}).get("crawler_bloccati", [])
    robots_ottimizzato = genera_robots_ottimizzato(crawler_bloccati)
    llmstxt = genera_llmstxt(url_sito, brand_name)

    # Crawler table
    crawler_data = moduli.get("crawler", {})
    bot_list = crawler_data.get("bot_details", crawler_data.get("dettagli_bot", []))
    if bot_list:
        crawler_table = '<table class="geo-table"><tr><th>Bot AI</th><th>Azienda</th><th>Accesso</th></tr>'
        for bot in bot_list:
            nome = bot.get("nome", bot.get("name", ""))
            azienda = bot.get("azienda", bot.get("company", ""))
            accesso = bot.get("accesso", bot.get("access", ""))
            icon = "✅ OK" if accesso in ["OK", "allowed", True, "✅"] else "❌ Bloccato"
            crawler_table += f"<tr><td>{nome}</td><td>{azienda}</td><td>{icon}</td></tr>"
        crawler_table += "</table>"
    else:
        crawler_table = "<p>Dati crawler non disponibili in formato tabellare. Vedi analisi AI sopra.</p>"

    # Priorità HTML
    priorita_list = risultati.get("priorita", [])
    if priorita_list:
        priorita_html = ""
        for i, p in enumerate(priorita_list[:3], 1):
            titolo = p.get("titolo", p.get("title", f"Problema {i}"))
            desc = p.get("descrizione", p.get("description", ""))
            modulo = p.get("modulo", p.get("module", ""))
            priorita_html += f"""<div class="timeline-item" style="border-color:#EF4444;">
              <p class="tl-title">{i}. {titolo}</p>
              <p class="tl-desc">{desc}</p>
              <p style="color:var(--di-gray-600);font-size:0.8rem;">Modulo: {modulo}</p>
            </div>"""
    else:
        priorita_html = "<p>Le priorità sono dettagliate nell'analisi AI sopra.</p>"

    # Schema templates (JSON-LD)
    schema_localbusiness = """{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": """" + brand_name + """",
  "url": """" + url_sito + """",
  "telephone": "[INSERISCI TELEFONO]",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "[INSERISCI VIA]",
    "addressLocality": """" + city + """",
    "addressRegion": "[REGIONE]",
    "postalCode": "[CAP]",
    "addressCountry": "IT"
  },
  "openingHoursSpecification": {
    "@type": "OpeningHoursSpecification",
    "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday"],
    "opens": "09:00",
    "closes": "18:00"
  }
}"""

    schema_faqpage = """{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "[DOMANDA 1]",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "[RISPOSTA 1]"
      }
    },
    {
      "@type": "Question",
      "name": "[DOMANDA 2]",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "[RISPOSTA 2]"
      }
    }
  ]
}"""

    schema_organization = """{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": """" + brand_name + """",
  "url": """" + url_sito + """",
  "logo": "[URL_LOGO]",
  "sameAs": [
    "[URL_FACEBOOK]",
    "[URL_INSTAGRAM]",
    "[URL_LINKEDIN]"
  ],
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "[TELEFONO]",
    "contactType": "customer service",
    "availableLanguage": "Italian"
  }
}"""

    # Checklist HTML
    def _chk(ok, text):
        if ok:
            return f'<div class="check-item"><span class="chk-y">✓</span> {text}</div>'
        return f'<div class="check-item"><span class="chk-n">✗</span> {text}</div>'

    crawler_details = moduli.get("crawler", {})
    has_llmstxt = crawler_details.get("has_llmstxt", False)
    
    checklist_crawler = ""
    checklist_crawler += _chk(True, "robots.txt permette GPTBot")
    checklist_crawler += _chk(True, "robots.txt permette ClaudeBot")
    checklist_crawler += _chk(True, "robots.txt permette Google-Extended")
    checklist_crawler += _chk(has_llmstxt, "llms.txt pubblicato nella root")
    checklist_crawler += _chk(has_llmstxt, "llms.txt aggiornato con dati corretti")

    schema_details = moduli.get("schema", {})
    has_local = schema_details.get("has_localbusiness", False)
    has_org = schema_details.get("has_organization", False)
    has_faq = schema_details.get("has_faqpage", False)

    checklist_schema = ""
    checklist_schema += _chk(has_local, "Schema LocalBusiness nel &lt;head&gt;")
    checklist_schema += _chk(has_org, "Schema Organization nel &lt;head&gt;")
    checklist_schema += _chk(has_faq, "Schema FAQPage sulla pagina FAQ")
    checklist_schema += _chk(False, "Validato su Rich Results Test")

    checklist_citabilita = ""
    checklist_citabilita += _chk(False, "Contenuto in blocchi 130-170 parole")
    checklist_citabilita += _chk(False, "FAQ con 10+ domande e risposte")
    checklist_citabilita += _chk(False, "Dati quantitativi (prezzi, durate)")
    checklist_citabilita += _chk(False, "Titoli H2/H3 come domande dirette")
    checklist_citabilita += _chk(False, "NAP (Nome/Indirizzo/Tel) nel footer")

    checklist_brand = ""
    checklist_brand += _chk(False, "Google My Business ottimizzato 100%")
    checklist_brand += _chk(False, "20+ recensioni Google ≥ 4.5 stelle")
    checklist_brand += _chk(False, "LinkedIn pagina aziendale")
    checklist_brand += _chk(False, "NAP coerente su tutte le directory")

    checklist_eeat = ""
    checklist_eeat += _chk(False, "Bio professionale completa")
    checklist_eeat += _chk(False, "Certificazioni e formazione elencate")
    checklist_eeat += _chk(False, "Blog attivo (min. 1 articolo/mese)")
    checklist_eeat += _chk(False, "Privacy Policy GDPR aggiornata")
    checklist_eeat += _chk(True, "HTTPS attivo e certificato valido")
    checklist_eeat += _chk(False, "Pagina contatti con indirizzo fisico")

    # Score proiezioni
    score_fase1 = min(geo_score + 15, 100)
    score_fase2 = min(score_fase1 + 13, 100)
    score_fase3 = min(score_fase2 + 15, 100)
    score_target = min(geo_score + 45, 100)

    # Letture moduli per sezione strategica
    def _lettura(score, mod_name):
        if score >= 70:
            return f"in buona forma. Mantieni e rafforza."
        elif score >= 50:
            return f"sufficiente ma con margini importanti di crescita."
        elif score >= 30:
            return f"critico — richiede intervento prioritario."
        else:
            return f"molto critico — il collo di bottiglia principale da risolvere."

    # Sostituzioni template
    replacements = {
        "{url_sito}": url_sito,
        "{brand_name}": brand_name,
        "{city}": city,
        "{data_analisi}": data_fmt,
        "{geo_score}": str(geo_score),
        "{score_deg}": str(int(geo_score * 3.6)),
        "{score_color}": score_color,
        "{score_emoji}": score_emoji,
        "{verdict_text}": verdict_text,
        "{module_cards}": cards_html,
        "{anno}": str(datetime.now().year),
        # Score moduli
        "{score_citabilita}": str(scores["citabilita"]),
        "{score_crawler}": str(scores["crawler"]),
        "{score_brand}": str(scores["brand"]),
        "{score_schema}": str(scores["schema"]),
        "{score_contenuto}": str(scores["contenuto"]),
        # Score deg per mini-ring
        "{score_citabilita_deg}": str(int(scores["citabilita"] * 3.6)),
        "{score_crawler_deg}": str(int(scores["crawler"] * 3.6)),
        "{score_brand_deg}": str(int(scores["brand"] * 3.6)),
        "{score_schema_deg}": str(int(scores["schema"] * 3.6)),
        "{score_contenuto_deg}": str(int(scores["contenuto"] * 3.6)),
        # Analisi Claude
        "{analisi_executive_summary}": analisi_html["executive_summary"],
        "{analisi_citabilita}": analisi_html["citabilita"],
        "{analisi_crawler}": analisi_html["crawler"],
        "{analisi_brand}": analisi_html["brand"],
        "{analisi_schema}": analisi_html["schema"],
        "{analisi_contenuto}": analisi_html["contenuto"],
        "{analisi_piano_azione}": analisi_html["piano_azione"],
        "{analisi_benchmark}": analisi_html["benchmark"],
        # Risorse
        "{robots_ottimizzato}": robots_ottimizzato,
        "{llmstxt}": llmstxt,
        "{schema_localbusiness}": schema_localbusiness,
        "{schema_faqpage}": schema_faqpage,
        "{schema_organization}": schema_organization,
        # Tabelle e liste
        "{crawler_table}": crawler_table,
        "{priorita_html}": priorita_html,
        # Checklist
        "{checklist_crawler}": checklist_crawler,
        "{checklist_schema}": checklist_schema,
        "{checklist_citabilita}": checklist_citabilita,
        "{checklist_brand}": checklist_brand,
        "{checklist_eeat}": checklist_eeat,
        # Piano 90gg
        "{score_fase1}": str(score_fase1),
        "{score_fase2}": str(score_fase2),
        "{score_fase3}": str(score_fase3),
        "{score_target}": str(score_target),
        "{delta_fase1}": str(score_fase1 - geo_score),
        "{delta_fase2}": str(score_fase2 - score_fase1),
        "{delta_fase3}": str(score_fase3 - score_fase2),
        "{delta_totale}": str(score_target - geo_score),
        # Letture strategiche
        "{lettura_crawler}": _lettura(scores["crawler"], "Crawler"),
        "{lettura_citabilita}": _lettura(scores["citabilita"], "Citabilità"),
        "{lettura_brand}": _lettura(scores["brand"], "Brand"),
        "{lettura_schema}": _lettura(scores["schema"], "Schema"),
        "{lettura_contenuto}": _lettura(scores["contenuto"], "Contenuto"),
    }

    html = template
    for key, val in replacements.items():
        html = html.replace(key, str(val))

    # Salva file
    out_dir = Path("/app/reports/geo")
    out_dir.mkdir(parents=True, exist_ok=True)
    filepath = out_dir / f"geo_{audit_id}.html"
    filepath.write_text(html, encoding="utf-8")

    logger.info(f"[GEO HTML] Report interattivo salvato: {filepath}")
    return str(filepath)
