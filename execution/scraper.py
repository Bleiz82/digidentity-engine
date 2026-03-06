"""
DigIdentity Engine — Scraper v3

Architettura a 6 layer:
  Layer 0: Smart Discovery (Serper + Claude) — trova nomi reali e profili
  Layer 1: Scraping sito web — HTML, meta tag, tecnologie
  Layer 2: Google APIs native — Places, Geocoding, Knowledge Graph, PageSpeed
  Layer 3: SerpAPI (solo 2 query) — posizione brand + posizione settore
  Layer 4: Apify — Instagram, Facebook, LinkedIn (scraping avanzato)
  Layer 5: AI Research — Perplexity (reputazione e mercato)
"""

import logging
import re
import time
import json
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}


# ══════════════════════════════════════════════════════════
#  FUNZIONE PRINCIPALE
# ══════════════════════════════════════════════════════════

def scrape_lead(
    website_url: str,
    company_name: str,
    social_links_db: dict = None,
    city: str = "",
    sector: str = "",
    indirizzo: str = "",
    nome_titolare: str = "",
    email: str = "",
    telefono: str = "",
) -> dict[str, Any]:
    """
    Esegue lo scraping completo di un'azienda con architettura a 6 layer.
    """
    logger.info(f"[SCRAPER] === Inizio scraping v3 per {company_name} ===")

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
        "discovery": {},
        "google_places": {},
        "google_geocoding": {},
        "google_knowledge_graph": {},
        "errors": [],
    }

    # ── LAYER 0: Smart Discovery ──
    try:
        from execution.smart_discovery import smart_discovery

        discovery = smart_discovery(
            nome_azienda=company_name,
            indirizzo=indirizzo,
            email=email,
            telefono=telefono,
            nome_titolare=nome_titolare,
            sito_web=website_url,
            citta=city,
            settore=sector,
        )
        results["discovery"] = discovery

        # Aggiorna dati con quelli scoperti
        if discovery.get("citta_confermata") and not city:
            city = discovery["citta_confermata"]
            results["city"] = city
        if discovery.get("settore_rilevato") and (not sector or sector.lower() in ("da identificare", "altro", "non specificato", "")):
            sector = discovery["settore_rilevato"]
            results["sector"] = sector
        if discovery.get("sito_web_confermato") and not website_url:
            website_url = discovery["sito_web_confermato"]
            results["website_url"] = website_url

        # Costruisci social_links arricchiti dal discovery
        if social_links_db is None:
            social_links_db = {}
        if discovery.get("facebook_url") and "facebook" not in social_links_db:
            social_links_db["facebook"] = discovery["facebook_url"]
        if discovery.get("instagram_username") and "instagram" not in social_links_db:
            social_links_db["instagram"] = discovery["instagram_username"]
        if discovery.get("linkedin_url") and "linkedin" not in social_links_db:
            social_links_db["linkedin"] = discovery["linkedin_url"]

        logger.info(f"[SCRAPER] Discovery completato: GMB='{discovery.get('nome_google_business')}', varianti={len(discovery.get('varianti_nome', []))}")
    except Exception as e:
        logger.warning(f"[SCRAPER] Errore Discovery: {e}")
        results["errors"].append(f"Discovery: {str(e)}")

    # ── LAYER 1: Scraping sito web ──
    try:
        results["website"] = _scrape_website(website_url)
    except Exception as e:
        logger.warning(f"[SCRAPER] Errore scraping sito: {e}")
        results["errors"].append(f"Sito web: {str(e)}")

    # ── LAYER 2: Google APIs native ──

    # 2a. PageSpeed Insights
    try:
        results["pagespeed"] = _analyze_pagespeed(website_url)
        logger.info(f"[SCRAPER] PageSpeed completato")
    except Exception as e:
        logger.warning(f"[SCRAPER] Errore PageSpeed: {e}")
        results["errors"].append(f"PageSpeed: {str(e)}")

    # 2b. Google Places API (New) — dati GMB completi
    try:
        place_query = results.get("discovery", {}).get("nome_google_business") or company_name
        place_city = city or ""
        results["google_places"] = _google_places_search(place_query, place_city)

        # Se Places ha trovato dati, arricchisci google_business
        gp = results["google_places"]
        if gp.get("found"):
            results["google_business"] = {
                "found": True,
                "source": "google_places_api",
                "title": gp.get("name"),
                "rating": gp.get("rating"),
                "reviews_count": gp.get("user_ratings_total"),
                "address": gp.get("formatted_address"),
                "phone": gp.get("phone"),
                "website": gp.get("website"),
                "hours": gp.get("opening_hours"),
                "category": gp.get("primary_type") or gp.get("types", [None])[0] if gp.get("types") else None,
                "place_id": gp.get("place_id"),
                "photos": gp.get("photos", []),
                "reviews": gp.get("reviews", []),
            }
            # Aggiorna città se mancante
            if not city and gp.get("city"):
                city = gp["city"]
                results["city"] = city

            logger.info(f"[SCRAPER] Google Places: {gp.get('name')} — rating {gp.get('rating')}, {gp.get('user_ratings_total')} recensioni")

            # 2b-bis. Nearby Search per competitor
