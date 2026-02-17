"""
DigIdentity Premium — Scoring Module
Calcola i punteggi per ogni area della diagnosi digitale.
"""

def calculate_scores(data: dict) -> dict:
    """Calcola punteggi 0-100 per ogni area e il punteggio globale."""

    scores = {}

    # ── SITO WEB ──
    site = data.get("website", {})
    site_score = 50  # base
    wc = site.get("word_count", 0) or 0
    if wc >= 2000:
        site_score += 15
    elif wc >= 1000:
        site_score += 8
    elif wc < 500:
        site_score -= 15

    lt = site.get("load_time_ms", 9999) or 9999
    if lt < 500:
        site_score += 10
    elif lt < 1000:
        site_score += 5
    elif lt > 2000:
        site_score -= 10

    imgs = site.get("images_total", 0) or 0
    imgs_no_alt = site.get("images_without_alt", 0) or 0
    if imgs > 0 and imgs_no_alt == 0:
        site_score += 5
    elif imgs > 0 and (imgs_no_alt / imgs) > 0.5:
        site_score -= 10

    if site.get("ssl"):
        site_score += 5
    else:
        site_score -= 15

    if site.get("favicon"):
        site_score += 2
    if site.get("meta_description"):
        site_score += 5
    else:
        site_score -= 5
    if site.get("h1_tags"):
        site_score += 3
    else:
        site_score -= 5
    if site.get("has_analytics"):
        site_score += 5
    else:
        site_score -= 5

    scores["sito"] = max(0, min(100, site_score))

    # ── PAGESPEED ──
    ps = data.get("pagespeed", {})
    mob = ps.get("mobile", {})
    desk = ps.get("desktop", {})
    scores["velocita_mobile"] = int((mob.get("performance", 0) or 0) * 100)
    scores["velocita_desktop"] = int((desk.get("performance", 0) or 0) * 100)
    scores["seo_score"] = int((mob.get("seo", 0) or 0) * 100)
    scores["accessibilita"] = int((mob.get("accessibility", 0) or 0) * 100)
    scores["best_practices"] = int((mob.get("best_practices", 0) or 0) * 100)

    # ── GOOGLE BUSINESS ──
    gb = data.get("google_business", {})
    gb_score = 0
    if gb and gb.get("name"):
        gb_score += 20
    rating = gb.get("rating", 0) or 0
    reviews = gb.get("reviews_count", 0) or 0
    photos = gb.get("photos_count", 0) or 0
    if rating >= 4.5:
        gb_score += 20
    elif rating >= 4.0:
        gb_score += 15
    elif rating >= 3.5:
        gb_score += 10
    if reviews >= 50:
        gb_score += 20
    elif reviews >= 20:
        gb_score += 15
    elif reviews >= 10:
        gb_score += 10
    elif reviews >= 5:
        gb_score += 5
    if photos >= 30:
        gb_score += 15
    elif photos >= 15:
        gb_score += 10
    elif photos >= 5:
        gb_score += 5
    if gb.get("hours"):
        gb_score += 5
    if gb.get("phone"):
        gb_score += 5
    if gb.get("website") and "https" in str(gb.get("website", "")):
        gb_score += 5
    if gb.get("services"):
        gb_score += 5
    if gb.get("posts_count", 0) or 0 > 0:
        gb_score += 5
    scores["google_business"] = max(0, min(100, gb_score))

    # ── FACEBOOK ──
    fb = data.get("apify", {}).get("facebook", {})
    fb_score = 0
    if fb and (fb.get("page_name") or fb.get("likes")):
        fb_score += 20
    likes = fb.get("likes", 0) or 0
    if likes >= 1000:
        fb_score += 20
    elif likes >= 500:
        fb_score += 15
    elif likes >= 200:
        fb_score += 10
    elif likes >= 50:
        fb_score += 5
    fb_rating_raw = fb.get("rating", 0) or 0
    try:
        fb_rating = float(fb_rating_raw)
    except (ValueError, TypeError):
        fb_rating = 5.0 if "100%" in str(fb_rating_raw) else 0.0
    if fb_rating >= 4.5:
        fb_score += 15
    elif fb_rating >= 4.0:
        fb_score += 10
    fb_posts = fb.get("recent_posts_count", 0) or 0
    if fb_posts >= 10:
        fb_score += 15
    elif fb_posts >= 5:
        fb_score += 10
    elif fb_posts >= 1:
        fb_score += 5
    fb_engagement = fb.get("engagement_rate", 0) or 0
    if fb_engagement >= 3:
        fb_score += 10
    elif fb_engagement >= 1:
        fb_score += 5
    if fb.get("last_post_days", 999) < 30:
        fb_score += 10
    scores["facebook"] = max(0, min(100, fb_score))

    # ── INSTAGRAM ──
    ig = data.get("apify", {}).get("instagram", {})
    ig_score = 0
    if ig and (ig.get("username") or ig.get("followers")):
        ig_score += 15
    followers = ig.get("followers", 0) or 0
    if followers >= 2000:
        ig_score += 20
    elif followers >= 1000:
        ig_score += 15
    elif followers >= 500:
        ig_score += 10
    elif followers >= 100:
        ig_score += 5
    ig_engagement = ig.get("engagement_rate", 0) or 0
    if ig_engagement >= 5:
        ig_score += 15
    elif ig_engagement >= 3:
        ig_score += 10
    elif ig_engagement >= 1:
        ig_score += 5
    ig_posts = ig.get("posts_count", 0) or 0
    if ig_posts >= 50:
        ig_score += 15
    elif ig_posts >= 20:
        ig_score += 10
    elif ig_posts >= 5:
        ig_score += 5
    if ig.get("is_business"):
        ig_score += 10
    if ig.get("last_post_days", 999) < 30:
        ig_score += 10
    scores["instagram"] = max(0, min(100, ig_score))

    # ── REPUTAZIONE AI ──
    perp = data.get("perplexity", {})
    ai_score = 30  # base
    perp_text = str(perp).lower()
    positive_terms = ["consigliato", "positiv", "ottim", "eccellent", "buon", "apprezzat", "professionale"]
    negative_terms = ["non visibile", "assente", "scarsa", "nessuna recensione", "poco conosciut", "non consolidat", "debole"]
    for term in positive_terms:
        if term in perp_text:
            ai_score += 8
    for term in negative_terms:
        if term in perp_text:
            ai_score -= 8
    scores["reputazione_ai"] = max(0, min(100, ai_score))

    # ── PUNTEGGIO GLOBALE ──
    weights = {
        "sito": 0.15,
        "velocita_mobile": 0.12,
        "velocita_desktop": 0.08,
        "seo_score": 0.10,
        "accessibilita": 0.035,
        "best_practices": 0.035,
        "google_business": 0.18,
        "facebook": 0.10,
        "instagram": 0.10,
        "reputazione_ai": 0.10,
    }
    globale = sum(scores.get(k, 0) * w for k, w in weights.items())
    scores["globale"] = round(globale)

    return scores


