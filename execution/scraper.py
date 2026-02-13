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


def scrape_lead(website_url: str, company_name: str, social_links_db: dict = None, city: str = "", sector: str = "") -> dict[str, Any]:
    """
    Esegue lo scraping completo di un'azienda.
    Restituisce un dizionario strutturato con tutti i dati raccolti.
    
    Args:
        website_url: URL del sito aziendale
        company_name: Nome dell'azienda
        social_links_db: Dict di social links dal database {platform: url}
        city: Città dell'azienda (se nota)
        sector: Settore dell'azienda (se noto)
    """
    logger.info(f"Inizio scraping per {company_name} — {website_url} ({city or 'città non fornita'})")
    results = {
        "company_name": company_name,
        "website_url": website_url,
        "city": city,
        "sector": sector,
        "scrape_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "website": {},
        "seo": {},
        "social_media": {},
        "google_business": {},
        "competitors": [],
        "citations": [],
        "indexed_pages": {"total": 0, "pages": []},
        "pagespeed": {},
        "apify": {},
        "perplexity": {},
        "errors": [],
    }

    # 1. Scraping sito web
    try:
        results["website"] = _scrape_website(website_url)
    except Exception as e:
        logger.warning(f"Errore scraping sito {website_url}: {e}")
        results["errors"].append(f"Sito web: {str(e)}")

    # 1b. PageSpeed Insights (Core Web Vitals, punteggi, suggerimenti)
    try:
        results["pagespeed"] = _analyze_pagespeed(website_url)
        logger.info(f"PageSpeed completato per {website_url}")
    except Exception as e:
        logger.warning(f"Errore PageSpeed per {website_url}: {e}")
        results["errors"].append(f"PageSpeed: {str(e)}")
        results["pagespeed"] = {"error": str(e)}

    # 2. Analisi SEO avanzata via SerpAPI (6 query)
    try:
        seo_data = _analyze_seo(website_url, company_name, city, sector)
        results["seo"] = seo_data.get("seo", {})
        results["google_business"] = seo_data.get("google_business", {})
        
        # Arricchisci GMB con Google Places API se abbiamo place_id
        gb_place_id = results["google_business"].get("place_id")
        if gb_place_id:
            try:
                places_data = _enrich_gmb_with_places_api(gb_place_id)
                if places_data.get("found"):
                    for k, v in places_data.items():
                        if v is not None:
                            results["google_business"][k] = v
                    logger.info(f"GMB arricchito con Places API: rating={places_data.get('rating')}, reviews={places_data.get('reviews_count')}, photos={places_data.get('photos_count')}")
            except Exception as e:
                logger.warning(f"Places API enrichment failed: {e}")
        
        results["competitors"] = seo_data.get("competitors", [])
        results["citations"] = seo_data.get("citations", [])
        results["indexed_pages"] = seo_data.get("indexed_pages", {"total": 0, "pages": []})
        
        # Keyword suggestions
        try:
            results["keyword_suggestions"] = _get_keyword_suggestions(sector, city)
        except Exception as e:
            logger.warning(f"Keyword suggestions error: {e}")
            results["keyword_suggestions"] = []
        
        # Aggiorna città e settore se estratti da SerpAPI
        if not results["city"] and seo_data.get("extracted_city"):
            results["city"] = seo_data["extracted_city"]
        if not results["sector"] and seo_data.get("extracted_sector"):
            results["sector"] = seo_data["extracted_sector"]
            
        logger.info(f"Analisi SerpAPI completata per {company_name}: {len(results['competitors'])} competitor, {len(results['citations'])} citazioni")
    except Exception as e:
        logger.warning(f"Errore analisi SEO per {company_name}: {e}")
        results["errors"].append(f"SEO: {str(e)}")

    # 3. Ricerca social media
    try:
        results["social_media"] = _find_social_media(website_url, company_name, social_links_db)
    except Exception as e:
        logger.warning(f"Errore ricerca social per {company_name}: {e}")
        results["errors"].append(f"Social: {str(e)}")

    # 4. Google Business Profile (Backup/Refine se Apify fallisce)
    # Nota: I dati principali sono già stati presi da _analyze_seo (Query 1)
    if not results["google_business"] or not results["google_business"].get("found"):
        try:
            results["google_business"] = _check_google_business(company_name)
        except Exception as e:
            logger.warning(f"Errore Google Business backup per {company_name}: {e}")


    # 5. Scraping avanzato via Apify (Facebook, Instagram, LinkedIn)
    try:
        from execution.scrape_apify import run_apify_scraping

        # Costruisci social_links dando priorità ai dati dal DB
        social_links = {}
        
        # 1. Carica profilazione dal DB (priorità)
        if social_links_db:
            for platform, data in social_links_db.items():
                # Se data è stringa (URL/Username)
                if isinstance(data, str):
                    social_links[platform.lower()] = data
                # Se data è dict (come ritornato da _find_social_media)
                elif isinstance(data, dict) and data.get("url"):
                    social_links[platform.lower()] = data["url"]

        # 2. Integra con link trovati nel sito solo se mancano
        sm = results.get("social_media", {})
        for platform in ["instagram", "facebook", "linkedin"]:
            if platform not in social_links and sm.get(platform):
                item = sm[platform]
                if isinstance(item, dict) and item.get("url"):
                    social_links[platform] = item["url"]
                elif isinstance(item, str):
                    social_links[platform] = item

        # Tenta di determinare la città se manca
        active_city = city
        if not active_city:
            gb = results.get("google_business", {})
            if gb.get("address"):
                # Estrai l'ultima parte dell'indirizzo (spesso la città)
                addr_parts = gb["address"].split(",")
                if len(addr_parts) >= 2:
                    # In Italia solitamente "Via ..., CAP Città (PROV)"
                    active_city = addr_parts[-2].strip().split(" ")[-1]
                else:
                    active_city = gb["address"]

        results["apify"] = run_apify_scraping(
            company_name=company_name,
            city=active_city,
            website=website_url,
            social_links=social_links,
            sector=sector,
        )
        logger.info(f"Apify scraping completato per {company_name}")

        # Fix 4: Passa dati Google Maps a google_business per GPT-4o
        apify_gm = results["apify"].get("google_maps", {})
        if apify_gm.get("found"):
            # Sovrascrivi/Estrai dati reali da Apify (più ricchi di SerpAPI)
            results["google_business"] = {
                "source": "apify_google_maps",
                "name": apify_gm.get("name"),
                "rating": apify_gm.get("rating"),
                "reviews_count": apify_gm.get("reviews_count"),
                "address": apify_gm.get("address"),
                "phone": apify_gm.get("phone"),
                "website": apify_gm.get("website"),
                "hours": apify_gm.get("opening_hours"),
                "category": apify_gm.get("category"),
                "photos": apify_gm.get("photos", []),
                "reviews": apify_gm.get("reviews", []), # Testi recensioni REALI
            }
            logger.info(f"Dati Google Business arricchiti con Apify per {company_name}")

    except Exception as e:
        logger.warning(f"Errore Apify per {company_name}: {e}")
        results["errors"].append(f"Apify: {str(e)}")
        results["apify"] = {"error": str(e)}

    # 6. Ricerca Perplexity AI (contesto mercato e reputazione online)
    try:
        results["perplexity"] = _perplexity_research(company_name, website_url)
        logger.info(f"Perplexity research completato per {company_name}")
    except Exception as e:
        logger.warning(f"Errore Perplexity per {company_name}: {e}")
        results["errors"].append(f"Perplexity: {str(e)}")
        results["perplexity"] = {"error": str(e)}

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