#            try:
#                if gp.get("lat") and gp.get("lng") and gp.get("primary_type"):
#                    nearby = _google_places_nearby(
#                        gp["lat"], gp["lng"],
#                        gp.get("primary_type", ""),
#                        company_name
#                    )
#                    for comp in nearby:
#                        _add_competitor(results["competitors"], comp, "google_places_nearby")
#                    logger.info(f"[SCRAPER] Places Nearby: {len(nearby)} competitor trovati")
#            except Exception as e:
#                logger.warning(f"[SCRAPER] Errore Places Nearby: {e}")

    except Exception as e:
        logger.warning(f"[SCRAPER] Errore Google Places: {e}")
        results["errors"].append(f"Google Places: {str(e)}")

    # 2c. Google Geocoding API
    try:
        address_to_geocode = indirizzo or results.get("google_business", {}).get("address", "")
        if address_to_geocode:
            results["google_geocoding"] = _google_geocoding(address_to_geocode)
            logger.info(f"[SCRAPER] Geocoding completato")
    except Exception as e:
        logger.warning(f"[SCRAPER] Errore Geocoding: {e}")

    # 2d. Knowledge Graph Search API
    try:
        results["google_knowledge_graph"] = _google_knowledge_graph(company_name)
        kg = results["google_knowledge_graph"]
        if kg.get("found"):
            logger.info(f"[SCRAPER] Knowledge Graph: {kg.get('name')} — {kg.get('description')}")
    except Exception as e:
        logger.warning(f"[SCRAPER] Errore Knowledge Graph: {e}")

    # ── LAYER 3: SerpAPI (solo 2 query) ──
    try:
        seo_data = _analyze_seo_serpapi(website_url, company_name, city, sector, indirizzo=indirizzo)
        results["seo"] = seo_data.get("seo", {})
        results["citations"] = seo_data.get("citations", [])
        results["indexed_pages"] = seo_data.get("indexed_pages", {"total": 0, "pages": []})

        # Competitor da SerpAPI (aggiungi senza duplicati)
        for comp in seo_data.get("competitors", []):
            _add_competitor(results["competitors"], comp, comp.get("source", "serpapi"))

        # Se Google Places non ha trovato GMB, prova con SerpAPI
        if not results["google_business"].get("found") and seo_data.get("google_business", {}).get("found"):
            results["google_business"] = seo_data["google_business"]

        # Aggiorna città e settore se estratti
        if not city and seo_data.get("extracted_city"):
            city = seo_data["extracted_city"]
            results["city"] = city
        if not sector and seo_data.get("extracted_sector"):
            sector = seo_data["extracted_sector"]
            results["sector"] = sector

        logger.info(f"[SCRAPER] SerpAPI completato: {len(results['competitors'])} competitor, {len(results['citations'])} citazioni")

        # Fallback: se nessun competitor trovato, cerca su SerpAPI Google Maps
        if not results["competitors"] and sector and city:
            try:
                logger.info(f"[SCRAPER] Competitor vuoti, fallback SerpAPI Google Maps: '{sector} {city}'")
                gps = results.get("google_places", {})
                gps_lat = gps.get("lat")
                gps_lng = gps.get("lng")
                maps_params = {
                    "engine": "google_maps",
                    "q": f"{sector} {city}",
                    "hl": "it",
                    "gl": "it",
                    "api_key": settings.SERPAPI_KEY,
                }
                if gps_lat and gps_lng:
                    maps_params["ll"] = f"@{gps_lat},{gps_lng},13z"
                
                import httpx
                from urllib.parse import urlencode
                maps_url = "https://serpapi.com/search?" + urlencode(maps_params, safe="@,")
                maps_resp = httpx.get(maps_url, timeout=15)
                maps_resp.raise_for_status()
                maps_data = maps_resp.json()
                
                for place in maps_data.get("local_results", [])[:8]:
                    if company_name.lower() not in place.get("title", "").lower():
                        _add_competitor(results["competitors"], {
                            "name": place.get("title"),
                            "rating": place.get("rating"),
                            "reviews_count": place.get("reviews"),
                            "address": place.get("address"),
                            "website": place.get("website"),
                            "phone": place.get("phone"),
                        }, "serpapi_maps")
                
                logger.info(f"[SCRAPER] SerpAPI Maps fallback: {len(results['competitors'])} competitor trovati")
            except Exception as e:
                logger.warning(f"[SCRAPER] Errore SerpAPI Maps fallback: {e}")

    except Exception as e:
        logger.warning(f"[SCRAPER] Errore SerpAPI: {e}")
        results["errors"].append(f"SerpAPI: {str(e)}")

    # ── LAYER 3b: Citazioni e pagine indicizzate via Serper.dev (gratis) ──
    try:
        domain = urlparse(website_url).netloc.replace("www.", "")
        _enrich_citations_serper(results, company_name, domain)
    except Exception as e:
        logger.warning(f"[SCRAPER] Errore citazioni Serper: {e}")

    # ── LAYER 4: Social media + Apify ──
    try:
        results["social_media"] = _find_social_media(website_url, company_name, social_links_db)
    except Exception as e:
        logger.warning(f"[SCRAPER] Errore ricerca social: {e}")
        results["errors"].append(f"Social: {str(e)}")

    try:
        from execution.scrape_apify import run_apify_scraping

        social_links = _build_social_links(social_links_db, results)
        active_city = city or _extract_city_from_results(results)

        results["apify"] = run_apify_scraping(
            company_name=company_name,
            city=active_city,
            website=website_url,
            social_links=social_links,
            sector=sector,
        )
        logger.info(f"[SCRAPER] Apify completato")

        # Arricchisci google_business con dati Apify Google Maps se disponibili
        apify_gm = results["apify"].get("google_maps", {})
        if apify_gm.get("found") and not results["google_business"].get("found"):
            results["google_business"] = {
                "found": True,
                "source": "apify_google_maps",
                "title": apify_gm.get("name"),
                "rating": apify_gm.get("rating"),
                "reviews_count": apify_gm.get("reviews_count"),
                "address": apify_gm.get("address"),
                "phone": apify_gm.get("phone"),
                "website": apify_gm.get("website"),
                "hours": apify_gm.get("opening_hours"),
                "category": apify_gm.get("category"),
                "photos": apify_gm.get("photos", []),
                "reviews": apify_gm.get("reviews", []),
            }
    except Exception as e:
        logger.warning(f"[SCRAPER] Errore Apify: {e}")
        results["errors"].append(f"Apify: {str(e)}")
        results["apify"] = {"error": str(e)}

    # ── LAYER 5: Perplexity AI Research ──
    try:
        results["perplexity"] = _perplexity_research(company_name, website_url, city, sector)
        logger.info(f"[SCRAPER] Perplexity completato")
    except Exception as e:
        logger.warning(f"[SCRAPER] Errore Perplexity: {e}")
        results["errors"].append(f"Perplexity: {str(e)}")
        results["perplexity"] = {"error": str(e)}

    logger.info(f"[SCRAPER] === Scraping completato per {company_name}: {len(results['errors'])} errori ===")
    return results


