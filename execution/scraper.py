"""
DigIdentity Engine — Modulo di scraping per analisi presenza digitale PMI.

Esegue scraping multi-sorgente:
1. Sito web aziendale (HTML, meta tag, performance)
2. Google Search (posizionamento, SERP) — via Serper.dev / Google CSE / scraping diretto
3. Social media (pagine pubbliche) — senza Apify
4. Google Business Profile (via Google Places API)
"""

import logging
import re
import time
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from backend.app.core.config import settings
from execution.serp_engine import smart_search

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}


def _deduce_sector(website_data: dict) -> str:
    """Deduce il settore dai dati del sito web."""
    text_to_analyze = f"{website_data.get('title', '') or ''} {website_data.get('meta_description', '') or ''} "
    text_to_analyze += " ".join(website_data.get('h1_tags', []) or []) + " "
    text_to_analyze += " ".join(website_data.get('h2_tags', []) or [])
    text_to_analyze = text_to_analyze.lower()

    sector_map = {
        "Ristorante": ["ristorante", "pizzeria", "trattoria", "osteria", "cucina", "menu"],
        "Hotel": ["hotel", "albergo", "b&b", "bed and breakfast", "resort", "ospitalità"],
        "Edilizia": ["edilizia", "costruzioni", "ristrutturazioni", "impresa edile", "cartongesso", "serramenti"],
        "Bellezza": ["parrucchiere", "estetica", "centro estetico", "salone", "beauty", "barbiere"],
        "Salute": ["dentista", "studio medico", "poliambulatorio", "farmacia", "fisioterapia", "medico"],
        "Commercio": ["negozio", "shop", "vendita", "articoli", "abbigliamento", "calzature"],
        "Servizi Professionali": ["avvocato", "commercialista", "consulenza", "studio legale", "architetto", "ingegnere"],
        "Automotive": ["auto", "concessionaria", "officina", "carrozzeria", "noleggio", "pneumatici"],
        "Benessere": ["palestra", "fitness", "yoga", "piscina", "sport", "spa"],
    }

    for sector, keywords in sector_map.items():
        if any(kw in text_to_analyze for kw in keywords):
            return sector

    return "Attività Locale"