def _analyze_seo(website_url: str, company_name: str, city: str = "", sector: str = "") -> dict:
    """
    Analisi SEO avanzata via SerpAPI utilizzando 6 query dinamiche.
    Estrae dati GMB, competitor, citazioni e indicizzazione.
    """
    results = {
        "google_business": {"found": False, "source": "not_found"},
        "competitors": [],
        "citations": [],
        "indexed_pages": {"total": 0, "pages": []},
        "seo": {
            "search_queries": [],
            "organic_position": {
                "brand_query": None,
                "sector_local_query": None,
                "sector_regional_query": None
            }
        },
        "extracted_city": None,
        "extracted_sector": None
    }

    api_key = settings.SERPAPI_KEY
    if not api_key:
        logger.error("SERPAPI_KEY non trovata nelle impostazioni")
        return results

    domain = urlparse(website_url).netloc.replace("www.", "")
    
    # 1. QUERY 1: Brand (Knowledge Graph + Local Pack + Organic)
    try:
        q1 = company_name
        loc = f"{city}, Italy" if city else "Italy"
        params = {
            "q": q1,
            "hl": "it", "gl": "it", "location": loc,
            "api_key": api_key, "num": 10
        }
        resp = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
        data = resp.json()
        
        # Estrai Knowledge Graph
        kg = data.get("knowledge_graph", {})
        if kg:
            results["google_business"] = {
                "found": True,
                "source": "knowledge_graph",
                "title": kg.get("title"),
                "rating": kg.get("rating"),
                "reviews_count": kg.get("reviews"),
                "address": kg.get("address"),
                "phone": kg.get("phone"),
                "hours": kg.get("hours"),
                "website": kg.get("website"),
                "place_id": kg.get("place_id"),
                "category": kg.get("type"),
                "thumbnail": kg.get("thumbnail")
            }
            # Se city era vuota, prova a estrarla dall'indirizzo
            if not city and results["google_business"]["address"]:
                addr = results["google_business"]["address"]
                # Cerca pattern città dopo il CAP
                m = re.search(r'\d{5}\s+([A-Za-z\s]+)(?:\s+\()?', addr)
                if m:
                    results["extracted_city"] = m.group(1).strip()
                    city = results["extracted_city"]
            
            # Se sector era vuoto, usa la categoria
            if not sector and results["google_business"]["category"]:
                results["extracted_sector"] = results["google_business"]["category"]
                sector = results["extracted_sector"]

        # Se non c'è KG, prova il Local Pack
        if not results["google_business"]["found"] and "local_results" in data:
            for place in data.get("local_results", {}).get("places", []):
                # Match approssimativo sul nome o website
                if company_name.lower() in place.get("title", "").lower() or domain in place.get("links", {}).get("website", ""):
                    results["google_business"] = {
                        "found": True,
                        "source": "local_pack",
                        "title": place.get("title"),
                        "rating": place.get("rating"),
                        "reviews_count": place.get("reviews"),
                        "address": place.get("address"),
                        "phone": place.get("phone"),
                        "place_id": place.get("place_id"),
                        "website": place.get("links", {}).get("website")
                    }
                    break

        # Organic Position Brand
        brand_pos = None
        for i, res in enumerate(data.get("organic_results", []), 1):
            if domain in res.get("link", ""):
                brand_pos = i
                break
        
        results["seo"]["organic_position"]["brand_query"] = {
            "query": q1,
            "position": brand_pos,
            "total_results": data.get("search_information", {}).get("total_results", 0)
        }
        results["seo"]["search_queries"].append({"query": q1, "results": len(data.get("organic_results", []))})
        
        logger.info(f"[SERPAPI] Brand Query: {q1} — Found: {results['google_business']['found']} ({results['google_business']['source']}), Pos: {brand_pos}")

    except Exception as e:
        logger.error(f"Errore Query 1 SerpAPI: {e}")

    # 2. QUERY 2: Brand + Recensioni (Citazioni/Reputazione)
    try:
        q2 = f"{company_name} recensioni"
        params = {"q": q2, "hl": "it", "gl": "it", "api_key": api_key}
        data = requests.get("https://serpapi.com/search.json", params=params, timeout=30).json()
        
        for res in data.get("organic_results", []):
            link = res.get("link", "")
            title = res.get("title", "")
            snippet = res.get("snippet", "")
            # Se il brand o il dominio sono nel risultato, lo salviamo come citazione
            if company_name.lower() in title.lower() or domain in link:
                _add_citation(results["citations"], res)
                
        logger.info(f"[SERPAPI] Reputazione Query: {q2} — Citazioni trovate: {len(results['citations'])}")
    except Exception as e:
        logger.error(f"Errore Query 2 SerpAPI: {e}")

    # 3. QUERY 3: Settore + Città (Competitor Locali)
    if city and sector:
        try:
            sector_clean = sector.split("-")[0].strip() if "-" in sector else sector.strip()
            q3 = f"{sector_clean} {city}"
            params = {"q": q3, "hl": "it", "gl": "it", "location": f"{city}, Italy", "api_key": api_key}
            data = requests.get("https://serpapi.com/search.json", params=params, timeout=30).json()
            
            # Local Competitors
            for place in data.get("local_results", {}).get("places", []):
                # Escludi l'azienda stessa
                if company_name.lower() not in place.get("title", "").lower() and domain not in place.get("links", {}).get("website", ""):
                    _add_competitor(results["competitors"], place, "local_pack")

            # Organic Competitors (escludi portali)
            for res in data.get("organic_results", []):
                if not _is_portal(res.get("link", "")) and domain not in res.get("link", ""):
                    _add_competitor(results["competitors"], res, "organic")

            # Organic Position Sector Local
            local_sec_pos = None
            for i, res in enumerate(data.get("organic_results", []), 1):
                if domain in res.get("link", ""):
                    local_sec_pos = i
                    break
            results["seo"]["organic_position"]["sector_local_query"] = {
                "query": q3, "position": local_sec_pos,
                "total_results": data.get("search_information", {}).get("total_results", 0)
            }
            logger.info(f"[SERPAPI] Local Sector Query: {q3} — Competitors: {len(results['competitors'])}, Pos: {local_sec_pos}")
        except Exception as e:
            logger.error(f"Errore Query 3 SerpAPI: {e}")

    # 4. QUERY 4: Settore + Capoluogo (Competitor Regionali)
    if sector:
        capoluogo = "Cagliari" # Default per la Sardegna se non noto
        # TODO: Implementare mappatura città-capoluogo più precisa se necessario
        if city and city.lower() != capoluogo.lower():
            try:
                sector_clean = sector.split("-")[0].strip() if "-" in sector else sector.strip()
                q4 = f"{sector_clean} {capoluogo}"
                params = {"q": q4, "hl": "it", "gl": "it", "location": f"{capoluogo}, Italy", "api_key": api_key}
                data = requests.get("https://serpapi.com/search.json", params=params, timeout=30).json()
                
                # Aggiungi competitor senza duplicati
                for place in data.get("local_results", {}).get("places", []):
                    if company_name.lower() not in place.get("title", "").lower() and domain not in place.get("links", {}).get("website", ""):
                        _add_competitor(results["competitors"], place, "local_pack")
                
                for res in data.get("organic_results", []):
                    if not _is_portal(res.get("link", "")) and domain not in res.get("link", ""):
                        _add_competitor(results["competitors"], res, "organic")
                
                logger.info(f"[SERPAPI] Regional Sector Query: {q4} — Competitors totali: {len(results['competitors'])}")
            except Exception as e:
                logger.error(f"Errore Query 4 SerpAPI: {e}")

    # 5. QUERY 5: Pagine Indicizzate (site:)
    try:
        q5 = f"site:{domain}"
        params = {"q": q5, "hl": "it", "gl": "it", "api_key": api_key}
        data = requests.get("https://serpapi.com/search.json", params=params, timeout=30).json()
        
        results["indexed_pages"] = {
            "total": data.get("search_information", {}).get("total_results", 0),
            "pages": [{"title": r.get("title"), "link": r.get("link")} for r in data.get("organic_results", [])[:10]]
        }
        logger.info(f"[SERPAPI] Indexed Pages: {results['indexed_pages']['total']}")
    except Exception as e:
        logger.error(f"Errore Query 5 SerpAPI: {e}")

    # 6. QUERY 6: Citazioni / Presenza Online
    try:
        q6 = f'"{company_name}" OR "{domain}" -site:{domain}'
        params = {"q": q6, "hl": "it", "gl": "it", "api_key": api_key}
        data = requests.get("https://serpapi.com/search.json", params=params, timeout=30).json()
        
        for res in data.get("organic_results", []):
            _add_citation(results["citations"], res)
            
        logger.info(f"[SERPAPI] Citations Query: {q6} — Totali: {len(results['citations'])}")
    except Exception as e:
        logger.error(f"Errore Query 6 SerpAPI: {e}")

    return results