# ══════════════════════════════════════════════════════════
#  LAYER 1: SCRAPING SITO WEB
# ══════════════════════════════════════════════════════════

def _scrape_website(url: str) -> dict:
    """Scraping del sito web: meta tag, struttura, contenuti, performance."""
    data = {
        "url": url, "reachable": False, "load_time_ms": None, "status_code": None,
        "title": None, "meta_description": None, "h1_tags": [], "h2_tags": [],
        "has_ssl": url.startswith("https"), "has_responsive_meta": False,
        "has_favicon": False, "has_analytics": False, "has_cookie_banner": False,
        "images_count": 0, "images_without_alt": 0,
        "internal_links_count": 0, "external_links_count": 0, "word_count": 0,
        "technologies_detected": [], "pages_found": [], "contact_info": {},
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
    viewport = soup.find("meta", attrs={"name": "viewport"})
    data["has_responsive_meta"] = viewport is not None
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
        "React": ["react", "__next"], "Vue.js": ["vue.js", "__vue"],
        "jQuery": ["jquery"], "Bootstrap": ["bootstrap"], "Tailwind": ["tailwind"],
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


# ══════════════════════════════════════════════════════════
#  LAYER 2: GOOGLE APIs NATIVE
# ══════════════════════════════════════════════════════════

def _google_places_search(company_name: str, city: str = "") -> dict:
    """
    Google Places API (New) — Cerca l'attività e restituisce dati completi.
    Usa Text Search per massima flessibilità.
    """
    api_key = settings.GOOGLE_API_KEY
    if not api_key:
        return {"found": False, "error": "GOOGLE_API_KEY mancante"}

    query = f"{company_name} {city}".strip()

    try:
        # Text Search (New)
        resp = requests.post(
            "https://places.googleapis.com/v1/places:searchText",
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": (
                    "places.id,places.displayName,places.formattedAddress,"
                    "places.rating,places.userRatingCount,places.websiteUri,"
                    "places.nationalPhoneNumber,places.internationalPhoneNumber,"
                    "places.currentOpeningHours,places.regularOpeningHours,"
                    "places.primaryType,places.primaryTypeDisplayName,"
                    "places.types,places.reviews,places.photos,"
                    "places.location,places.businessStatus,"
                    "places.editorialSummary,places.addressComponents"
                ),
            },
            json={"textQuery": query, "languageCode": "it", "maxResultCount": 1},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        places = data.get("places", [])
        if not places:
            return {"found": False, "error": "Nessun risultato"}

        place = places[0]

        # Estrai città dai componenti dell'indirizzo
        place_city = ""
        for comp in place.get("addressComponents", []):
            if "locality" in comp.get("types", []):
                place_city = comp.get("longText", "")
                break

        # Estrai recensioni
        reviews = []
        for r in place.get("reviews", [])[:5]:
            reviews.append({
                "text": r.get("text", {}).get("text", ""),
                "rating": r.get("rating"),
                "author": r.get("authorAttribution", {}).get("displayName", ""),
                "date": r.get("publishTime", ""),
            })

        # Estrai foto URL
        photos = []
        for p in place.get("photos", [])[:5]:
            photo_name = p.get("name", "")
            if photo_name:
                photos.append(
                    f"https://places.googleapis.com/v1/{photo_name}/media"
                    f"?maxHeightPx=400&maxWidthPx=600&key={api_key}"
                )

        location = place.get("location", {})

        return {
            "found": True,
            "source": "google_places_api_new",
            "place_id": place.get("id"),
            "name": place.get("displayName", {}).get("text", ""),
            "formatted_address": place.get("formattedAddress", ""),
            "city": place_city,
            "rating": place.get("rating"),
            "user_ratings_total": place.get("userRatingCount", 0),
            "phone": place.get("nationalPhoneNumber") or place.get("internationalPhoneNumber"),
            "website": place.get("websiteUri"),
            "primary_type": place.get("primaryTypeDisplayName", {}).get("text", ""),
            "types": place.get("types", []),
            "opening_hours": place.get("regularOpeningHours", {}).get("weekdayDescriptions", []),
            "business_status": place.get("businessStatus", ""),
            "editorial_summary": place.get("editorialSummary", {}).get("text", ""),
            "reviews": reviews,
            "photos": photos,
            "lat": location.get("latitude"),
            "lng": location.get("longitude"),
        }
    except Exception as e:
        logger.warning(f"[PLACES] Errore: {e}")
        return {"found": False, "error": str(e)}


