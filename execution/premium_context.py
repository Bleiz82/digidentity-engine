"""
DigIdentity Premium — Context Builder
Estrae e organizza i dati per ogni sezione del report Premium.
"""
import json
from datetime import datetime
MESI_IT = ["gennaio","febbraio","marzo","aprile","maggio","giugno",
           "luglio","agosto","settembre","ottobre","novembre","dicembre"]

def _format_date_it():
    now = datetime.now()
    return f"{now.day} {MESI_IT[now.month-1]} {now.year}"




def build_context(lead: dict, scores: dict, top_actions: list) -> dict:
    """Costruisce il contesto completo per il report premium."""
    data = lead.get("scraping_data", {})
    return {
        "lead_id": lead.get("id", ""),
        "nome_titolare": lead.get("nome_titolare", lead.get("name", "Titolare")),
        "nome_attivita": lead.get("nome_attivita", lead.get("business_name", "Attivita")),
        "settore": lead.get("settore", lead.get("sector", "non specificato")),
        "citta": lead.get("citta", lead.get("city", "")),
        "email": lead.get("email", ""),
        "telefono": lead.get("telefono", lead.get("phone", "")),
        "website_url": lead.get("website", lead.get("url", "")),
        "data_odierna": _format_date_it(),
        "scores": scores,
        "punteggio_globale": scores.get("globale", 0),
        "top_actions": top_actions,
        "scraping_data": data,
    }


def get_apertura_dashboard_data(ctx: dict) -> str:
    """Dati per sezione 01: lettera apertura + dashboard."""
    scores = ctx["scores"]
    return f"""
DATI LEAD:
- Titolare: {ctx['nome_titolare']}
- Attivita: {ctx['nome_attivita']}
- Settore: {ctx['settore']}
- Citta: {ctx['citta']}
- Sito web: {ctx['website_url']}
- Data: {ctx['data_odierna']}

PUNTEGGI:
- Sito Web: {scores.get('sito', 0)}/100
- Velocita Mobile: {scores.get('velocita_mobile', 0)}/100
- Velocita Desktop: {scores.get('velocita_desktop', 0)}/100
- SEO: {scores.get('seo_score', 0)}/100
- Accessibilita: {scores.get('accessibilita', 0)}/100
- Best Practices: {scores.get('best_practices', 0)}/100
- Google Business: {scores.get('google_business', 0)}/100
- Facebook: {scores.get('facebook', 0)}/100
- Instagram: {scores.get('instagram', 0)}/100
- Reputazione AI: {scores.get('reputazione_ai', 0)}/100
- PUNTEGGIO GLOBALE: {scores.get('globale', 0)}/100
"""


def get_sito_web_data(ctx: dict) -> str:
    """Dati per sezione 02: analisi sito web."""
    site = ctx["scraping_data"].get("website", {})
    seo = ctx["scraping_data"].get("seo", {})
    indexed = seo.get("indexed_pages", {})
    pages_list = indexed.get("pages", []) if isinstance(indexed, dict) else []
    return f"""
DATI SITO WEB:
- URL: {ctx['website_url']}
- SSL: {site.get('ssl', 'N/A')}
- Raggiungibile: {site.get('reachable', 'N/A')}
- Tempo caricamento: {site.get('load_time_ms', 'N/A')} ms
- Parole totali: {site.get('word_count', 'N/A')}
- Immagini totali: {site.get('images_total', 'N/A')}
- Immagini senza alt: {site.get('images_without_alt', 'N/A')}
- Tecnologie: {site.get('technologies', 'N/A')}
- Meta description: {site.get('meta_description', 'ASSENTE')}
- Tag H1: {site.get('h1_tags', 'ASSENTE')}
- Tag H2: {json.dumps(site.get('h2_tags', []), ensure_ascii=False)}
- Favicon: {site.get('favicon', 'N/A')}
- Google Analytics: {site.get('has_analytics', False)}
- Dati strutturati: {site.get('has_structured_data', False)}
- Cookie banner: {site.get('has_cookie_banner', False)}
- Responsive: {site.get('is_responsive', 'N/A')}

PAGINE INDICIZZATE ({indexed.get('total', 0)} totali):
{json.dumps(pages_list, indent=2, ensure_ascii=False) if pages_list else 'Nessun dato disponibile'}
"""


