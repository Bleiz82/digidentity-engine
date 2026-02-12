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

    # 2. Analisi SEO via SerpAPI
    try:
        results["seo"] = _analyze_seo(website_url, company_name, city, sector)
        # Salva i competitor identificati dalla query SEO
        if "competitors" in results["seo"] and results["seo"]["competitors"]:
            results["competitors"] = results["seo"]["competitors"]
            logger.info(f"Identificati {len(results['competitors'])} competitor per {company_name}")
    except Exception as e:
        logger.warning(f"Errore analisi SEO per {company_name}: {e}")
        results["errors"].append(f"SEO: {str(e)}")

    # 3. Ricerca social media
    try:
        results["social_media"] = _find_social_media(website_url, company_name, social_links_db)
    except Exception as e:
        logger.warning(f"Errore ricerca social per {company_name}: {e}")
        results["errors"].append(f"Social: {str(e)}")

    # 4. Google Business Profile
    try:
        results["google_business"] = _check_google_business(company_name)
    except Exception as e:
        logger.warning(f"Errore Google Business per {company_name}: {e}")
        results["errors"].append(f"Google Business: {str(e)}")


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
    """Analisi SEO via SerpAPI: posizionamento su Google."""
    data = {
        "search_queries": [],
        "organic_results": [],
        "total_results_for_brand": 0,
        "knowledge_graph": None,
        "local_results": [],
        "competitors": [],
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

    competitive_query = None
    if city and sector:
        # Pulisci il settore (prendi solo la prima parte prima del trattino)
        sector_clean = sector.split("-")[0].strip() if "-" in sector else sector.strip()
        competitive_query = f"{sector_clean} {city}"
        queries.append(competitive_query)

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
                item_link = item.get("link", "")
                item_domain = urlparse(item_link).netloc.replace("www.", "")
                query_data["organic_results"].append({
                    "position": item.get("position"),
                    "title": item.get("title"),
                    "link": item_link,
                    "snippet": item.get("snippet"),
                    "domain": item_domain,
                })

            # Se è la query competitiva, estrai i competitor
            if query == competitive_query:
                for item in query_data["organic_results"]:
                    if item["domain"] != domain:
                        data["competitors"].append({
                            "name": item["title"],
                            "link": item["link"],
                            "domain": item["domain"],
                            "snippet": item["snippet"],
                            "position": item["position"]
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
