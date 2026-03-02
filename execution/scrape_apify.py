"""
DigIdentity Engine — Modulo Apify per scraping avanzato.

Utilizza gli Actor Apify per raccogliere dati da:
1. Google Maps (recensioni, rating, foto, orari)
2. Instagram (profilo pubblico, post, engagement)
3. Facebook (pagina pubblica, post recenti)
4. TikTok (profilo, video recenti)

Costi stimati: ~$0.30-0.50 per diagnosi completa.
"""

import os
import logging
import time
import re
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)

APIFY_API_KEY = os.getenv("APIFY_API_KEY", "")
APIFY_BASE_URL = "https://api.apify.com/v2"

# Timeout per attesa risultati Actor (secondi)
ACTOR_TIMEOUT = 180
POLL_INTERVAL = 5


def _run_actor(actor_id: str, run_input: dict, timeout: int = ACTOR_TIMEOUT) -> list[dict]:
    """
    Lancia un Actor Apify e attende i risultati.
    
    Args:
        actor_id: ID dell'actor (es. "nwua9Gu5YrADL7ZDj", timeout=300)
        run_input: Input JSON per l'actor
        timeout: Timeout massimo in secondi
    
    Returns:
        Lista di risultati dall'actor
    """
    if not APIFY_API_KEY:
        logger.warning("APIFY_API_KEY non configurata — skip Actor %s", actor_id)
        return []

    headers = {"Authorization": f"Bearer {APIFY_API_KEY}"}

    # Avvia l'actor
    try:
        start_url = f"{APIFY_BASE_URL}/acts/{actor_id}/runs"
        resp = requests.post(
            start_url,
            json=run_input,
            headers=headers,
            params={"timeout": timeout, "memory": 1024},
            timeout=30,
        )
        resp.raise_for_status()
        run_data = resp.json()["data"]
        run_id = run_data["id"]
        logger.info(f"Actor {actor_id} avviato — run_id: {run_id}")
    except Exception as e:
        logger.error(f"Errore avvio Actor {actor_id}: {e}")
        return []

    # Poll per completamento
    elapsed = 0
    status_url = f"{APIFY_BASE_URL}/actor-runs/{run_id}"

    while elapsed < timeout:
        try:
            status_resp = requests.get(status_url, headers=headers, timeout=15)
            status_resp.raise_for_status()
            status = status_resp.json()["data"]["status"]

            if status == "SUCCEEDED":
                logger.info(f"Actor {actor_id} completato in {elapsed}s")
                break
            elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
                logger.error(f"Actor {actor_id} fallito con status: {status}")
                return []
        except Exception as e:
            logger.warning(f"Errore poll Actor {actor_id}: {e}")

        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL

    if elapsed >= timeout:
        logger.error(f"Actor {actor_id} timeout dopo {timeout}s")
        return []

    # Recupera risultati dal dataset
    try:
        dataset_id = run_data.get("defaultDatasetId")
        if not dataset_id:
            # Recupera dal run aggiornato
            status_resp = requests.get(status_url, headers=headers, timeout=15)
            dataset_id = status_resp.json()["data"]["defaultDatasetId"]

        items_url = f"{APIFY_BASE_URL}/datasets/{dataset_id}/items"
        items_resp = requests.get(
            items_url,
            headers=headers,
            params={"format": "json", "limit": 50},
            timeout=30,
        )
        items_resp.raise_for_status()
        results = items_resp.json()
        logger.info(f"Actor {actor_id}: {len(results)} risultati ottenuti")
        return results
    except Exception as e:
        logger.error(f"Errore recupero risultati Actor {actor_id}: {e}")
        return []