def get_pagespeed_seo_data(ctx: dict) -> str:
    """Dati per sezione 03: PageSpeed + SEO."""
    ps = ctx["scraping_data"].get("pagespeed", {})
    mob = ps.get("mobile", {})
    desk = ps.get("desktop", {})
    seo = ctx["scraping_data"].get("seo", {})
    positions = seo.get("positions", [])
    return f"""
PAGESPEED MOBILE:
- Performance: {mob.get('performance', 'N/A')}
- SEO: {mob.get('seo', 'N/A')}
- Accessibilita: {mob.get('accessibility', 'N/A')}
- Best Practices: {mob.get('best_practices', 'N/A')}

PAGESPEED DESKTOP:
- Performance: {desk.get('performance', 'N/A')}
- SEO: {desk.get('seo', 'N/A')}
- Accessibilita: {desk.get('accessibility', 'N/A')}
- Best Practices: {desk.get('best_practices', 'N/A')}

POSIZIONAMENTO SEO:
{json.dumps(positions, indent=2, ensure_ascii=False) if positions else 'Nessun dato disponibile'}

PUNTEGGI CALCOLATI:
- Velocita Mobile: {ctx['scores'].get('velocita_mobile', 0)}/100
- Velocita Desktop: {ctx['scores'].get('velocita_desktop', 0)}/100
- SEO Score: {ctx['scores'].get('seo_score', 0)}/100
"""


def get_keyword_data(ctx: dict) -> str:
    """Dati per sezione 04: keyword research."""
    seo = ctx["scraping_data"].get("seo", {})
    keywords = seo.get("keyword_suggestions", [])
    positions = seo.get("positions", [])
    return f"""
ATTIVITA: {ctx['nome_attivita']}
SETTORE: {ctx['settore']}
CITTA: {ctx['citta']}

KEYWORD SUGGERITE:
{json.dumps(keywords, indent=2, ensure_ascii=False) if keywords else 'Nessun dato disponibile'}

POSIZIONAMENTO ATTUALE:
{json.dumps(positions, indent=2, ensure_ascii=False) if positions else 'Nessun dato disponibile'}
"""


def get_google_business_reputazione_data(ctx: dict) -> str:
    """Dati per sezione 05: Google Business + Reputazione."""
    gb = ctx["scraping_data"].get("google_business", {})
    perp = ctx["scraping_data"].get("perplexity", {})
    fb = ctx["scraping_data"].get("apify", {}).get("facebook", {})
    site = ctx["scraping_data"].get("website", {})
    ig = ctx["scraping_data"].get("apify", {}).get("instagram", {})
    return f"""
GOOGLE BUSINESS PROFILE:
- Nome: {gb.get('name', 'N/A')}
- Indirizzo: {gb.get('address', 'N/A')}
- Telefono: {gb.get('phone', 'N/A')}
- Orari: {gb.get('hours', 'N/A')}
- Categoria: {gb.get('category', 'N/A')}
- Rating: {gb.get('rating', 'N/A')}
- Recensioni: {gb.get('reviews_count', 'N/A')}
- Foto: {gb.get('photos_count', 'N/A')}
- Sito web: {gb.get('website', 'N/A')}
- Stato: {gb.get('status', 'N/A')}
- Servizi elencati: {gb.get('services', 'N/A')}
- Post pubblicati: {gb.get('posts_count', 'N/A')}
- Link Maps: {gb.get('maps_url', 'N/A')}

COERENZA DATI CONTATTO:
- Google Business: tel {gb.get('phone', 'N/A')}, sito {gb.get('website', 'N/A')}
- Sito web: {ctx['website_url']}
- Facebook: {fb.get('page_name', 'N/A')}, email {fb.get('email', 'N/A')}
- Instagram: @{ig.get('username', 'N/A')}

ANALISI AI (PERPLEXITY):
{json.dumps(perp, indent=2, ensure_ascii=False) if perp else 'Nessun dato disponibile'}

RATING FACEBOOK: {fb.get('rating', 'Nessuno')}
"""


