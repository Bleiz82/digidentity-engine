"""
DigIdentity Engine — Modulo di scraping per analisi presenza digitale PMI.

Esegue scraping multi-sorgente:
1. Sito web aziendale (HTML, meta tag, performance)
2. Google Search (posizionamento, SERP)
3. Social media (pagine pubbliche)
4. Google Business Profile (via SerpAPI)
"""

import logging
import re
import time
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

# Timeout per le richieste HTTP
REQUEST_TIMEOUT = 15
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}


def scrape_lead(website_url: str, company_name: str) -> dict[str, Any]:
    """
    Esegue lo scraping completo di un'azienda.
    Restituisce un dizionario strutturato con tutti i dati raccolti.
    """
    logger.info(f"Inizio scraping per {company_name} — {website_url}")
    results = {
        "company_name": company_name,
        "website_url": website_url,
        "scrape_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "website": {},
        "seo": {},
        "social_media": {},
        "google_business": {},
        "competitors": [],
        "errors": [],
    }

    # 1. Scraping sito web
    try:
        results["website"] = _scrape_website(website_url)
    except Exception as e:
        logger.warning(f"Errore scraping sito {website_url}: {e}")
        results["errors"].append(f"Sito web: {str(e)}")

    # 2. Analisi SEO via SerpAPI
    try:
        results["seo"] = _analyze_seo(website_url, company_name)
    except Exception as e:
        logger.warning(f"Errore analisi SEO per {company_name}: {e}")
        results["errors"].append(f"SEO: {str(e)}")

    # 3. Ricerca social media
    try:
        results["social_media"] = _find_social_media(website_url, company_name)
    except Exception as e:
        logger.warning(f"Errore ricerca social per {company_name}: {e}")
        results["errors"].append(f"Social: {str(e)}")

    # 4. Google Business Profile
    try:
        results["google_business"] = _check_google_business(company_name)
    except Exception as e:
        logger.warning(f"Errore Google Business per {company_name}: {e}")
        results["errors"].append(f"Google Business: {str(e)}")

    logger.info(
        f"Scraping completato per {company_name}: "
        f"{len(results['errors'])} errori"
    )
    return results