def scrape_google_maps(company_name: str, city: str = "", sector: str = "") -> dict[str, Any]:
    """
    Scraping Google Maps via Apify per dati local business.
    Actor: compass/crawler-google-places (nwua9Gu5YrADL7ZDj)
    """
    # Pulizia nome azienda (rimozione suffissi legali per ricerca migliore)
    clean_name = company_name
    suffixes = [
        r"\bS\.?r\.?l\.?s?\.?\b", r"\bS\.?p\.?A\.?\b", r"\bS\.?N\.?C\.?\b", 
        r"\bS\.?a\.?s\.?\.?\b", r"\bS\.?S\.?\.?\b", r"\bS\.?R\.?L\.?\b",
        r"\bDitta Individuale\b", r"\bdi\b .*", r"\bEredi\b .*"
    ]
    for suffix in suffixes:
        clean_name = re.sub(suffix, "", clean_name, flags=re.IGNORECASE).strip()
    
    # Costruisci query multiple per massimizzare le probabilità
    search_queries = []
    if clean_name and city:
        search_queries.append(f"{clean_name} {city}")
    
    if clean_name:
        search_queries.append(clean_name)
    
    if sector and city:
        search_queries.append(f"{sector} {city}")
        
    if company_name != clean_name:
        search_queries.append(company_name)

    # Rimuovi duplicati mantenendo l'ordine
    unique_queries = []
    for q in search_queries:
        if q and q not in unique_queries:
            unique_queries.append(q)

    logger.info(f"[APIFY] Google Maps scraping con query multiple: {unique_queries}")

    run_input = {
        "searchStringsArray": unique_queries,
        "maxCrawledPlacesPerSearch": 1,
        "language": "it",
        "countryCode": "it",
        "includeHistogram": False,
        "includeOpeningHours": True,
        "includePeopleAlsoSearch": False,
        "maxReviews": 5,
        "reviewsSort": "newest",
        "scrapeReviewerName": True,
    }

    # Timeout alzato a 300s come richiesto
    results = _run_actor("nwua9Gu5YrADL7ZDj", run_input, timeout=300)

    if not results:
        return {"source": "google_maps", "found": False, "error": "Attività non trovata"}

    # Trova il match migliore (primo risultato)
    place = results[0]

    # Estrai recensioni testuali (Fix 1C)
    reviews_summary = []
    for review in place.get("reviews", [])[:5]:
        reviews_summary.append({
            "text": review.get("text", "") or "",
            "stars": review.get("stars"),
            "publishedAtDate": review.get("publishedAtDate"),
            "reviewer_name": review.get("name", "Utente Google"),
        })

    # Estrai prime 5 foto URL
    photos = []
    for image in place.get("images", [])[:5]:
        if isinstance(image, dict) and image.get("url"):
            photos.append(image["url"])
        elif isinstance(image, str):
            photos.append(image)

    return {
        "source": "google_maps",
        "found": True,
        "name": place.get("title", ""),
        "rating": place.get("totalScore"),
        "reviews_count": place.get("reviewsCount", 0),
        "address": place.get("address", ""),
        "phone": place.get("phone", ""),
        "website": place.get("website", ""),
        "category": place.get("categoryName", ""),
        "opening_hours": place.get("openingHours", []),
        "photos": photos,
        "reviews": reviews_summary,
        "place_id": place.get("placeId", ""),
    }