def get_competitor_data(ctx: dict) -> str:
    """Dati per sezione 06: analisi competitor."""
    competitors = ctx["scraping_data"].get("competitors", [])
    seo = ctx["scraping_data"].get("seo", {})
    positions = seo.get("positions", [])
    perp = ctx["scraping_data"].get("perplexity", {})
    perp_analysis = perp.get("analysis", "") if perp.get("found") else ""
    perp_citations = perp.get("citations", [])
    return f"""
ATTIVITA ANALIZZATA: {ctx['nome_attivita']}
CITTA: {ctx['citta']}
SETTORE: {ctx['settore']}

COMPETITOR DA GOOGLE MAPS NEARBY SEARCH (dati reali — nome, indirizzo, rating, recensioni):
{json.dumps(competitors, indent=2, ensure_ascii=False) if competitors else 'Nessun dato disponibile'}

ANALISI COMPETITOR E MERCATO DA PERPLEXITY AI:
{perp_analysis if perp_analysis else 'Nessun dato disponibile'}

FONTI PERPLEXITY:
{chr(10).join(perp_citations) if perp_citations else 'Nessuna'}

POSIZIONAMENTO ATTUALE DELL ATTIVITA:
{json.dumps(positions, indent=2, ensure_ascii=False) if positions else 'Nessun dato disponibile'}

DATI GOOGLE BUSINESS ATTIVITA:
- Rating: {ctx['scraping_data'].get('google_business', {}).get('rating', 'N/A')}
- Recensioni: {ctx['scraping_data'].get('google_business', {}).get('reviews_count', 'N/A')}
"""


def get_social_bio_data(ctx: dict) -> str:
    """Dati per sezione 07: social media + bio proposte."""
    fb = ctx["scraping_data"].get("apify", {}).get("facebook", {})
    ig = ctx["scraping_data"].get("apify", {}).get("instagram", {})
    gb = ctx["scraping_data"].get("google_business", {})

    # Anti-allucinazione: se i dati sono vuoti, istruzioni esplicite
    fb_warning = ""
    ig_warning = ""
    if not fb or (not fb.get('page_name') and not fb.get('likes') and not fb.get('followers')):
        fb_warning = "\n⚠️ ISTRUZIONE CRITICA: NON CI SONO DATI FACEBOOK. Non inventare nomi, numeri, follower o post. Scrivi SOLO che non è stata rilevata una pagina Facebook attiva per questa attività e spiega perché è importante averne una.\n"
    if not ig or (not ig.get('username') and not ig.get('followers') and not ig.get('posts_count')):
        ig_warning = "\n⚠️ ISTRUZIONE CRITICA: NON CI SONO DATI INSTAGRAM. Non inventare username, follower, post o engagement. Scrivi SOLO che non è stato rilevato un profilo Instagram attivo per questa attività e spiega perché è importante averne uno.\n"

    return f"""
ATTIVITA: {ctx['nome_attivita']}
TITOLARE: {ctx['nome_titolare']}
SETTORE: {ctx['settore']}
CITTA: {ctx['citta']}
TELEFONO: {ctx['telefono']}
SITO: {ctx['website_url']}

{fb_warning}FACEBOOK:
- Nome pagina: {fb.get('page_name', 'N/A')}
- Likes: {fb.get('likes', 'N/A')}
- Followers: {fb.get('followers', 'N/A')}
- Rating: {fb.get('rating', 'N/A')}
- Email: {fb.get('email', 'N/A')}
- Post recenti: {fb.get('recent_posts_count', 'N/A')}
- Ultimo post (giorni fa): {fb.get('last_post_days', 'N/A')}
- Engagement rate: {fb.get('engagement_rate', 'N/A')}%
- Bio attuale: {fb.get('about', fb.get('description', 'N/A'))}

{ig_warning}INSTAGRAM:
- Username: @{ig.get('username', 'N/A')}
- Followers: {ig.get('followers', 'N/A')}
- Following: {ig.get('following', 'N/A')}
- Post totali: {ig.get('posts_count', 'N/A')}
- Engagement rate: {ig.get('engagement_rate', 'N/A')}%
- Media like: {ig.get('avg_likes', 'N/A')}
- Account business: {ig.get('is_business', 'N/A')}
- Bio attuale: {ig.get('biography', 'N/A')}
- Ultimo post (giorni fa): {ig.get('last_post_days', 'N/A')}

GOOGLE BUSINESS:
- Nome: {gb.get('name', 'N/A')}
- Descrizione: {gb.get('description', 'N/A')}
- Categoria: {gb.get('category', 'N/A')}
"""