def _scrape_website(url: str) -> dict:
    """Scraping del sito web: meta tag, struttura, contenuti, performance."""
    data = {
        "url": url,
        "reachable": False,
        "load_time_ms": None,
        "status_code": None,
        "title": None,
        "meta_description": None,
        "h1_tags": [],
        "h2_tags": [],
        "has_ssl": url.startswith("https"),
        "has_responsive_meta": False,
        "has_favicon": False,
        "has_analytics": False,
        "has_cookie_banner": False,
        "images_count": 0,
        "images_without_alt": 0,
        "internal_links_count": 0,
        "external_links_count": 0,
        "word_count": 0,
        "technologies_detected": [],
        "pages_found": [],
        "contact_info": {},
        "structured_data": False,
    }

    start = time.time()
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        data["load_time_ms"] = round((time.time() - start) * 1000)
        data["status_code"] = resp.status_code
        data["reachable"] = resp.status_code == 200
    except requests.RequestException as e:
        data["error"] = str(e)
        return data

    if not data["reachable"]:
        return data

    soup = BeautifulSoup(resp.text, "html.parser")
    domain = urlparse(url).netloc

    # Meta tags
    data["title"] = soup.title.string.strip() if soup.title and soup.title.string else None

    meta_desc = soup.find("meta", attrs={"name": "description"})
    data["meta_description"] = meta_desc["content"].strip() if meta_desc and meta_desc.get("content") else None

    # Viewport (responsive)
    viewport = soup.find("meta", attrs={"name": "viewport"})
    data["has_responsive_meta"] = viewport is not None

    # Favicon
    favicon = soup.find("link", rel=lambda x: x and "icon" in x)
    data["has_favicon"] = favicon is not None

    # Headings
    data["h1_tags"] = [h.get_text(strip=True) for h in soup.find_all("h1")][:10]
    data["h2_tags"] = [h.get_text(strip=True) for h in soup.find_all("h2")][:20]

    # Immagini
    images = soup.find_all("img")
    data["images_count"] = len(images)
    data["images_without_alt"] = sum(1 for img in images if not img.get("alt"))

    # Link
    links = soup.find_all("a", href=True)
    for link in links:
        href = link["href"]
        if href.startswith(("http://", "https://")):
            if domain in href:
                data["internal_links_count"] += 1
            else:
                data["external_links_count"] += 1
        elif href.startswith("/"):
            data["internal_links_count"] += 1

    # Conteggio parole
    text = soup.get_text(separator=" ", strip=True)
    data["word_count"] = len(text.split())

    # Tecnologie
    html_lower = resp.text.lower()
    tech_signatures = {
        "WordPress": ["wp-content", "wp-includes", "wordpress"],
        "Shopify": ["cdn.shopify.com", "shopify"],
        "Wix": ["wix.com", "wixstatic"],
        "Squarespace": ["squarespace.com", "sqsp"],
        "Joomla": ["joomla", "/media/system/js/"],
        "React": ["react", "__next"],
        "Vue.js": ["vue.js", "__vue"],
        "jQuery": ["jquery"],
        "Bootstrap": ["bootstrap"],
        "Tailwind": ["tailwind"],
        "Google Analytics": ["google-analytics.com", "gtag", "ga.js", "googletagmanager"],
        "Google Tag Manager": ["googletagmanager.com"],
        "Facebook Pixel": ["facebook.net/en_US/fbevents", "fbq("],
        "Hotjar": ["hotjar.com"],
        "Cookiebot": ["cookiebot", "cookieconsent"],
        "GDPR Cookie": ["cookie-consent", "cookie-banner", "cookie-notice"],
    }
    for tech, signatures in tech_signatures.items():
        if any(sig in html_lower for sig in signatures):
            data["technologies_detected"].append(tech)

    data["has_analytics"] = any(
        t in data["technologies_detected"]
        for t in ["Google Analytics", "Google Tag Manager"]
    )
    data["has_cookie_banner"] = any(
        t in data["technologies_detected"]
        for t in ["Cookiebot", "GDPR Cookie"]
    )

    # Structured data (JSON-LD)
    json_ld = soup.find_all("script", type="application/ld+json")
    data["structured_data"] = len(json_ld) > 0

    # Contatti
    email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    phone_pattern = re.compile(r"(?:\+39\s?)?(?:0\d{1,3}[\s.-]?\d{5,9}|\d{3}[\s.-]?\d{6,7})")
    found_emails = email_pattern.findall(text)
    found_phones = phone_pattern.findall(text)
    data["contact_info"] = {
        "emails": list(set(found_emails))[:5],
        "phones": list(set(found_phones))[:5],
    }

    # Pagine principali (dal menu)
    nav_links = []
    for nav in soup.find_all(["nav", "header"]):
        for a in nav.find_all("a", href=True):
            href = a["href"]
            label = a.get_text(strip=True)
            if label and len(label) < 50:
                nav_links.append({"label": label, "href": href})
    data["pages_found"] = nav_links[:20]

    return data