def scrape_instagram(username: str = "", company_name: str = "", website: str = "") -> dict[str, Any]:
    """
    Scraping Instagram via Apify (Dual-Call: Details + Posts).
    Actor: apify/instagram-scraper (shu8hvrXbJbY3Eb9W)
    """
    if not username and not company_name:
        return {"source": "instagram", "found": False, "error": "Nessun dato fornito"}

    if username:
        username = username.strip().lstrip("@").split("/")[-1]
        ig_url = f"https://www.instagram.com/{username}/"
    else:
        # Qui potremmo implementare una ricerca, ma per ora usiamo il nome azienda se possibile
        return {"source": "instagram", "found": False, "error": "Username mancante"}

    logger.info(f"[APIFY] Instagram Dual-Call per: {ig_url}")

    # Chiamata 1: Posts (per engagement)
    run_input_posts = {
        "directUrls": [ig_url],
        "resultsType": "posts",
        "resultsLimit": 12,
    }
    posts_results = _run_actor("shu8hvrXbJbY3Eb9W", run_input_posts)

    # Chiamata 2: Details (per profilo completo)
    run_input_details = {
        "directUrls": [ig_url],
        "resultsType": "details",
        "resultsLimit": 1,
    }
    details_results = _run_actor("shu8hvrXbJbY3Eb9W", run_input_details)

    if not details_results and not posts_results:
        return {"source": "instagram", "found": False, "error": "Profilo non trovato"}

    # Merge risultati
    profile = details_results[0] if details_results else {}
    
    # Fallback username dai post se details fallisce
    if not profile and posts_results:
        first_post = posts_results[0]
        profile["username"] = first_post.get("ownerUsername") or username
        profile["fullName"] = first_post.get("ownerUsername")
        logger.warning(f"[APIFY] Fallback profiling per {username}")

    # Analisi post (dalla Chiamata 1)
    posts = []
    total_likes = 0
    total_comments = 0
    for p in posts_results[:12]:
        l = p.get("likesCount", 0) or 0
        c = p.get("commentsCount", 0) or 0
        total_likes += l
        total_comments += c
        posts.append({
            "likes": l,
            "comments": c,
            "caption": (p.get("caption") or "")[:150],
            "url": p.get("url"),
            "timestamp": p.get("timestamp"),
        })

    followers = profile.get("followersCount", 0) or 0
    avg_likes = total_likes / max(len(posts), 1)
    avg_comments = total_comments / max(len(posts), 1)
    engagement_rate = round(((avg_likes + avg_comments) / followers) * 100, 2) if followers > 0 else 0

    return {
        "source": "instagram",
        "found": True,
        "username": profile.get("username", username),
        "full_name": profile.get("fullName", ""),
        "biography": profile.get("biography", ""),
        "followers": followers,
        "following": profile.get("followsCount", 0),
        "posts_count": profile.get("postsCount", 0),
        "is_verified": profile.get("verified", False),
        "is_business": profile.get("isBusinessAccount", False),
        "external_url": profile.get("externalUrl", ""),
        "profile_pic_url": profile.get("profilePicUrl", ""),
        "engagement_rate": engagement_rate,
        "avg_likes": round(avg_likes),
        "avg_comments": round(avg_comments),
        "recent_posts": posts,
    }


def _scrape_facebook_serp_fallback(company_name: str, page_url: str = "") -> dict[str, Any]:
    """Fallback SerpAPI per profili personali o quando Apify fallisce"""
    logger.info(f"[APIFY] Fallback SerpAPI per Facebook: {company_name}")
    try:
        import os
        import requests as req
        # Prova tutte le varianti comuni per compatibilità
        api_key = os.getenv("SERPAPI_KEY") or os.getenv("SERP_API_KEY") or os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return {"found": False, "error": "SerpAPI key mancante"}

        params = {
            "q": f'"{company_name}" facebook',
            "hl": "it",
            "gl": "it",
            "api_key": api_key,
            "num": 5
        }
        resp = req.get("https://serpapi.com/search.json", params=params, timeout=20)
        data = resp.json()
        
        # Cerca nel Knowledge Graph
        kg = data.get("knowledge_graph", {})
        followers = None
        for k, v in kg.items():
            if "follower" in k.lower() and isinstance(v, str):
                import re
                m = re.search(r'[\d.,]+', v.replace('.', '').replace(',', ''))
                if m:
                    followers = int(m.group())
                    break
        
        # Cerca negli organic results
        fb_snippet = ""
        fb_url = page_url
        for r in data.get("organic_results", []):
            if "facebook.com" in r.get("link", ""):
                fb_snippet = r.get("snippet", "")
                fb_url = r.get("link", page_url)
                # Prova a estrarre follower dallo snippet
                if not followers:
                    import re
                    m = re.search(r'([\d.,]+)\s*(follower|seguaci|fan|mi piace)', fb_snippet, re.IGNORECASE)
                    if m:
                        followers = int(m.group(1).replace('.','').replace(',',''))
                break
        
        if kg or fb_snippet:
            logger.info(f"[APIFY] Facebook SerpAPI OK: followers={followers}, snippet={fb_snippet[:80]}")
            return {
                "source": "facebook",
                "found": True,
                "scraped_via": "serpapi_fallback",
                "name": kg.get("title") or company_name,
                "url": fb_url,
                "followers": followers,
                "likes": followers,
                "description": kg.get("description") or fb_snippet,
                "avg_engagement_per_post": None,
                "recent_posts": []
            }
    except Exception as e:
        logger.warning(f"[APIFY] SerpAPI Facebook fallback errore: {e}")

    return {
        "source": "facebook",
        "found": False,
        "not_scraped": True,
        "reason": "profilo personale — nessun dato disponibile"
    }