def _is_portal(url: str) -> bool:
    """Verifica se l'URL appartiene a un portale o directory."""
    portals = [
        "paginebianche.it", "paginegialle.it", "edilnet.it", "virgilio.it",
        "yelp.com", "tripadvisor.com", "infobel.com", "cylex-italia.it",
        "prontopro.it", "instapro.it", "houzz.it", "misterimprese.it",
        "paginegialle.it", "cybo.com", "guidaedilizia.it", "edilmap.it"
    ]
    domain = urlparse(url).netloc.lower()
    return any(p in domain for p in portals)


def _add_competitor(comp_list: list, item: dict, source: str):
    """Aggiunge un competitor alla lista se non già presente (max 5)."""
    if len(comp_list) >= 5:
        return

    name = item.get("title") or item.get("name")
    if not name: return
    
    # Evita duplicati pesanti
    if any(c["name"].lower() == name.lower() for c in comp_list):
        return
        
    # Pulisci website
    raw_website = item.get("links", {}).get("website") or item.get("link")
    if raw_website and any(x in raw_website.lower() for x in ["aggiungi sito", "add website", "aggiungisito"]):
        raw_website = None
    
    # Arrotondi rating
    raw_rating = item.get("rating")
    if raw_rating is not None:
        raw_rating = round(float(raw_rating), 1)
    
    # Pulisci indirizzo (rimuovi emoji e caratteri strani)
    import re as _re
    raw_address = item.get("address")
    if raw_address:
        raw_address = _re.sub(r"[^\w\s,./°]", "", raw_address).strip()
        raw_address = _re.sub(r'\s+', ' ', raw_address)
    
    comp_list.append({
        "name": name,
        "website": raw_website,
        "rating": raw_rating,
        "reviews_count": item.get("reviews"),
        "address": raw_address,
        "phone": item.get("phone"),
        "source": source,
        "position": item.get("position"),
        "place_id": item.get("place_id")
    })


