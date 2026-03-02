"""
DigIdentity Engine — SERP Engine (sostituto SerpAPI)
Sistema a cascata: Serper.dev → Google CSE API → Scraping diretto
- Serper.dev:       2.500 crediti gratis (no CC), poi $0.001/query
- Google CSE API:   100 query/giorno gratis, poi $5/1.000
- Scraping diretto: 0 costo, usato solo per citazioni e site:
"""

import logging
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, quote_plus

logger = logging.getLogger(__name__)

HEADERS_GOOGLE = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "it-IT,it;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


# ══════════════════════════════════════════════
# LAYER 1 — Serper.dev  (drop-in di SerpAPI)
# 2.500 crediti gratis su https://serper.dev
# ══════════════════════════════════════════════

def _serper_search(query: str, serper_key: str, gl: str = "it", hl: str = "it", num: int = 10) -> dict:
    """Esegue una ricerca Google via Serper.dev."""
    try:
        resp = requests.post(
            "https://google.serper.dev/search",
            headers={
                "X-API-KEY": serper_key,
                "Content-Type": "application/json",
            },
            json={
                "q": query,
                "gl": gl,
                "hl": hl,
                "num": num,
            },
            timeout=15,
        )
        data = resp.json()
        return _normalize_serper_response(data)
    except Exception as e:
        logger.warning(f"[SERPER] Errore query '{query}': {e}")
        return {}


def _normalize_serper_response(data: dict) -> dict:
    """
    Converte la risposta Serper.dev nel formato SerpAPI-like
    che il tuo _analyze_seo() si aspetta.
    """
    normalized = {
        "organic_results": [],
        "local_results": {"places": []},
        "knowledge_graph": {},
        "search_information": {
            "total_results": data.get("searchInformation", {}).get("totalResults", 0)
        },
    }

    # Organic results
    for r in data.get("organic", []):
        normalized["organic_results"].append({
            "title": r.get("title"),
            "link": r.get("link"),
            "snippet": r.get("snippet"),
            "position": r.get("position"),
        })

    # Local results (Places / Maps)
    for p in data.get("places", []):
        normalized["local_results"]["places"].append({
            "title": p.get("title"),
            "address": p.get("address"),
            "rating": p.get("rating"),
            "reviews": p.get("ratingCount"),
            "phone": p.get("phoneNumber"),
            "links": {"website": p.get("website")},
            "place_id": p.get("placeId"),
        })

    # Knowledge Graph
    kg = data.get("knowledgeGraph", {})
    if kg:
        normalized["knowledge_graph"] = {
            "title": kg.get("title"),
            "type": kg.get("type"),
            "address": kg.get("address"),
            "phone": kg.get("phone"),
            "website": kg.get("website"),
            "rating": kg.get("rating"),
            "reviews": kg.get("reviewsCount"),
            "hours": kg.get("attributes", {}).get("Orari"),
            "thumbnail": kg.get("imageUrl"),
        }

    return normalized


# ══════════════════════════════════════════════
# LAYER 2 — Google Custom Search JSON API
# 100 query/giorno gratis (3.000/mese)
# Crea chiave: console.cloud.google.com
# Crea CX: programmablesearchengine.google.com
# ══════════════════════════════════════════════

def _google_cse_search(query: str, api_key: str, cx: str, num: int = 10) -> dict:
    """Esegue una ricerca via Google Custom Search JSON API."""
    try:
        resp = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": api_key,
                "cx": cx,
                "q": query,
                "hl": "it",
                "gl": "it",
                "num": min(num, 10),
            },
            timeout=15,
        )
        data = resp.json()

        organic = []
        for item in data.get("items", []):
            organic.append({
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet"),
                "position": len(organic) + 1,
            })

        return {
            "organic_results": organic,
            "local_results": {"places": []},
            "knowledge_graph": {},
            "search_information": {
                "total_results": int(
                    data.get("searchInformation", {})
                    .get("totalResults", 0)
                )
            },
        }
    except Exception as e:
        logger.warning(f"[GOOGLE_CSE] Errore query '{query}': {e}")
        return {}


# ══════════════════════════════════════════════
# LAYER 3 — Scraping diretto Google (gratuito)
# Solo per Q5 (site:) e Q6 (citazioni)
# ══════════════════════════════════════════════

def _google_scrape(query: str, num: int = 10) -> dict:
    """Scraping diretto HTML di Google."""
    try:
        url = f"https://www.google.it/search?q={quote_plus(query)}&hl=it&gl=it&num={num}"
        time.sleep(2)  # Rate limiting obbligatorio
        resp = requests.get(url, headers=HEADERS_GOOGLE, timeout=15)

        if resp.status_code != 200:
            logger.warning(f"[SCRAPE] Google ha risposto {resp.status_code} per '{query}'")
            return {}

        soup = BeautifulSoup(resp.text, "html.parser")
        organic = []

        for div in soup.select("div.g, div[data-sokoban-container]"):
            a_tag = div.find("a", href=True)
            title_tag = div.find("h3")
            snippet_tag = div.find("div", {"data-sncf": True}) or div.find("span", class_=re.compile("aCOpRe|st"))

            if a_tag and title_tag:
                href = a_tag.get("href", "")
                if href.startswith("/url?"):
                    href = re.sub(r"/url\?q=([^&]+).*", r"\1", href)
                if href.startswith("http"):
                    organic.append({
                        "title": title_tag.get_text(strip=True),
                        "link": href,
                        "snippet": snippet_tag.get_text(strip=True) if snippet_tag else "",
                        "position": len(organic) + 1,
                    })

        total = 0
        stats = soup.find("div", id="result-stats")
        if stats:
            m = re.search(r"([\d.,]+)", stats.get_text())
            if m:
                total = int(m.group(1).replace(".", "").replace(",", ""))

        return {
            "organic_results": organic[:num],
            "local_results": {"places": []},
            "knowledge_graph": {},
            "search_information": {"total_results": total},
        }
    except Exception as e:
        logger.warning(f"[SCRAPE] Errore Google scraping '{query}': {e}")
        return {}


# ══════════════════════════════════════════════
# ROUTER INTELLIGENTE
# Sceglie automaticamente il layer disponibile
# ══════════════════════════════════════════════

def smart_search(
    query: str,
    serper_key: str = None,
    google_cse_key: str = None,
    google_cx: str = None,
    need_local_pack: bool = False,
    need_knowledge_graph: bool = False,
) -> dict:
    """
    Router intelligente: sceglie il layer migliore in base
    a disponibilità delle chiavi e tipo di dati necessari.

    - Se serve KG o Local Pack → SOLO Serper.dev
    - Se serve solo organic   → Serper > Google CSE > Scraping diretto
    """
    # Se serve KG o Local Pack, solo Serper può farlo
    if need_local_pack or need_knowledge_graph:
        if serper_key:
            result = _serper_search(query, serper_key)
            if result:
                logger.info(f"[ROUTER] Serper.dev → '{query}'")
                return result
        logger.warning(f"[ROUTER] KG/LocalPack richiesto ma Serper non disponibile: '{query}'")
        return {}

    # Per organic puro: cascata Serper → CSE → Scraping
    if serper_key:
        result = _serper_search(query, serper_key)
        if result:
            logger.info(f"[ROUTER] Serper.dev → '{query}'")
            return result

    if google_cse_key and google_cx:
        result = _google_cse_search(query, google_cse_key, google_cx)
        if result:
            logger.info(f"[ROUTER] Google CSE → '{query}'")
            return result

    # Ultimo fallback: scraping diretto
    logger.info(f"[ROUTER] Scraping diretto → '{query}'")
    return _google_scrape(query)