def scrape_lead(website_url: str, company_name: str, social_links_db: dict = None, city: str = "", sector: str = "", indirizzo: str = "") -> dict[str, Any]:
    """Esegue lo scraping completo di un'azienda."""
    if city:
        city = re.sub(r'\d{5}\s+', '', city)
        city = re.sub(r'\s+[A-Z]{2}$', '', city)
        city = city.strip()

    if indirizzo and not city:
        parti = [p.strip() for p in indirizzo.split(",")]
        if len(parti) >= 3:
            city = parti[-2].strip()
            city = re.sub(r'^\d{5}\s*', '', city).strip()
        elif len(parti) == 2:
            city = parti[-1].strip()
            city = re.sub(r'^\d{5}\s*', '', city).strip()
        logger.info(f"Città estratta dall'indirizzo: {city}")

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
        if not sector or sector == "Da identificare":
            sector = _deduce_sector(results["website"])
            results["sector"] = sector
            logger.info(f"Settore dedotto dal sito: {sector}")
    except Exception as e:
        logger.warning(f"Errore scraping sito {website_url}: {e}")
        results["errors"].append(f"Sito web: {str(e)}")

    # 1b. PageSpeed Insights
    try:
        results["pagespeed"] = _analyze_pagespeed(website_url)
        logger.info(f"PageSpeed completato per {website_url}")
    except Exception as e:
        logger.warning(f"Errore PageSpeed per {website_url}: {e}")
        results["errors"].append(f"PageSpeed: {str(e)}")
        results["pagespeed"] = {"error": str(e)}

    # 2. Analisi SEO avanzata (6 query) — via Serper.dev / CSE / scraping
    try:
        seo_data = _analyze_seo(website_url, company_name, city, sector)
        results["seo"] = seo_data.get("seo", {})
        results["google_business"] = seo_data.get("google_business", {})
        results["competitors"] = seo_data.get("competitors", [])
        results["citations"] = seo_data.get("citations", [])
        results["indexed_pages"] = seo_data.get("indexed_pages", {"total": 0, "pages": []})

        if not results["city"] and seo_data.get("extracted_city"):
            results["city"] = seo_data["extracted_city"]
        if not results["sector"] and seo_data.get("extracted_sector"):
            results["sector"] = seo_data["extracted_sector"]

        logger.info(f"Analisi SEO completata per {company_name}: {len(results['competitors'])} competitor, {len(results['citations'])} citazioni")
    except Exception as e:
        logger.warning(f"Errore analisi SEO per {company_name}: {e}")
        results["errors"].append(f"SEO: {str(e)}")

    # 3. Ricerca social media
    try:
        results["social_media"] = _find_social_media(website_url, company_name, social_links_db)
    except Exception as e:
        logger.warning(f"Errore ricerca social per {company_name}: {e}")
        results["errors"].append(f"Social: {str(e)}")

    # 4. Google Business Profile backup
    if not results["google_business"] or not results["google_business"].get("found"):
        try:
            results["google_business"] = _check_google_business(company_name)
        except Exception as e:
            logger.warning(f"Errore Google Business backup per {company_name}: {e}")

    # 5. Scraping social media (Facebook, Instagram, LinkedIn) - senza Apify
    try:
        from execution.scrape_social import run_social_scraping

        social_links = {}

        if social_links_db:
            for platform, data in social_links_db.items():
                if isinstance(data, str):
                    social_links[platform.lower()] = data
                elif isinstance(data, dict) and data.get("url"):
                    social_links[platform.lower()] = data["url"]

        sm = results.get("social_media", {})
        for platform in ["instagram", "facebook", "linkedin"]:
            if platform not in social_links and sm.get(platform):
                item = sm[platform]
                if isinstance(item, dict) and item.get("url"):
                    social_links[platform] = item["url"]
                elif isinstance(item, str):
                    social_links[platform] = item

        active_city = city
        if not active_city:
            gb = results.get("google_business", {})
            if gb.get("address"):
                addr_parts = gb["address"].split(",")
                if len(addr_parts) >= 2:
                    active_city = addr_parts[-2].strip().split(" ")[-1]
                else:
                    active_city = gb["address"]

        results["apify"] = run_social_scraping(
            company_name=company_name,
            city=active_city,
            website=website_url,
            social_links=social_links,
            sector=sector,
            rapidapi_key=getattr(settings, 'RAPIDAPI_KEY', None),
        )
        logger.info(f"Social scraping completato per {company_name}")

    except Exception as e:
        logger.warning(f"Errore social scraping per {company_name}: {e}")
        results["errors"].append(f"Social: {str(e)}")
        results["apify"] = {"error": str(e)}

    # 6. Ricerca Perplexity AI
    try:
        results["perplexity"] = _perplexity_research(company_name, website_url)
        logger.info(f"Perplexity research completato per {company_name}")
    except Exception as e:
        logger.warning(f"Errore Perplexity per {company_name}: {e}")
        results["errors"].append(f"Perplexity: {str(e)}")
        results["perplexity"] = {"error": str(e)}

    logger.info(f"Scraping completato per {company_name}: {len(results['errors'])} errori")
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

    data["title"] = soup.title.string.strip() if soup.title and soup.title.string else None
    meta_desc = soup.find("meta", attrs={"name": "description"})
    data["meta_description"] = meta_desc["content"].strip() if meta_desc and meta_desc.get("content") else None
    viewport = soup.find("meta", attrs={"name": "viewport"})
    data["has_responsive_meta"] = viewport is not None
    favicon = soup.find("link", rel=lambda x: x and "icon" in x)
    data["has_favicon"] = favicon is not None
    data["h1_tags"] = [h.get_text(strip=True) for h in soup.find_all("h1")][:10]
    data["h2_tags"] = [h.get_text(strip=True) for h in soup.find_all("h2")][:20]

    images = soup.find_all("img")
    data["images_count"] = len(images)
    data["images_without_alt"] = sum(1 for img in images if not img.get("alt"))

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

    text = soup.get_text(separator=" ", strip=True)
    data["word_count"] = len(text.split())

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

    data["has_analytics"] = any(t in data["technologies_detected"] for t in ["Google Analytics", "Google Tag Manager"])
    data["has_cookie_banner"] = any(t in data["technologies_detected"] for t in ["Cookiebot", "GDPR Cookie"])

    json_ld = soup.find_all("script", type="application/ld+json")
    data["structured_data"] = len(json_ld) > 0

    email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    phone_pattern = re.compile(r"(?:\+39\s?)?(?:0\d{1,3}[\s.-]?\d{5,9}|\d{3}[\s.-]?\d{6,7})")
    found_emails = email_pattern.findall(text)
    found_phones = phone_pattern.findall(text)
    data["contact_info"] = {
        "emails": list(set(found_emails))[:5],
        "phones": list(set(found_phones))[:5],
    }

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
    Analisi SEO via smart_search (Serper.dev → Google CSE → scraping diretto).
    Sostituisce SerpAPI mantenendo la stessa struttura di output.
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
                "sector_regional_query": None,
            },
        },
        "extracted_city": None,
        "extracted_sector": None,
    }

    serper_key = getattr(settings, 'SERPER_KEY', None)
    cse_key = getattr(settings, 'GOOGLE_CSE_KEY', None)
    cx = getattr(settings, 'GOOGLE_CX', None)
    domain = urlparse(website_url).netloc.replace("www.", "")

    # ── QUERY 1: Brand (Knowledge Graph + Local Pack + Organic) ──
    try:
        q1 = company_name
        data = smart_search(
            query=q1,
            serper_key=serper_key,
            google_cse_key=cse_key,
            google_cx=cx,
            need_knowledge_graph=True,
            need_local_pack=True,
        )

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
                "thumbnail": kg.get("thumbnail"),
            }
            if not city and results["google_business"]["address"]:
                addr = results["google_business"]["address"]
                m = re.search(r'\d{5}\s+([A-Za-z\s]+?)(?:\s*\(|$)', addr)
                if m:
                    results["extracted_city"] = m.group(1).strip()
                else:
                    parts = [p.strip() for p in addr.split(",")]
                    if len(parts) >= 2:
                        candidate = re.sub(r'^\d{5}\s*', '', parts[-2]).strip()
                        candidate = re.sub(r'\s*\([A-Z]{2}\)\s*$', '', candidate)
                        candidate = re.sub(r'\s+[A-Z]{2}$', '', candidate)
                        if candidate and not candidate.isdigit():
                            results["extracted_city"] = candidate
                if results["extracted_city"]:
                    city = results["extracted_city"]
                    logger.info(f"[SEO] Città estratta: {city}")

            if not sector and results["google_business"]["category"]:
                results["extracted_sector"] = results["google_business"]["category"]
                sector = results["extracted_sector"]

        if not results["google_business"]["found"]:
            for place in data.get("local_results", {}).get("places", []):
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
                        "website": place.get("links", {}).get("website"),
                    }
                    break

        brand_pos = None
        for i, res in enumerate(data.get("organic_results", []), 1):
            if domain in res.get("link", ""):
                brand_pos = i
                break

        results["seo"]["organic_position"]["brand_query"] = {
            "query": q1,
            "position": brand_pos,
            "total_results": data.get("search_information", {}).get("total_results", 0),
        }
        results["seo"]["search_queries"].append({"query": q1, "results": len(data.get("organic_results", []))})
        logger.info(f"[SEO] Q1 Brand: found={results['google_business']['found']}, pos={brand_pos}")

    except Exception as e:
        logger.error(f"Errore Query 1: {e}")

    # ── QUERY 2: Brand + Recensioni (citazioni) ──
    try:
        q2 = f"{company_name} recensioni"
        data = smart_search(query=q2, serper_key=serper_key, google_cse_key=cse_key, google_cx=cx)
        for res in data.get("organic_results", []):
            if company_name.lower() in res.get("title", "").lower() or domain in res.get("link", ""):
                _add_citation(results["citations"], res)
        logger.info(f"[SEO] Q2 Recensioni: {len(results['citations'])} citazioni")
    except Exception as e:
        logger.error(f"Errore Query 2: {e}")

    # ── QUERY 3: Settore + Città (competitor locali) ──
    if city and sector:
        try:
            sector_clean = sector.split("-")[0].strip() if "-" in sector else sector.strip()
            if city.lower() in sector_clean.lower():
                sector_clean = re.sub(re.escape(city), '', sector_clean, flags=re.IGNORECASE).strip()
            q3 = f"{sector_clean} {city}"
            data = smart_search(
                query=q3,
                serper_key=serper_key,
                google_cse_key=cse_key,
                google_cx=cx,
                need_local_pack=True,
            )
            for place in data.get("local_results", {}).get("places", []):
                if company_name.lower() not in place.get("title", "").lower():
                    _add_competitor(results["competitors"], place, "local_pack")
            for res in data.get("organic_results", []):
                if not _is_portal(res.get("link", "")) and domain not in res.get("link", ""):
                    _add_competitor(results["competitors"], res, "organic")

            local_sec_pos = None
            for i, res in enumerate(data.get("organic_results", []), 1):
                if domain in res.get("link", ""):
                    local_sec_pos = i
                    break
            results["seo"]["organic_position"]["sector_local_query"] = {
                "query": q3, "position": local_sec_pos,
                "total_results": data.get("search_information", {}).get("total_results", 0),
            }
            logger.info(f"[SEO] Q3 Competitor locali: {len(results['competitors'])}, pos={local_sec_pos}")
        except Exception as e:
            logger.error(f"Errore Query 3: {e}")

    # ── QUERY 4: Settore + Capoluogo (competitor regionali) ──
    if sector:
        capoluogo = "Cagliari"
        if city and city.lower() != capoluogo.lower():
            try:
                sector_clean = sector.split("-")[0].strip() if "-" in sector else sector.strip()
                if city.lower() in sector_clean.lower():
                    sector_clean = re.sub(re.escape(city), '', sector_clean, flags=re.IGNORECASE).strip()
                q4 = f"{sector_clean} {capoluogo}"
                data = smart_search(
                    query=q4,
                    serper_key=serper_key,
                    google_cse_key=cse_key,
                    google_cx=cx,
                    need_local_pack=True,
                )
                for place in data.get("local_results", {}).get("places", []):
                    if company_name.lower() not in place.get("title", "").lower():
                        _add_competitor(results["competitors"], place, "local_pack")
                for res in data.get("organic_results", []):
                    if not _is_portal(res.get("link", "")) and domain not in res.get("link", ""):
                        _add_competitor(results["competitors"], res, "organic")
                logger.info(f"[SEO] Q4 Competitor regionali: {len(results['competitors'])}")
            except Exception as e:
                logger.error(f"Errore Query 4: {e}")

    # ── QUERY 5: Pagine indicizzate (site:) — scraping diretto ok ──
    try:
        q5 = f"site:{domain}"
        data = smart_search(query=q5, serper_key=serper_key, google_cse_key=cse_key, google_cx=cx)
        results["indexed_pages"] = {
            "total": data.get("search_information", {}).get("total_results", 0),
            "pages": [{"title": r.get("title"), "link": r.get("link")} for r in data.get("organic_results", [])[:10]],
        }
        logger.info(f"[SEO] Q5 Pagine indicizzate: {results['indexed_pages']['total']}")
    except Exception as e:
        logger.error(f"Errore Query 5: {e}")

    # ── QUERY 6: Citazioni / presenza online — scraping diretto ok ──
    try:
        q6 = f'"{company_name}" OR "{domain}" -site:{domain}'
        data = smart_search(query=q6, serper_key=serper_key, google_cse_key=cse_key, google_cx=cx)
        for res in data.get("organic_results", []):
            _add_citation(results["citations"], res)
        logger.info(f"[SEO] Q6 Citazioni totali: {len(results['citations'])}")
    except Exception as e:
        logger.error(f"Errore Query 6: {e}")

    return results