def _analyze_seo(website_url: str, company_name: str) -> dict:
    """Analisi SEO via SerpAPI: posizionamento su Google."""
    data = {
        "search_queries": [],
        "organic_results": [],
        "total_results_for_brand": 0,
        "knowledge_graph": None,
        "local_results": [],
    }

    if not settings.SERPAPI_KEY:
        data["error"] = "SerpAPI key non configurata"
        return data

    # Query di ricerca
    domain = urlparse(website_url).netloc.replace("www.", "")
    queries = [
        company_name,
        f"{company_name} recensioni",
        f"site:{domain}",
    ]

    for query in queries:
        try:
            resp = requests.get(
                "https://serpapi.com/search.json",
                params={
                    "q": query,
                    "hl": "it",
                    "gl": "it",
                    "api_key": settings.SERPAPI_KEY,
                    "num": 10,
                },
                timeout=REQUEST_TIMEOUT,
            )
            result = resp.json()

            query_data = {
                "query": query,
                "total_results": result.get("search_information", {}).get("total_results", 0),
                "organic_results": [],
            }

            for item in result.get("organic_results", [])[:5]:
                query_data["organic_results"].append({
                    "position": item.get("position"),
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "snippet": item.get("snippet"),
                    "domain": urlparse(item.get("link", "")).netloc,
                })

            # Knowledge Graph
            if "knowledge_graph" in result and not data["knowledge_graph"]:
                data["knowledge_graph"] = {
                    "title": result["knowledge_graph"].get("title"),
                    "type": result["knowledge_graph"].get("type"),
                    "description": result["knowledge_graph"].get("description"),
                }

            # Local results
            for local in result.get("local_results", {}).get("places", [])[:3]:
                data["local_results"].append({
                    "title": local.get("title"),
                    "rating": local.get("rating"),
                    "reviews": local.get("reviews"),
                    "address": local.get("address"),
                })

            data["search_queries"].append(query_data)
            time.sleep(1)  # Rate limiting

        except Exception as e:
            logger.warning(f"Errore SerpAPI per query '{query}': {e}")

    return data


def _find_social_media(website_url: str, company_name: str) -> dict:
    """Cerca i profili social dell'azienda."""
    data = {
        "facebook": None,
        "instagram": None,
        "linkedin": None,
        "twitter": None,
        "youtube": None,
        "tiktok": None,
    }

    # Prima cerca nel sito web
    try:
        resp = requests.get(website_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        html = resp.text.lower()

        social_patterns = {
            "facebook": r"(?:facebook\.com|fb\.com)/[\w.-]+",
            "instagram": r"instagram\.com/[\w.-]+",
            "linkedin": r"linkedin\.com/(?:company|in)/[\w.-]+",
            "twitter": r"(?:twitter\.com|x\.com)/[\w.-]+",
            "youtube": r"youtube\.com/(?:@|channel/|c/)[\w.-]+",
            "tiktok": r"tiktok\.com/@[\w.-]+",
        }

        for platform, pattern in social_patterns.items():
            match = re.search(pattern, html)
            if match:
                url = match.group(0)
                if not url.startswith("http"):
                    url = f"https://{url}"
                data[platform] = {"url": url, "found_on_website": True}

    except Exception as e:
        logger.warning(f"Errore ricerca social nel sito: {e}")

    return data


def _check_google_business(company_name: str) -> dict:
    """Verifica la presenza su Google Business."""
    data = {
        "found": False,
        "rating": None,
        "reviews_count": None,
        "address": None,
        "phone": None,
        "hours": None,
        "category": None,
    }

    if not settings.SERPAPI_KEY:
        data["error"] = "SerpAPI key non configurata"
        return data

    try:
        resp = requests.get(
            "https://serpapi.com/search.json",
            params={
                "q": company_name,
                "hl": "it",
                "gl": "it",
                "api_key": settings.SERPAPI_KEY,
            },
            timeout=REQUEST_TIMEOUT,
        )
        result = resp.json()

        # Cerca nei local results
        local = result.get("local_results", {})
        places = local.get("places", [])

        if places:
            place = places[0]
            data.update({
                "found": True,
                "rating": place.get("rating"),
                "reviews_count": place.get("reviews"),
                "address": place.get("address"),
                "phone": place.get("phone"),
                "category": place.get("type"),
            })

        # Knowledge graph
        kg = result.get("knowledge_graph", {})
        if kg and not data["found"]:
            data.update({
                "found": True,
                "rating": kg.get("rating"),
                "reviews_count": kg.get("reviews"),
                "address": kg.get("address"),
            })

    except Exception as e:
        logger.warning(f"Errore Google Business per {company_name}: {e}")
        data["error"] = str(e)

    return data