def scrape_facebook(page_url: str = "", company_name: str = "") -> dict[str, Any]:
    """
    Scraping Facebook Page + Posts (Dual-Call).
    Actors: facebook-pages-scraper (4Hv5RhChiaDk6iwad) + facebook-posts-scraper (KoJrdxJCTtpon81KY)
    """
    if not page_url:
        if company_name:
            logger.info(f"[APIFY] Facebook URL mancante, provo fallback per '{company_name}'")
            return _scrape_facebook_serp_fallback(company_name, "")
        return {"source": "facebook", "found": False, "error": "URL pagina mancante"}

    # Fix: Profili personali (profile.php?id=...) non supportati da Apify page-scraper
    if "profile.php" in page_url or "/people/" in page_url:
        logger.warning(f"[APIFY] Facebook URL è un profilo personale, non una pagina: {page_url}")
        return _scrape_facebook_serp_fallback(company_name, page_url)

    logger.info(f"[APIFY] Facebook Dual-Call per: {page_url}")

    # Chiamata 1: Dati Pagina
    run_input_page = {"startUrls": [{"url": page_url}]}
    page_results = _run_actor("4Hv5RhChiaDk6iwad", run_input_page)

    # Chiamata 2: Post Recenti
    run_input_posts = {
        "startUrls": [{"url": page_url}],
        "resultsLimit": 10,
    }
    posts_results = _run_actor("KoJrdxJCTtpon81KY", run_input_posts)

    # Fallback per profili personali o errori — se page_results è vuoto, usa SerpAPI
    if not page_results:
        logger.warning(f"[APIFY] facebook-pages-scraper returned 0 results for {page_url}. Uso SerpAPI fallback.")
        return _scrape_facebook_serp_fallback(company_name, page_url)
    
    page = page_results[0]

    
    # Analisi post (dalla Chiamata 2)
    posts = []
    total_eng = 0
    for p in posts_results[:10]:
        # reactionsCount o likes + comments + shares
        likes = p.get("likes", 0) or 0
        comments = p.get("comments", 0) or 0
        shares = p.get("shares", 0) or 0
        eng = likes + comments + shares
        total_eng += eng
        posts.append({
            "text": (p.get("text") or "")[:150],
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "date": p.get("time"),
        })

    num_posts = max(len(posts), 1)
    avg_engagement = round(total_eng / num_posts, 2)

    return {
        "source": "facebook",
        "found": True,
        "name": page.get("name") or page.get("pageName", ""),
        "likes": page.get("likes") or page.get("likesCount", 0),
        "followers": page.get("followers") or page.get("followersCount", 0),
        "rating": page.get("rating"),
        "address": page.get("address"),
        "phone": page.get("phone"),
        "email": page.get("email"),
        "website": page.get("website"),
        "categories": page.get("categories", []),
        "avg_engagement_per_post": avg_engagement,
        "recent_posts": posts,
    }