def _is_portal(url: str) -> bool:
    """Verifica se l'URL appartiene a un portale o directory."""
    portals = [
        "paginebianche.it", "paginegialle.it", "edilnet.it", "virgilio.it",
        "yelp.com", "tripadvisor.com", "infobel.com", "cylex-italia.it",
        "prontopro.it", "instapro.it", "houzz.it", "misterimprese.it",
        "cybo.com", "guidaedilizia.it", "edilmap.it",
    ]
    domain = urlparse(url).netloc.lower()
    return any(p in domain for p in portals)


def _add_competitor(comp_list: list, item: dict, source: str):
    """Aggiunge un competitor alla lista se non già presente (max 5)."""
    if len(comp_list) >= 5:
        return
    name = item.get("title") or item.get("name")
    if not name:
        return
    if any(c["name"].lower() == name.lower() for c in comp_list):
        return
    comp_list.append({
        "name": name,
        "website": item.get("links", {}).get("website") or item.get("link"),
        "rating": item.get("rating"),
        "reviews_count": item.get("reviews"),
        "address": item.get("address"),
        "phone": item.get("phone"),
        "source": source,
        "position": item.get("position"),
        "place_id": item.get("place_id"),
    })


def _add_citation(cit_list: list, item: dict):
    """Aggiunge una citazione classificandola per tipo."""
    link = item.get("link", "")
    domain = urlparse(link).netloc.lower().replace("www.", "")

    cit_type = "other"
    if any(s in domain for s in ["facebook.com", "instagram.com", "linkedin.com", "tiktok.com", "youtube.com"]):
        cit_type = "social"
    elif "digidentitycard.com" in domain:
        cit_type = "digidentity_card"
    elif any(d in domain for d in ["paginegialle.it", "paginebianche.it", "tripadvisor.com", "yelp.com"]):
        cit_type = "directory"

    if any(c["link"] == link for c in cit_list):
        return

    cit_list.append({
        "title": item.get("title"),
        "link": link,
        "source_domain": domain,
        "type": cit_type,
        "snippet": item.get("snippet"),
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

    if social_links_db:
        for platform, url in social_links_db.items():
            platform_lower = platform.lower()
            if platform_lower in data and url:
                data[platform_lower] = {"url": url, "found_on_website": False, "found_in_db": True}

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
            if match and data[platform] is None:
                url = match.group(0)
                if not url.startswith("http"):
                    url = f"https://{url}"
                data[platform] = {"url": url, "found_on_website": True}

    except Exception as e:
        logger.warning(f"Errore ricerca social nel sito: {e}")

    return data


def _check_google_business(company_name: str) -> dict:
    """Verifica la presenza su Google Business via smart_search."""
    data = {
        "found": False,
        "rating": None,
        "reviews_count": None,
        "address": None,
        "phone": None,
        "hours": None,
        "category": None,
    }

    try:
        result = smart_search(
            query=company_name,
            serper_key=getattr(settings, 'SERPER_KEY', None),
            google_cse_key=getattr(settings, 'GOOGLE_CSE_KEY', None),
            google_cx=getattr(settings, 'GOOGLE_CX', None),
            need_local_pack=True,
            need_knowledge_graph=True,
        )

        places = result.get("local_results", {}).get("places", [])
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
    """Usa Perplexity AI per ricerca contestuale sull'azienda."""
    if not settings.PERPLEXITY_API_KEY:
        return {"error": "PERPLEXITY_API_KEY non configurata", "found": False}

    try:
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

        resp = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.PERPLEXITY_MODEL,
                "messages": [
                    {"role": "system", "content": "Sei un analista di digital marketing specializzato in PMI italiane."},
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
        return {
            "found": True,
            "analysis": content,
            "citations": data.get("citations", []),
            "model": data.get("model", settings.PERPLEXITY_MODEL),
            "tokens_used": data.get("usage", {}).get("total_tokens", 0),
        }

    except Exception as e:
        logger.warning(f"Errore Perplexity per {company_name}: {e}")
        return {"found": False, "error": str(e)}


def _analyze_pagespeed(website_url: str) -> dict[str, Any]:
    """Analisi PageSpeed Insights via API Google."""
    API_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    results = {"mobile": {}, "desktop": {}, "errors": []}

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
                if settings.GOOGLE_PAGESPEED_API_KEY:
                    params["key"] = settings.GOOGLE_PAGESPEED_API_KEY

                resp = requests.get(API_URL, params=params, timeout=60)

                if resp.status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)
                        logger.warning(f"PageSpeed 429. Retry {attempt+1}/{max_retries} in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        resp.raise_for_status()

                resp.raise_for_status()
                data = resp.json()

                categories = data.get("lighthouseResult", {}).get("categories", {})
                scores = {k: round((v.get("score", 0) or 0) * 100) for k, v in categories.items()}

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
                logger.info(f"PageSpeed {strategy}: performance={scores.get('performance', '?')}, seo={scores.get('seo', '?')}")
                break

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(f"Errore PageSpeed {strategy} (tentativo {attempt+1}): {e}. Riprovo in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"PageSpeed {strategy} fallito: {e}")
                    results["errors"].append(f"PageSpeed {strategy}: {str(e)}")
                    results[strategy] = {"error": str(e)}

    return results