"""
DigIdentity Engine — Canonical Scoring Logic for FREE Report.
Ensures consistency between Database, PDF and HTML Report.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def compute_free_scores(scraping_data: Dict[str, Any]) -> Dict[str, int]:
    """
    Calculates all scores (0-100) based on scraping data.
    This is the SINGLE SOURCE OF TRUTH for scores.
    """
    try:
        # 1. Google Business Score
        gb = scraping_data.get("google_business", {})
        gb_rating = gb.get("rating", 0) or 0
        
        # Gestione flessibile reviews count (può essere int o list di testi)
        gb_reviews_raw = gb.get("reviews_count", gb.get("total_reviews", 0))
        if isinstance(gb_reviews_raw, list):
            gb_reviews = len(gb_reviews_raw)
        else:
            gb_reviews = int(gb_reviews_raw or 0)
            
        score_gmb = min(100, int(gb_rating * 12 + min(gb_reviews, 200) * 0.2))

        # 2. Social Media Score
        apify_data = scraping_data.get("apify", {})
        ig = apify_data.get("instagram", {})
        fb = apify_data.get("facebook", {})
        
        ig_followers = int(ig.get("followers", 0) or 0)
        fb_followers = int(fb.get("followers", fb.get("likes", 0)) or 0)
        
        # Considerato "trovato" se Apify dice found=True o se abbiamo estratto follower/link
        ig_found = 1 if ig.get("found") or ig_followers > 0 or ig.get("url") else 0
        fb_found = 1 if fb.get("found") or fb_followers > 0 or fb.get("url") else 0
        
        score_social = min(100, int((ig_found + fb_found) * 25 + min(ig_followers + fb_followers, 5000) * 0.01))

        # 3. Sito Web Score
        ps = scraping_data.get("pagespeed", {})
        # Tenta di prendere performance mobile (prioritaria) o desktop
        perf_mobile = ps.get("mobile", {}).get("scores", {}).get("performance", 0)
        perf_desktop = ps.get("desktop", {}).get("scores", {}).get("performance", 0)
        perf = max(perf_mobile or 0, perf_desktop or 0)
        
        has_site = 1 if scraping_data.get("website", {}).get("reachable") or scraping_data.get("website_url") else 0
        score_sito = min(100, int(has_site * 40 + (perf or 0) * 0.6))

        # 4. SEO Score
        seo = scraping_data.get("seo", {})
        indexed = seo.get("indexed_pages", {}).get("total", 0) or 0
        citations_count = len(scraping_data.get("citations", []))
        score_seo = min(100, int(min(int(indexed), 100) * 0.3 + min(citations_count, 20) * 3))

        # 5. Competitività Score
        comp = scraping_data.get("competitors", [])
        n_comp = len(comp) if isinstance(comp, list) else 0
        score_comp = max(20, 100 - n_comp * 10)

        # 6. GEO Score (AI Visibility)
        geo = scraping_data.get("geo", {})
        geo_score_raw = geo.get("geo_score", {}).get("score", 0) or 0
        score_geo = int(geo_score_raw)

        # 7. Score Totale (Pesato)
        score_totale = int(
            score_gmb * 0.25 +
            score_social * 0.20 +
            score_sito * 0.20 +
            score_seo * 0.15 +
            score_comp * 0.10 +
            score_geo * 0.10
        )

        return {
            "punteggio_globale": score_totale,
            "score_gmb": score_gmb,
            "score_social": score_social,
            "score_sito_web": score_sito,
            "score_seo": score_seo,
            "score_competitivo": score_comp,
            "score_geo": score_geo,
            # Compatibilità con html_generator card_defs
            "sito": score_sito,
            "seo_score": score_seo,
            "google_business": score_gmb,
            "facebook": score_social if fb_found else 0,
            "instagram": score_social if ig_found else 0,
            "reputazione_ai": score_gmb,
            "geo": score_geo
        }
    except Exception as e:
        logger.error(f"Errore calcolo score: {e}")
        return {
            "punteggio_globale": 0, "score_gmb": 0, "score_social": 0,
            "score_sito_web": 0, "score_seo": 0, "score_competitivo": 0
        }
