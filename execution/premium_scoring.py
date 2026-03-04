"""
DigIdentity Premium — Scoring Module (v2)
Wrapper su compute_free_scores: punteggi IDENTICI alla free.
Aggiunge chiavi extra per compatibilita con premium_context.
"""
import logging
from execution.calculate_scores import compute_free_scores

logger = logging.getLogger(__name__)


def calculate_scores(scraping_data: dict) -> dict:
    """
    Calcola punteggi con la STESSA logica della free report.
    Aggiunge chiavi extra per premium_context (pagespeed dettaglio).
    """
    # Punteggi identici alla free
    scores = compute_free_scores(scraping_data)

    # Chiavi extra da PageSpeed (premium_context le mostra nel dettaglio)
    ps = scraping_data.get("pagespeed", {})
    mob = ps.get("mobile", {}).get("scores", {})
    desk = ps.get("desktop", {}).get("scores", {})

    def _norm(v):
        if v is None:
            return 0
        v = float(v)
        return int(v * 100) if v <= 1 else int(v)

    scores["velocita_mobile"] = _norm(mob.get("performance", 0))
    scores["velocita_desktop"] = _norm(desk.get("performance", 0))
    scores["seo_score"] = _norm(mob.get("seo", 0))
    scores["accessibilita"] = _norm(mob.get("accessibility", 0))
    scores["best_practices"] = _norm(mob.get("best-practices", 0))

    # Alias: premium_context usa "globale"
    scores["globale"] = scores.get("punteggio_globale", 0)

    logger.info(f"[PREMIUM SCORING v2] Punteggio globale: {scores['globale']}/100 (identico a free)")
    return scores


def determine_top_actions(scraping_data: dict, scores: dict) -> list:
    """Restituisce le 5 azioni prioritarie basate sui dati e punteggi."""
    actions = []

    # 1. Recensioni Google
    gb = scraping_data.get("google_business", {})
    gb_reviews_raw = gb.get("reviews_count", gb.get("total_reviews", 0))
    if isinstance(gb_reviews_raw, list):
        reviews = len(gb_reviews_raw)
    else:
        reviews = int(gb_reviews_raw or 0)

    if reviews < 15:
        actions.append({
            "azione": "Raccolta recensioni Google",
            "descrizione": f"Hai solo {reviews} recensioni. Invia un messaggio WhatsApp a 20-30 clienti soddisfatti con un link diretto. Obiettivo: 30 recensioni entro 60 giorni.",
            "costo": "Gratuito",
            "impatto": "Alto",
            "priorita": 1
        })

    # 2. Correzioni urgenti sito
    site = scraping_data.get("website", {})
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
    seo = scraping_data.get("seo", {})
    indexed = seo.get("indexed_pages", {})
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
    ig = scraping_data.get("apify", {}).get("instagram", {})
    fb = scraping_data.get("apify", {}).get("facebook", {})
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

    # Riempimento se meno di 5
    if len(actions) < 5:
        if not any(a["azione"].startswith("Google Business") for a in actions):
            actions.append({
                "azione": "Potenziamento Google Business Profile",
                "descrizione": "Aggiungere foto (target 30-50), elencare tutti i servizi, pubblicare un post settimanale, aggiornare orari e categorie.",
                "costo": "Gratuito",
                "impatto": "Medio-Alto",
                "priorita": len(actions) + 1
            })

    if len(actions) < 5:
        geo_score = scores.get("score_geo", scores.get("geo", 0))
        if geo_score < 50:
            actions.append({
                "azione": "Ottimizzazione visibilita AI (GEO)",
                "descrizione": f"GEO Score: {geo_score}/100. Aggiungere dati strutturati, creare contenuti citabili, ottimizzare per motori AI come ChatGPT e Perplexity.",
                "costo": "200-500 EUR",
                "impatto": "Medio-Alto",
                "priorita": len(actions) + 1
            })

    return sorted(actions, key=lambda x: x["priorita"])[:5]