def scrape_linkedin(company_url: str = "", company_name: str = "") -> dict[str, Any]:
    """
    Scraping LinkedIn Company Page via Apify.
    Actor: anchor/linkedin-company-scraper (heCRoeHip2BHXGCLU)
    
    Restituisce: descrizione azienda, settore, dipendenti, specialità, post recenti.
    """
    if not company_url and not company_name:
        return {"source": "linkedin", "found": False, "error": "Nessun URL o nome azienda"}

    if company_url:
        # Normalizza URL LinkedIn
        url = company_url.strip().rstrip("/")
        if "linkedin.com" not in url:
            url = f"https://www.linkedin.com/company/{url}"
        logger.info(f"[APIFY] LinkedIn scraping: {url}")
        run_input = {
            "startUrls": [{"url": url}],
            "maxItems": 1,
        }
    else:
        logger.info(f"[APIFY] LinkedIn search: '{company_name}'")
        run_input = {
            "search": company_name,
            "maxItems": 3,
        }

    results = _run_actor("Vb6LZkh4EqRlR0Ka9", run_input)

    if not results:
        return {"source": "linkedin", "found": False, "error": "Profilo aziendale non trovato"}

    company = results[0]

    # Estrai post recenti se disponibili
    recent_posts = []
    for post in company.get("posts", company.get("updates", []))[:10]:
        text = post.get("text", post.get("commentary", ""))
        likes = post.get("likesCount", post.get("numLikes", 0)) or 0
        comments = post.get("commentsCount", post.get("numComments", 0)) or 0
        recent_posts.append({
            "text": (text or "")[:200],
            "likes": likes,
            "comments": comments,
            "date": post.get("postedDate", post.get("date", "")),
        })

    total_likes = sum(p["likes"] for p in recent_posts)
    total_comments = sum(p["comments"] for p in recent_posts)
    num_posts = max(len(recent_posts), 1)

    return {
        "source": "linkedin",
        "found": True,
        "name": company.get("name", company.get("companyName", "")),
        "description": company.get("description", company.get("tagline", "")),
        "industry": company.get("industry", ""),
        "company_size": company.get("staffCount", company.get("employeeCount", "")),
        "company_type": company.get("type", company.get("companyType", "")),
        "headquarters": company.get("headquarter", company.get("locations", "")),
        "website": company.get("website", company.get("companyUrl", "")),
        "specialities": company.get("specialities", []),
        "followers": company.get("followerCount", company.get("followersCount", 0)),
        "founded": company.get("foundedOn", company.get("founded", "")),
        "logo_url": company.get("logo", company.get("logoUrl", "")),
        "linkedin_url": company.get("url", company.get("linkedinUrl", "")),
        "posts_count": len(recent_posts),
        "avg_likes_per_post": round(total_likes / num_posts),
        "avg_comments_per_post": round(total_comments / num_posts),
        "recent_posts": recent_posts,
    }