def _add_citation(cit_list: list, item: dict):
    """Aggiunge una citazione classificandola per tipo."""
    link = item.get("link", "")
    domain = urlparse(link).netloc.lower().replace("www.", "")
    
    # Classificazione tipo
    cit_type = "other"
    if any(s in domain for s in ["facebook.com", "instagram.com", "linkedin.com", "tiktok.com", "youtube.com"]):
        cit_type = "social"
    elif "digidentitycard.com" in domain:
        cit_type = "digidentity_card"
    elif any(d in domain for d in ["paginegialle.it", "paginebianche.it", "edilnet.it", "virgilio.it", "yelp.com", "tripadvisor.com", "infobel.com"]):
        cit_type = "directory"
        
    # Evita duplicati esatti di link
    if any(c["link"] == link for c in cit_list):
        return
        
    cit_list.append({
        "title": item.get("title"),
        "link": link,
        "source_domain": domain,
        "type": cit_type,
        "snippet": item.get("snippet")
    })


def _find_social_media(website_url: str, company_name: str, social_links_db: dict = None) -> dict:
    """Cerca i profili social dell'azienda."""
    data = {
        "facebook": None,
        "instagram": None,
        "linkedin": None,
        "twitter": None,
        "youtube": None,
        "tiktok": None,
    }

    # Se sono presenti link social dal DB, usali con priorità
    if social_links_db:
        for platform, url in social_links_db.items():
            platform_lower = platform.lower()
            if platform_lower in data and url:
                data[platform_lower] = {"url": url, "found_on_website": False, "found_in_db": True}

    # Poi cerca nel sito web (sovrascrive solo se non trovato nel DB)
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
            if match and data[platform] is None:  # Solo se non trovato nel DB
                url = match.group(0)
                if not url.startswith("http"):
                    url = f"https://{url}"
                data[platform] = {"url": url, "found_on_website": True}

    except Exception as e:
        logger.warning(f"Errore ricerca social nel sito: {e}")

    return data