def get_branding_ai_data(ctx: dict) -> str:
    """Dati per sezione 08: branding + analisi AI."""
    gb = ctx["scraping_data"].get("google_business", {})
    fb = ctx["scraping_data"].get("apify", {}).get("facebook", {})
    ig = ctx["scraping_data"].get("apify", {}).get("instagram", {})
    site = ctx["scraping_data"].get("website", {})
    perp = ctx["scraping_data"].get("perplexity", {})
    return f"""
NOME SUI VARI CANALI:
- Sito web: {ctx['website_url']}
- Google Business: {gb.get('name', 'N/A')}
- Facebook: {fb.get('page_name', 'N/A')}
- Instagram: @{ig.get('username', 'N/A')}

ATTIVITA: {ctx['nome_attivita']}
SETTORE: {ctx['settore']}
CITTA: {ctx['citta']}

ANALISI AI (PERPLEXITY):
{json.dumps(perp, indent=2, ensure_ascii=False) if perp else 'Nessun dato disponibile'}

DATI SITO:
- Parole totali: {site.get('word_count', 'N/A')}
- H1: {site.get('h1_tags', 'N/A')}
- H2: {json.dumps(site.get('h2_tags', []), ensure_ascii=False)}
- Meta description: {site.get('meta_description', 'N/A')}
"""


def get_ads_data(ctx: dict) -> str:
    """Dati per sezione 09: piano ads."""
    seo = ctx["scraping_data"].get("seo", {})
    keywords = seo.get("keyword_suggestions", [])
    positions = seo.get("positions", [])
    fb = ctx["scraping_data"].get("apify", {}).get("facebook", {})
    ig = ctx["scraping_data"].get("apify", {}).get("instagram", {})
    return f"""
ATTIVITA: {ctx['nome_attivita']}
SETTORE: {ctx['settore']}
CITTA: {ctx['citta']}
SITO: {ctx['website_url']}

KEYWORD PRINCIPALI:
{json.dumps(keywords[:8], indent=2, ensure_ascii=False) if keywords else 'Nessun dato disponibile'}

POSIZIONAMENTO ATTUALE:
{json.dumps(positions, indent=2, ensure_ascii=False) if positions else 'Nessun dato disponibile'}

PRESENZA SOCIAL:
- Facebook likes: {fb.get('likes', 'N/A')}
- Instagram followers: {ig.get('followers', 'N/A')}
- Facebook engagement: {fb.get('engagement_rate', 'N/A')}%
- Instagram engagement: {ig.get('engagement_rate', 'N/A')}%

PUNTEGGI ATTUALI:
- Sito: {ctx['scores'].get('sito', 0)}/100
- Google Business: {ctx['scores'].get('google_business', 0)}/100
- Globale: {ctx['scores'].get('globale', 0)}/100
"""