def run_apify_scraping(
    company_name: str,
    city: str = "",
    website: str = "",
    social_links: dict = None,
    sector: str = "",
) -> dict[str, Any]:
    """
    Funzione principale: esegue scraping Apify completo per una PMI.
    """
    if social_links is None:
        social_links = {}

    # === AUTO-DISCOVERY SOCIAL VIA SERPAPI ===
    if not social_links.get("facebook") or not social_links.get("instagram"):
        try:
            import os as _os
            _serpapi_key = _os.getenv("SERPAPI_KEY", "") or _os.getenv("SERP_API_KEY", "")
            if _serpapi_key:
                _q = f"{company_name} {city}".strip()
                _resp = requests.get("https://serpapi.com/search.json", params={"q": _q, "hl": "it", "gl": "it", "num": 10, "api_key": _serpapi_key}, timeout=15)
                for _r in _resp.json().get("organic_results", []):
                    _link = _r.get("link", "")
                    if "facebook.com" in _link and not social_links.get("facebook") and "/posts/" not in _link and "/photos/" not in _link:
                        social_links["facebook"] = _link
                        logger.info(f"[APIFY DISCOVERY] Facebook: {_link}")
                    elif "instagram.com" in _link and not social_links.get("instagram"):
                        _clean = _link.split("?")[0].rstrip("/")
                        _path = _clean.split("instagram.com/")[-1] if "instagram.com/" in _clean else ""
                        if _path and "/" not in _path and len(_path) > 2 and _path not in ("explore","accounts","directory","tags"):
                            social_links["instagram"] = _path
                            logger.info(f"[APIFY DISCOVERY] Instagram: @{_path}")
        except Exception as _e:
            logger.warning(f"[APIFY DISCOVERY] Errore: {_e}")

    logger.info(f"[APIFY] === Inizio scraping completo per {company_name} ({city}) — Settore: {sector} ===")

    result = {
        "company_name": company_name,
        "city": city,
        "sector": sector,
        "google_maps": {},
        "instagram": {},
        "facebook": {},
        "linkedin": {},
        "errors": [],
    }

    # 1. Google Maps — controllato da env var (default: disabilitato per timeout)
    enable_gmaps = os.getenv("ENABLE_GOOGLE_MAPS_APIFY", "false").lower() == "true"
    if enable_gmaps:
        try:
            result["google_maps"] = scrape_google_maps(company_name, city, sector)
            logger.info(f"[APIFY] Google Maps: found={result['google_maps'].get('found')}")
        except Exception as e:
            logger.error(f"[APIFY] Errore Google Maps: {e}")
            result["errors"].append(f"Google Maps: {str(e)}")
            result["google_maps"] = {"source": "google_maps", "found": False, "error": str(e)}
    else:
        logger.info("[APIFY] Google Maps disabilitato (ENABLE_GOOGLE_MAPS_APIFY=false) — dati da SerpAPI")
        result["google_maps"] = {"found": False, "source": "google_maps", "note": "Disabled - set ENABLE_GOOGLE_MAPS_APIFY=true to enable"}

    # 2. Instagram — se ha il link
    ig_link = social_links.get("instagram", "")
    if ig_link:
        try:
            result["instagram"] = scrape_instagram(username=ig_link, company_name=company_name)
        except Exception as e:
            logger.error(f"[APIFY] Errore Instagram: {e}")
            result["errors"].append(f"Instagram: {str(e)}")
            result["instagram"] = {"source": "instagram", "found": False, "error": str(e)}
    else:
        # Prova a cercare per nome azienda
        try:
            clean_name = company_name.split(" S.")[0].split(" s.")[0].split(" SRL")[0].split(" srl")[0].strip()
            result["instagram"] = scrape_instagram(company_name=clean_name)
        except Exception as e:
            result["instagram"] = {"source": "instagram", "found": False, "error": str(e)}

    # 3. Facebook — se ha il link o cerca per nome
    fb_link = social_links.get("facebook", "")
    try:
        result["facebook"] = scrape_facebook(page_url=fb_link, company_name=company_name)
    except Exception as e:
        logger.error(f"[APIFY] Errore Facebook: {e}")
        result["errors"].append(f"Facebook: {str(e)}")
        result["facebook"] = {"source": "facebook", "found": False, "error": str(e)}

    # 4. LinkedIn — sempre (fondamentale per analisi aziendale)
    li_link = social_links.get("linkedin", "")
    try:
        result["linkedin"] = scrape_linkedin(company_url=li_link, company_name=company_name)
    except Exception as e:
        logger.error(f"[APIFY] Errore LinkedIn: {e}")
        result["errors"].append(f"LinkedIn: {str(e)}")
        result["linkedin"] = {"source": "linkedin", "found": False, "error": str(e)}

    found_count = sum(1 for k in ["google_maps", "instagram", "facebook", "linkedin"] if result[k].get("found"))
    logger.info(f"[APIFY] === Scraping completato: {found_count}/4 fonti trovate ===")

    return result