def _get_keyword_suggestions(sector: str, city: str) -> list:
    """Genera keyword strategiche per settore + città. Zero API calls."""
    if not sector or not city:
        return []
    
    sector_lower = sector.lower()
    city_lower = city.lower()
    
    # Keyword base: settore + città
    keywords = [
        f"{sector_lower} {city_lower}",
        f"{sector_lower} a {city_lower}",
        f"{sector_lower} {city_lower} prezzi",
        f"{sector_lower} {city_lower} preventivo",
        f"{sector_lower} {city_lower} opinioni",
        f"{sector_lower} {city_lower} migliore",
        f"{sector_lower} vicino a me",
        f"preventivo {sector_lower} {city_lower}",
        f"migliore {sector_lower} {city_lower}",
    ]
    
    # Keyword specifiche per macro-settori comuni
    sector_keywords = {
        "edil": ["ristrutturazione casa", "ristrutturazione bagno", "costruzione casa", "preventivo ristrutturazione", "impresa ristrutturazioni"],
        "ristor": ["ristorante", "trattoria", "dove mangiare", "ristorante economico", "ristorante pesce"],
        "estet": ["centro estetico", "trattamenti viso", "epilazione laser", "manicure pedicure", "massaggi"],
        "parruc": ["parrucchiere", "taglio capelli", "colore capelli", "barbiere", "salone bellezza"],
        "idraul": ["idraulico", "pronto intervento idraulico", "riparazione perdite", "sostituzione caldaia", "bagno nuovo"],
        "elettr": ["elettricista", "impianto elettrico", "pronto intervento elettricista", "domotica", "fotovoltaico"],
        "avvoc": ["avvocato", "studio legale", "consulenza legale", "avvocato divorzista", "avvocato penalista"],
        "dentist": ["dentista", "studio dentistico", "impianti dentali", "sbiancamento denti", "ortodonzia"],
        "meccan": ["officina meccanica", "meccanico auto", "tagliando auto", "revisione auto", "carrozzeria"],
    }
    
    for key, extra_kw in sector_keywords.items():
        if key in sector_lower:
            for kw in extra_kw:
                keywords.append(f"{kw} {city_lower}")
            break
    
    # Rimuovi duplicati mantenendo ordine
    seen = set()
    unique = []
    for k in keywords:
        if k not in seen:
            seen.add(k)
            unique.append(k)
    
    logger.info(f"[KEYWORDS] Generate {len(unique)} keyword per {sector} + {city}")
    return unique[:20]