def _google_places_nearby(lat: float, lng: float, place_type: str, exclude_name: str) -> list:
    """Google Places Nearby Search — trova competitor nella stessa zona."""
    api_key = settings.GOOGLE_API_KEY
    if not api_key:
        return []

    try:
        resp = requests.post(
            "https://places.googleapis.com/v1/places:searchNearby",
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": (
                    "places.id,places.displayName,places.formattedAddress,"
                    "places.rating,places.userRatingCount,places.websiteUri,"
                    "places.nationalPhoneNumber"
                ),
            },
            json={
                "locationRestriction": {
                    "circle": {
                        "center": {"latitude": lat, "longitude": lng},
                        "radius": 5000.0,
                    }
                },
                "includedPrimaryTypes": [place_type] if place_type else [],
                "maxResultCount": 10,
                "languageCode": "it",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        competitors = []
        for p in data.get("places", []):
            name = p.get("displayName", {}).get("text", "")
            if name and exclude_name.lower() not in name.lower():
                competitors.append({
                    "name": name,
                    "rating": p.get("rating"),
                    "reviews_count": p.get("userRatingCount"),
                    "address": p.get("formattedAddress"),
                    "website": p.get("websiteUri"),
                    "phone": p.get("nationalPhoneNumber"),
                    "place_id": p.get("id"),
                })
        return competitors[:5]
    except Exception as e:
        logger.warning(f"[PLACES NEARBY] Errore: {e}")
        return []


def _google_geocoding(address: str) -> dict:
    """Google Geocoding API — coordinate e verifica indirizzo."""
    api_key = settings.GOOGLE_API_KEY
    if not api_key:
        return {"found": False}

    try:
        resp = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": address, "key": api_key, "language": "it"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "OK" or not data.get("results"):
            return {"found": False, "status": data.get("status")}

        result = data["results"][0]
        location = result["geometry"]["location"]

        # Estrai componenti indirizzo
        components = {}
        for comp in result.get("address_components", []):
            for t in comp["types"]:
                components[t] = comp.get("long_name", "")

        return {
            "found": True,
            "formatted_address": result.get("formatted_address"),
            "lat": location.get("lat"),
            "lng": location.get("lng"),
            "city": components.get("locality", ""),
            "province": components.get("administrative_area_level_2", ""),
            "region": components.get("administrative_area_level_1", ""),
            "postal_code": components.get("postal_code", ""),
            "country": components.get("country", ""),
        }
    except Exception as e:
        logger.warning(f"[GEOCODING] Errore: {e}")
        return {"found": False, "error": str(e)}


def _google_knowledge_graph(query: str) -> dict:
    """Google Knowledge Graph Search API — entità strutturata."""
    api_key = settings.GOOGLE_API_KEY
    if not api_key:
        return {"found": False}

    try:
        resp = requests.get(
            "https://kgsearch.googleapis.com/v1/entities:search",
            params={"query": query, "key": api_key, "languages": "it", "limit": 3},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        elements = data.get("itemListElement", [])
        if not elements:
            return {"found": False}

        entity = elements[0].get("result", {})
        return {
            "found": True,
            "name": entity.get("name"),
            "description": entity.get("description"),
            "detailed_description": entity.get("detailedDescription", {}).get("articleBody"),
            "types": entity.get("@type", []),
            "url": entity.get("url"),
            "image": entity.get("image", {}).get("contentUrl"),
            "result_score": elements[0].get("resultScore", 0),
        }
    except Exception as e:
        logger.warning(f"[KG] Errore: {e}")
        return {"found": False, "error": str(e)}


def _analyze_pagespeed(website_url: str) -> dict[str, Any]:
    """PageSpeed Insights API — Core Web Vitals, scores, suggerimenti."""
    API_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    results = {"mobile": {}, "desktop": {}, "errors": []}

    for strategy in ["mobile", "desktop"]:
        max_retries = 3
        retry_delay = 2
        for attempt in range(max_retries):
            try:
                params = {
                    "url": website_url, "strategy": strategy, "locale": "it",
                    "category": ["performance", "seo", "best-practices", "accessibility"],
                }
                if settings.GOOGLE_PAGESPEED_API_KEY:
                    params["key"] = settings.GOOGLE_PAGESPEED_API_KEY

                resp = requests.get(API_URL, params=params, timeout=60)
                if resp.status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)
                        logger.warning(f"PageSpeed 429. Retry {attempt+1} in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        resp.raise_for_status()

                resp.raise_for_status()
                data = resp.json()

                categories = data.get("lighthouseResult", {}).get("categories", {})
                scores = {}
                for cat_key, cat_data in categories.items():
                    scores[cat_key] = round((cat_data.get("score", 0) or 0) * 100)

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
                                "id": audit_key, "title": audit_data.get("title", ""),
                                "description": audit_data.get("description", "")[:200],
                                "score": round(audit_data["score"] * 100), "savings_ms": savings,
                            })
                opportunities.sort(key=lambda x: x.get("savings_ms", 0), reverse=True)

                results[strategy] = {
                    "scores": scores, "core_web_vitals": cwv,
                    "opportunities": opportunities[:10],
                    "overall_category": data.get("loadingExperience", {}).get("overall_category", ""),
                }
                logger.info(f"PageSpeed {strategy}: perf={scores.get('performance', '?')}, seo={scores.get('seo', '?')}")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                else:
                    logger.error(f"PageSpeed {strategy} fallito: {e}")
                    results["errors"].append(f"PageSpeed {strategy}: {str(e)}")
                    results[strategy] = {"error": str(e)}
    return results