def determine_top_actions(data: dict, scores: dict) -> list:
    """Restituisce le 5 azioni prioritarie basate sui dati e punteggi."""
    actions = []

    # 1. Recensioni Google
    gb = data.get("google_business", {})
    reviews = gb.get("reviews_count", 0) or 0
    if reviews < 15:
        actions.append({
            "azione": "Raccolta recensioni Google",
            "descrizione": f"Hai solo {reviews} recensioni. Invia un messaggio WhatsApp a 20-30 clienti soddisfatti con un link diretto. Obiettivo: 30 recensioni entro 60 giorni.",
            "costo": "Gratuito",
            "impatto": "Alto",
            "priorita": 1
        })

    # 2. Correzioni urgenti sito/brand
    site = data.get("website", {})
    problems = []
    if not site.get("meta_description"):
        problems.append("meta description assente")
    if not site.get("h1_tags"):
        problems.append("nessun H1")
    if not site.get("has_analytics"):
        problems.append("Google Analytics mancante")
    if site.get("images_without_alt", 0) > 0:
        problems.append(f"{site['images_without_alt']} immagini senza alt-text")
    if problems:
        actions.append({
            "azione": "Correzioni tecniche urgenti del sito",
            "descrizione": f"Problemi trovati: {', '.join(problems)}. Risolvibili in 2-3 ore con impatto immediato su SEO e accessibilita.",
            "costo": "Gratuito (fai-da-te) o 150-300 EUR",
            "impatto": "Alto",
            "priorita": 2
        })

    # 3. Performance mobile
    if scores.get("velocita_mobile", 0) < 60:
        actions.append({
            "azione": "Ottimizzazione performance mobile",
            "descrizione": f"Punteggio mobile: {scores.get('velocita_mobile', 0)}/100. Convertire immagini in WebP, attivare lazy-loading e caching. Il 70% del traffico locale e da smartphone.",
            "costo": "Gratuito (plugin) o 200-400 EUR",
            "impatto": "Alto",
            "priorita": 3
        })

    # 4. Pagine servizio
    indexed = data.get("seo", {}).get("indexed_pages", {})
    total_pages = indexed.get("total", 0) if isinstance(indexed, dict) else 0
    if total_pages < 15:
        actions.append({
            "azione": "Creazione pagine servizio dedicate",
            "descrizione": f"Solo {total_pages} pagine indicizzate. Ogni nuovo servizio = nuova porta di ingresso da Google. Creare 4-6 pagine da 400-600 parole ciascuna.",
            "costo": "Gratuito (fai-da-te) o 500-1000 EUR",
            "impatto": "Medio-Alto",
            "priorita": 4
        })

    # 5. Calendario social
    ig = data.get("apify", {}).get("instagram", {})
    fb = data.get("apify", {}).get("facebook", {})
    ig_posts = ig.get("posts_count", 0) or 0
    fb_days = fb.get("last_post_days", 999) or 999
    if ig_posts < 20 or fb_days > 60:
        actions.append({
            "azione": "Avvio calendario editoriale social",
            "descrizione": "Pubblicare 3 post/settimana con format strutturato: lunedi foto lavoro, mercoledi consiglio, venerdi dietro le quinte. Costanza batte perfezione.",
            "costo": "2-3 ore/settimana",
            "impatto": "Medio",
            "priorita": 5
        })

    # Se meno di 5 azioni, aggiungi generiche
    if len(actions) < 5:
        if not any(a["azione"].startswith("Google Business") for a in actions):
            actions.append({
                "azione": "Potenziamento Google Business Profile",
                "descrizione": "Aggiungere foto (target 30-50), elencare tutti i servizi, pubblicare un post settimanale, aggiornare orari e categorie.",
                "costo": "Gratuito",
                "impatto": "Medio-Alto",
                "priorita": len(actions) + 1
            })

    return sorted(actions, key=lambda x: x["priorita"])[:5]
