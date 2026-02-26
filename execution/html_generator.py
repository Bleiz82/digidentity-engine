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
            html_lines.append(f'<h3>{stripped[3:]}</h3>')  # Render as h3 inside sections
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
    sez_05_rep_html = _markdown_to_html(sez_05_rep) if sez_05_rep else _markdown_to_html(raw_05)

    sez_06 = _markdown_to_html(section_map.get("06_competitor", ""))
    sez_07 = _markdown_to_html(section_map.get("07_social_bio", ""))

    # Sezione 08: split Branding / AI
    raw_08 = section_map.get("08_branding_ai", "")
    sez_08_brand, sez_08_ai = _split_section_08(raw_08)
    sez_08_brand_html = _markdown_to_html(sez_08_brand)
    sez_08_ai_html = _markdown_to_html(sez_08_ai) if sez_08_ai else _markdown_to_html(raw_08)

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
        "{score_reputazione}": str(score_reputazione),
        "{color_reputazione}": _score_color(score_reputazione),
        "{dashoffset_reputazione}": str(_dashoffset(score_reputazione)),
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

    # Converti tutto il markdown in HTML (stesso contenuto del PDF)
    report_html = _markdown_to_html(report_markdown)

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
        # Sostituisci la tabella markdown dei competitor con quella stilizzata
        report_html = _re.sub(r'<table>.*?</table>', '', report_html, count=1, flags=_re.DOTALL)
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
    # Pulsante download PDF
    pdf_url = f"/api/reports/diagnosi/free/{lead_id}/pdf" if lead_id else "#"
    nav_html += f'\n    <a href="{pdf_url}" class="nav-link" style="color:#fff;background:#F90100;border-color:#F90100;padding:6px 14px;border-radius:6px;" download>⬇ Scarica PDF</a>'

    # Score map per JS
    score_map = {
        "mainScore": punteggio,
        "dashScore": punteggio,
        "finalScore": punteggio,
    }

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
    }

    html = template
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, str(value))

    logger.info(f"HTML free generato: {len(html)} caratteri per {company_name}")
    return html


    # Data
    MESI = ["gennaio","febbraio","marzo","aprile","maggio","giugno",
            "luglio","agosto","settembre","ottobre","novembre","dicembre"]
    now = datetime.now()
    data_odierna = f"{now.day} {MESI[now.month-1]} {now.year}"

    # Split report in sezioni
    free_sections = _split_free_sections(report_markdown)

    # Converti in HTML
    sez_01 = _markdown_to_html(free_sections.get('sezione_01', ''))
    sez_02 = _markdown_to_html(free_sections.get('sezione_02', ''))
    sez_03 = _markdown_to_html(free_sections.get('sezione_03', ''))
    sez_04 = _markdown_to_html(free_sections.get('sezione_04', ''))
    sez_05 = _markdown_to_html(free_sections.get('sezione_05', ''))

    # Score map per JS
    score_map = {
        "mainScore": punteggio,
        "dashScore": punteggio,
        "finalScore": punteggio,
    }

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
        "{sezione_01}": sez_01,
        "{sezione_02}": sez_02,
        "{sezione_03}": sez_03,
        "{sezione_04}": sez_04,
        "{sezione_05}": sez_05,
        "{score_map_json}": json.dumps(score_map),
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