# ══════════════════════════════════════════════════════════
#  LAYER 3: SerpAPI (solo 2 query)
# ══════════════════════════════════════════════════════════

def _analyze_seo_serpapi(website_url: str, company_name: str, city: str = "", sector: str = "", indirizzo: str = "") -> dict:
    """
    SerpAPI — solo 2 query per risparmiare crediti (limite 250/mese).
    Query 1: "{nome_azienda} {città}" — posizione brand
    Query 2: "{settore} {città}" — posizione settore + competitor
    """
    results = {
        "google_business": {"found": False, "source": "not_found"},
        "competitors": [],
        "citations": [],
        "indexed_pages": {"total": 0, "pages": []},
        "seo": {
            "search_queries": [],
            "organic_position": {"brand_query": None, "sector_local_query": None},
        },
        "extracted_city": None,
        "extracted_sector": None,
    }

    api_key = settings.SERPAPI_KEY
    if not api_key:
        logger.warning("[SERPAPI] SERPAPI_KEY non trovata — skip")
        return results

    domain = urlparse(website_url).netloc.replace("www.", "")

    # ── Query 1: Brand ──
    try:
        q1 = company_name.strip()
        loc = f"{city}, Italy" if city else "Italy"
        params = {"q": q1, "hl": "it", "gl": "it", "location": loc, "api_key": api_key, "num": 20}
        resp = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
        data = resp.json()

        # Knowledge Graph
        kg = data.get("knowledge_graph", {})
        if kg:
            results["google_business"] = {
                "found": True, "source": "knowledge_graph",
                "title": kg.get("title"), "rating": kg.get("rating"),
                "reviews_count": kg.get("reviews"), "address": kg.get("address"),
                "phone": kg.get("phone"), "hours": kg.get("hours"),
                "website": kg.get("website"), "place_id": kg.get("place_id"),
                "category": kg.get("type"), "thumbnail": kg.get("thumbnail"),
            }
            # Estrai città
            if not city and kg.get("address"):
                addr_parts = kg["address"].split(",")
                for part in addr_parts:
                    part = part.strip()
                    if part and not any(c.isdigit() for c in part[:3]):
                        city = part
                        break
        # Posizione organica brand
        brand_pos = None
        for i, res in enumerate(data.get("organic_results", []), 1):
            if domain in res.get("link", ""):
                brand_pos = i
                break

        results["seo"]["organic_position"]["brand_query"] = {
            "query": q1, "position": brand_pos,
            "total_results": data.get("search_information", {}).get("total_results", 0),
        }
        results["seo"]["search_queries"].append({"query": q1, "results": len(data.get("organic_results", []))})

        # Citazioni dalla query brand
        # Cerca nome flessibile: parole principali del nome (>3 chars, no forme giuridiche)
        _skip_words = {"srls", "srl", "sas", "snc", "spa", "s.r.l.", "s.r.l.s.", "s.a.s.", "s.n.c.", "s.p.a.", "di", "e", "il", "la", "da", "del", "dei", "delle"}
        _name_words = [w.lower() for w in company_name.split() if len(w) > 3 and w.lower().strip(".") not in _skip_words]
        _known_citation_domains = ["digidentitycard.com", "paginegialle.it", "paginebianche.it", "edilnet.it", "yelp.com", "tripadvisor.com", "trustpilot.com", "virgilio.it", "infobel.com"]
        for res in data.get("organic_results", []):
            res_link = res.get("link", "")
            if domain not in res_link:
                res_title = res.get("title", "").lower()
                res_snippet = res.get("snippet", "").lower() if res.get("snippet") else ""
                # Citazione se: nome trovato nel titolo/snippet O sito di citazione noto
                name_match = sum(1 for w in _name_words if w in res_title or w in res_snippet) >= max(1, len(_name_words) // 2)
                known_domain = any(d in res_link for d in _known_citation_domains)
                if name_match or known_domain:
                    _add_citation(results["citations"], res)

        logger.info(f"[SERPAPI] Q1 '{q1}': GMB={results['google_business']['found']}, Pos={brand_pos}")
    except Exception as e:
        logger.error(f"[SERPAPI] Errore Query 1: {e}")

    # ── Query 2: Settore + Città ──
    if city and sector:
        try:
            sector_clean = sector.split("-")[0].strip() if "-" in sector else sector.strip()
            if city.lower() in sector_clean.lower():
                sector_clean = re.sub(re.escape(city), '', sector_clean, flags=re.IGNORECASE).strip()
            q2 = f"{sector_clean} {city}"
            loc2 = f"{city}, Italy" if city else "Italy"
            params = {"q": q2, "hl": "it", "gl": "it", "location": loc2, "api_key": api_key, "num": 20}
            data = requests.get("https://serpapi.com/search.json", params=params, timeout=30).json()

            # Competitor dal local pack
            for place in data.get("local_results", {}).get("places", []):
                if company_name.lower() not in place.get("title", "").lower() and domain not in place.get("links", {}).get("website", ""):
                    _add_competitor(results["competitors"], {
                        "name": place.get("title"), "rating": place.get("rating"),
                        "reviews_count": place.get("reviews"), "address": place.get("address"),
                        "website": place.get("links", {}).get("website"),
                        "phone": place.get("phone"), "place_id": place.get("place_id"),
                    }, "local_pack")

            # Competitor organici
            for res in data.get("organic_results", []):
                if not _is_portal(res.get("link", "")) and domain not in res.get("link", ""):
                    _add_competitor(results["competitors"], {
                        "name": res.get("title"), "website": res.get("link"),
                    }, "organic")

            # Posizione settore
            sector_pos = None
            for i, res in enumerate(data.get("organic_results", []), 1):
                if domain in res.get("link", ""):
                    sector_pos = i
                    break
            results["seo"]["organic_position"]["sector_local_query"] = {
                "query": q2, "position": sector_pos,
                "total_results": data.get("search_information", {}).get("total_results", 0),
            }

            logger.info(f"[SERPAPI] Q2 '{q2}': {len(results['competitors'])} competitor, Pos={sector_pos}")
        except Exception as e:
            logger.error(f"[SERPAPI] Errore Query 2: {e}")

    return results


# ══════════════════════════════════════════════════════════
#  LAYER 3b: CITAZIONI E INDICIZZAZIONE (Serper.dev gratis)
# ══════════════════════════════════════════════════════════

def _enrich_citations_serper(results: dict, company_name: str, domain: str):
    """Usa Serper.dev (gratis) per citazioni e pagine indicizzate."""
    if not settings.SERPER_KEY:
        return

    from execution.smart_discovery import _serper_search

    # Pagine indicizzate
    try:
        site_data = _serper_search(f"site:{domain}", num=10)
        organic = site_data.get("organic", [])
        results["indexed_pages"] = {
            "total": site_data.get("searchParameters", {}).get("totalResults", len(organic)),
            "pages": [{"title": r.get("title"), "link": r.get("link")} for r in organic[:10]],
        }
        logger.info(f"[SERPER] Pagine indicizzate: {results['indexed_pages']['total']}")
    except Exception as e:
        logger.warning(f"[SERPER] Errore indexed pages: {e}")

    # Citazioni extra
    try:
        cit_data = _serper_search(f'"{company_name}" -site:{domain}', num=10)
        for r in cit_data.get("organic", []):
            _add_citation(results["citations"], {
                "title": r.get("title"), "link": r.get("link"), "snippet": r.get("snippet"),
            })
        logger.info(f"[SERPER] Citazioni totali: {len(results['citations'])}")
    except Exception as e:
        logger.warning(f"[SERPER] Errore citazioni: {e}")


# ══════════════════════════════════════════════════════════
#  LAYER 5: PERPLEXITY AI
# ══════════════════════════════════════════════════════════

def _perplexity_research(company_name: str, website_url: str, city: str = "", sector: str = "") -> dict[str, Any]:
    """Perplexity AI — ricerca contestuale su reputazione e mercato."""
    if not settings.PERPLEXITY_API_KEY:
        return {"error": "PERPLEXITY_API_KEY non configurata", "found": False}

    try:
        prompt = (
            f"Analizza la presenza digitale e la reputazione dell'azienda '{company_name}' "
            f"(sito: {website_url}, città: {city or 'non nota'}, settore: {sector or 'non noto'}). "
            f"Cerca informazioni su:\n"
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

        return {
            "found": True,
            "analysis": data["choices"][0]["message"]["content"],
            "citations": data.get("citations", []),
            "model": data.get("model", settings.PERPLEXITY_MODEL),
            "tokens_used": data.get("usage", {}).get("total_tokens", 0),
        }
    except Exception as e:
        logger.warning(f"[PERPLEXITY] Errore: {e}")
        return {"found": False, "error": str(e)}


# ══════════════════════════════════════════════════════════
#  FUNZIONI HELPER
# ══════════════════════════════════════════════════════════

def _find_social_media(website_url: str, company_name: str, social_links_db: dict = None) -> dict:
    """Cerca i profili social dell'azienda nel sito e nel DB."""
    data = {"facebook": None, "instagram": None, "linkedin": None, "twitter": None, "youtube": None, "tiktok": None}

    if social_links_db:
        for platform, url in social_links_db.items():
            pl = platform.lower()
            if pl in data and url:
                data[pl] = {"url": url, "found_on_website": False, "found_in_db": True}

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


def _build_social_links(social_links_db: dict, results: dict) -> dict:
    """Costruisce dizionario social links per Apify, unendo DB + discovery + sito."""
    social_links = {}

    # Priorità 1: DB
    if social_links_db:
        for platform, data in social_links_db.items():
            if isinstance(data, str):
                social_links[platform.lower()] = data
            elif isinstance(data, dict) and data.get("url"):
                social_links[platform.lower()] = data["url"]

    # Priorità 2: Discovery
    discovery = results.get("discovery", {})
    if discovery.get("facebook_url") and "facebook" not in social_links:
        social_links["facebook"] = discovery["facebook_url"]
    if discovery.get("instagram_username") and "instagram" not in social_links:
        social_links["instagram"] = discovery["instagram_username"]
    if discovery.get("linkedin_url") and "linkedin" not in social_links:
        social_links["linkedin"] = discovery["linkedin_url"]

    # Priorità 3: Trovati nel sito
    sm = results.get("social_media", {})
    for platform in ["instagram", "facebook", "linkedin"]:
        if platform not in social_links and sm.get(platform):
            item = sm[platform]
            if isinstance(item, dict) and item.get("url"):
                social_links[platform] = item["url"]
            elif isinstance(item, str):
                social_links[platform] = item

    return social_links


def _extract_city_from_results(results: dict) -> str:
    """Estrai città dai risultati disponibili."""
    if results.get("city"):
        return results["city"]
    gb = results.get("google_business", {})
    if gb.get("address"):
        addr_parts = gb["address"].split(",")
        if len(addr_parts) >= 2:
            return addr_parts[-2].strip().split(" ")[-1]
    return ""


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
    """Aggiunge un competitor alla lista (max 8, senza duplicati)."""
    if len(comp_list) >= 8:
        return
    name = item.get("name") or item.get("title")
    if not name:
        return
    if any(c["name"].lower() == name.lower() for c in comp_list):
        return
    comp_list.append({
        "name": name,
        "website": item.get("website") or item.get("link"),
        "rating": item.get("rating"),
        "reviews_count": item.get("reviews_count") or item.get("reviews"),
        "address": item.get("address"),
        "phone": item.get("phone"),
        "source": source,
        "place_id": item.get("place_id"),
    })


def _add_citation(cit_list: list, item: dict):
    """Aggiunge una citazione classificandola per tipo."""
    link = item.get("link", "")
    if not link:
        return
    domain = urlparse(link).netloc.lower().replace("www.", "")

    cit_type = "other"
    if any(s in domain for s in ["facebook.com", "instagram.com", "linkedin.com", "tiktok.com", "youtube.com"]):
        cit_type = "social"
    elif "digidentitycard.com" in domain:
        cit_type = "digidentity_card"
    elif any(d in domain for d in ["paginegialle.it", "paginebianche.it", "edilnet.it", "virgilio.it", "yelp.com", "tripadvisor.com", "infobel.com"]):
        cit_type = "directory"

    if any(c["link"] == link for c in cit_list):
        return

    cit_list.append({
        "title": item.get("title"), "link": link,
        "source_domain": domain, "type": cit_type,
        "snippet": item.get("snippet"),
    })