def get_piano_90_giorni_data(ctx: dict) -> str:
    """Dati per sezione 10: piano operativo 90 giorni."""
    data = ctx["scraping_data"]
    site = data.get("website", {})
    gb = data.get("google_business", {})
    fb = data.get("apify", {}).get("facebook", {})
    ig = data.get("apify", {}).get("instagram", {})
    seo = data.get("seo", {})
    keywords = seo.get("keyword_suggestions", [])
    indexed = seo.get("indexed_pages", {})
    actions_str = ""
    for a in ctx["top_actions"]:
        actions_str += f"- [{a['priorita']}] {a['azione']}: {a['descrizione']}\n"
    return f"""
ATTIVITA: {ctx['nome_attivita']}
TITOLARE: {ctx['nome_titolare']}
SETTORE: {ctx['settore']}
CITTA: {ctx['citta']}
SITO: {ctx['website_url']}

PROBLEMI SITO:
- Meta description: {site.get('meta_description', 'ASSENTE')}
- H1: {site.get('h1_tags', 'ASSENTE')}
- Analytics: {site.get('has_analytics', False)}
- Cookie banner: {site.get('has_cookie_banner', False)}
- Immagini senza alt: {site.get('images_without_alt', 0)}
- Parole totali: {site.get('word_count', 0)}
- Tempo caricamento: {site.get('load_time_ms', 'N/A')} ms

GOOGLE BUSINESS:
- Recensioni: {gb.get('reviews_count', 0)}
- Foto: {gb.get('photos_count', 0)}
- Servizi: {gb.get('services', 'Non elencati')}
- Post: {gb.get('posts_count', 0)}

SOCIAL:
- Facebook ultimo post: {fb.get('last_post_days', 'N/A')} giorni fa
- Instagram post totali: {ig.get('posts_count', 0)}
- Instagram business: {ig.get('is_business', 'N/A')}

SEO:
- Pagine indicizzate: {indexed.get('total', 0) if isinstance(indexed, dict) else 0}
- Keyword suggerite: {json.dumps(keywords[:6], ensure_ascii=False)}

AZIONI PRIORITARIE GIA CALCOLATE:
{actions_str}

PUNTEGGIO GLOBALE ATTUALE: {ctx['scores'].get('globale', 0)}/100
"""


def get_relazione_punteggio_data(ctx: dict) -> str:
    """Dati per sezione 11: relazione finale + punteggio."""
    scores = ctx["scores"]
    actions_str = ""
    for a in ctx["top_actions"]:
        actions_str += f"- [{a['priorita']}] {a['azione']}: {a['descrizione']} (Impatto: {a['impatto']}, Costo: {a['costo']})\n"
    return f"""
ATTIVITA: {ctx['nome_attivita']}
TITOLARE: {ctx['nome_titolare']}
SETTORE: {ctx['settore']}
CITTA: {ctx['citta']}

PUNTEGGIO GLOBALE: {scores.get('globale', 0)}/100

TUTTI I PUNTEGGI:
- Sito Web: {scores.get('sito', 0)}/100
- Velocita Mobile: {scores.get('velocita_mobile', 0)}/100
- Velocita Desktop: {scores.get('velocita_desktop', 0)}/100
- SEO: {scores.get('seo_score', 0)}/100
- Accessibilita: {scores.get('accessibilita', 0)}/100
- Best Practices: {scores.get('best_practices', 0)}/100
- Google Business: {scores.get('google_business', 0)}/100
- Facebook: {scores.get('facebook', 0)}/100
- Instagram: {scores.get('instagram', 0)}/100
- Reputazione AI: {scores.get('reputazione_ai', 0)}/100

TOP 5 AZIONI PRIORITARIE:
{actions_str}

TARGET 90 GIORNI: {_calc_target(scores.get('globale', 0))}
"""


def _calc_target(globale: int) -> str:
    if globale < 40:
        return "60-65/100"
    elif globale < 60:
        return "70-75/100"
    elif globale < 75:
        return "80-85/100"
    else:
        return "85-90/100"


# Mapping sezione -> funzione dati
SECTION_DATA_MAP = {
    "01_apertura_dashboard": get_apertura_dashboard_data,
    "02_sito_web": get_sito_web_data,
    "03_pagespeed_seo": get_pagespeed_seo_data,
    "04_keyword": get_keyword_data,
    "05_google_business_reputazione": get_google_business_reputazione_data,
    "06_competitor": get_competitor_data,
    "07_social_bio": get_social_bio_data,
    "08_branding_ai": get_branding_ai_data,
    "09_ads": get_ads_data,
    "10_piano_90_giorni": get_piano_90_giorni_data,
    "11_relazione_punteggio": get_relazione_punteggio_data,
}