def _enrich_gmb_with_places_api(place_id: str) -> dict:
    """Arricchisce i dati GMB usando Google Places API (più affidabile di SerpAPI)."""
    data = {}
    api_key = getattr(settings, 'GOOGLE_PAGESPEED_API_KEY', None) or os.environ.get('GOOGLE_PAGESPEED_API_KEY')
    if not api_key or not place_id:
        return data
    try:
        resp = requests.get(
            "https://maps.googleapis.com/maps/api/place/details/json",
            params={
                "place_id": place_id,
                "fields": "name,rating,user_ratings_total,formatted_address,formatted_phone_number,website,opening_hours,reviews,photos,types,business_status,url",
                "language": "it",
                "key": api_key,
            },
            timeout=15,
        )
        result = resp.json()
        if result.get("status") == "OK":
            place = result.get("result", {})
            data = {
                "found": True,
                "name": place.get("name"),
                "rating": place.get("rating"),
                "reviews_count": place.get("user_ratings_total"),
                "address": place.get("formatted_address"),
                "phone": place.get("formatted_phone_number"),
                "website": place.get("website"),
                "business_status": place.get("business_status"),
                "hours": place.get("opening_hours", {}).get("weekday_text"),
                "photos_count": len(place.get("photos", [])),
                "maps_url": place.get("url"),
                "types": place.get("types"),
                "source": "google_places_api",
            }
            # Salva recensioni con testo
            raw_reviews = place.get("reviews", [])
            if raw_reviews:
                data["reviews"] = []
                for rev in raw_reviews[:5]:
                    data["reviews"].append({
                        "author": rev.get("author_name"),
                        "rating": rev.get("rating"),
                        "text": rev.get("text", ""),
                        "time": rev.get("relative_time_description"),
                    })
            logger.info(f"Google Places API OK: {data.get('name')}, rating={data.get('rating')}, reviews={data.get('reviews_count')}, photos={data.get('photos_count')}, reviews_text={len(raw_reviews)}")
        else:
            logger.warning(f"Google Places API status: {result.get('status')} - {result.get('error_message','')}")
    except Exception as e:
        logger.warning(f"Google Places API error: {e}")
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

    # Arricchisci con Google Places API se abbiamo un place_id
    place_id = data.get("place_id") or kg.get("place_id") if 'kg' in dir() else None
    if not place_id:
        # Prova a estrarre place_id dal knowledge graph
        try:
            resp2 = requests.get(
                "https://serpapi.com/search.json",
                params={"q": company_name, "hl": "it", "gl": "it", "api_key": settings.SERPAPI_KEY},
                timeout=REQUEST_TIMEOUT,
            )
            kg2 = resp2.json().get("knowledge_graph", {})
            place_id = kg2.get("place_id")
        except Exception:
            pass
    if place_id:
        places_data = _enrich_gmb_with_places_api(place_id)
        if places_data.get("found"):
            for k, v in places_data.items():
                if v is not None:
                    data[k] = v
            logger.info(f"GMB arricchito con Places API per {company_name}")

    return data


def _perplexity_research(company_name: str, website_url: str) -> dict[str, Any]:
    """
    Usa Perplexity AI per ricerca contestuale sull'azienda.
    Restituisce informazioni su reputazione, mercato, competitor.
    """
    if not settings.PERPLEXITY_API_KEY:
        return {"error": "PERPLEXITY_API_KEY non configurata", "found": False}

    try:
        import requests as req

        prompt = (
            f"Analizza la presenza digitale e la reputazione dell'azienda '{company_name}' "
            f"(sito: {website_url}). Cerca informazioni su:\n"
            f"1. Reputazione online e recensioni\n"
            f"2. Posizionamento nel mercato locale\n"
            f"3. Principali competitor diretti\n"
            f"4. Punti di forza e debolezza della loro presenza digitale\n"
            f"5. Opportunità di miglioramento\n"
            f"Rispondi in italiano con dati concreti."
        )

        resp = req.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.PERPLEXITY_MODEL,
                "messages": [
                    {"role": "system", "content": "Sei un analista di digital marketing specializzato in PMI italiane. Rispondi con dati concreti e specifici."},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 2000,
                "temperature": 0.3,
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()

        content = data["choices"][0]["message"]["content"]
        citations = data.get("citations", [])

        return {
            "found": True,
            "analysis": content,
            "citations": citations,
            "model": data.get("model", settings.PERPLEXITY_MODEL),
            "tokens_used": data.get("usage", {}).get("total_tokens", 0),
        }

    except Exception as e:
        logger.warning(f"Errore Perplexity per {company_name}: {e}")
        return {"found": False, "error": str(e)}



def _analyze_pagespeed(website_url: str) -> dict[str, Any]:
    """
    Analisi PageSpeed Insights via API Google (gratuita).
    Restituisce Core Web Vitals, punteggi mobile e desktop, suggerimenti.
    """
    API_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    results = {
        "mobile": {},
        "desktop": {},
        "errors": [],
    }

    for strategy in ["mobile", "desktop"]:
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                params = {
                    "url": website_url,
                    "strategy": strategy,
                    "locale": "it",
                    "category": ["performance", "seo", "best-practices", "accessibility"],
                }
                
                # Aggiungi API Key se presente
                if settings.GOOGLE_PAGESPEED_API_KEY:
                    params["key"] = settings.GOOGLE_PAGESPEED_API_KEY

                resp = requests.get(API_URL, params=params, timeout=60)
                
                # Gestione Rate Limit (429) con backoff esponenziale
                if resp.status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)
                        logger.warning(f"⚠️ PageSpeed 429 (Rate Limit). Retry {attempt+1}/{max_retries} in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        resp.raise_for_status() # Lancia errore se superati i tentativi
                
                resp.raise_for_status()
                data = resp.json()

                # Lighthouse scores
                categories = data.get("lighthouseResult", {}).get("categories", {})
                scores = {}
                for cat_key, cat_data in categories.items():
                    scores[cat_key] = round((cat_data.get("score", 0) or 0) * 100)

                # Core Web Vitals
                field_data = data.get("loadingExperience", {}).get("metrics", {})
                cwv = {}
                metric_map = {
                    "LARGEST_CONTENTFUL_PAINT_MS": "lcp_ms",
                    "FIRST_INPUT_DELAY_MS": "fid_ms",
                    "CUMULATIVE_LAYOUT_SHIFT_SCORE": "cls",
                    "FIRST_CONTENTFUL_PAINT_MS": "fcp_ms",
                    "INTERACTION_TO_NEXT_PAINT": "inp_ms",
                    "EXPERIMENTAL_TIME_TO_FIRST_BYTE": "ttfb_ms",
                }
                for api_name, local_name in metric_map.items():
                    metric = field_data.get(api_name, {})
                    if metric:
                        cwv[local_name] = metric.get("percentile", metric.get("distributions", [{}]))

                # Audit principali (opportunità di miglioramento)
                audits = data.get("lighthouseResult", {}).get("audits", {})
                opportunities = []
                for audit_key, audit_data in audits.items():
                    if audit_data.get("score") is not None and audit_data["score"] < 0.9:
                        savings = audit_data.get("details", {}).get("overallSavingsMs", 0)
                        if savings > 0 or audit_data["score"] < 0.5:
                            opportunities.append({
                                "id": audit_key,
                                "title": audit_data.get("title", ""),
                                "description": audit_data.get("description", "")[:200],
                                "score": round(audit_data["score"] * 100),
                                "savings_ms": savings,
                            })

                opportunities.sort(key=lambda x: x.get("savings_ms", 0), reverse=True)

                results[strategy] = {
                    "scores": scores,
                    "core_web_vitals": cwv,
                    "opportunities": opportunities[:10],
                    "overall_category": data.get("loadingExperience", {}).get("overall_category", ""),
                }

                logger.info(
                    f"✅ PageSpeed {strategy}: performance={scores.get('performance', '?')}, "
                    f"seo={scores.get('seo', '?')}"
                )
                break # Esci dal ciclo retry se successo

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(f"🔄 Errore PageSpeed {strategy} (Tentativo {attempt+1}): {e}. Riprovo in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ PageSpeed {strategy} fallito dopo {max_retries} tentativi: {e}")
                    results["errors"].append(f"PageSpeed {strategy}: {str(e)}")
                    results[strategy] = {"error": str(e)}

    return results
