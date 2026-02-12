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


def scrape_google_maps(company_name: str, city: str, sector: str = "") -> dict[str, Any]:
    """
    Scraping Google Maps via Apify per dati local business.
    Actor: compass/crawler-google-places (nwua9Gu5YrADL7ZDj)
    
    Restituisce: rating, recensioni, orari, indirizzo, foto, categorie e ultime recensioni testuali.
    """
    search_query = f"{company_name} {city}"
    if sector:
        search_query = f"{company_name} {sector} {city}"

    logger.info(f"[APIFY] Google Maps scraping: '{search_query}'")

    run_input = {
        "searchStringsArray": [search_query],
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
        return {"source": "google_maps", "found": False, "error": "Nessun risultato"}

    # Trova il match migliore (primo risultato)
    place = results[0]

    # Estrai ultime 5 recensioni testuali
    reviews_summary = []
    for review in place.get("reviews", [])[:5]:
        reviews_summary.append({
            "text": review.get("text", "") or "",
            "stars": review.get("stars"),
            "publishedAtDate": review.get("publishedAtDate"),
            "publishAt": review.get("publishAt"),
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
        "address": place.get("address", ""),
        "phone": place.get("phone", ""),
        "website": place.get("website", ""),
        "rating": place.get("totalScore"),
        "total_reviews": place.get("reviewsCount", 0),
        "category": place.get("categoryName", ""),
        "categories": place.get("categories", []),
        "opening_hours": place.get("openingHours", []),
        "photos": photos,
        "reviews": reviews_summary,
        "place_id": place.get("placeId", ""),
        "temporarily_closed": place.get("temporarilyClosed", False),
        "permanently_closed": place.get("permanentlyClosed", False),
    }


def scrape_instagram(username: str = "", company_name: str = "", website: str = "") -> dict[str, Any]:
    """
    Scraping Instagram via Apify.
    Actor: apify/instagram-scraper (shu8hvrXbJbY3Eb9W)
    """
    if not username and not company_name:
        return {"source": "instagram", "found": False, "error": "Nessun username o nome azienda"}

    # Fix: Uso di directUrls come richiesto
    if username:
        username = username.strip().lstrip("@").split("/")[-1]
        url = f"https://www.instagram.com/{username}/"
        logger.info(f"[APIFY] Instagram scraping: {url}")

        run_input = {
            "directUrls": [url],
            "resultsType": "posts",
            "resultsLimit": 12,
        }
    else:
        # Cerca per nome
        logger.info(f"[APIFY] Instagram search: '{company_name}'")
        run_input = {
            "search": company_name,
            "resultsLimit": 3,
            "searchType": "user",
        }

    results = _run_actor("shu8hvrXbJbY3Eb9W", run_input)

    if not results:
        return {"source": "instagram", "found": False, "error": "Profilo non trovato"}

    # Il profilo è nel primo risultato (o nei metadati del post se resultsType=posts)
    # Spesso con resultsType=posts, i dati del profilo sono duplicati in ogni post under 'owner' 
    # o l'actor ritorna un oggetto profilo se configurato.
    # Assumiamo la struttura standard di instagram-scraper
    profile = results[0]
    
    # Se l'actor ritorna post, i dati profilo sono spesso in 'owner' o 'user'
    user_data = profile.get("owner") or profile.get("user") or profile

    # Analisi post recenti per engagement
    recent_posts = []
    total_likes = 0
    total_comments = 0
    posts_analyzed = 0

    # L'actor ritorna una lista di post
    for post in results[:12]:
        likes = post.get("likesCount", 0) or 0
        comments = post.get("commentsCount", 0) or 0
        total_likes += likes
        total_comments += comments
        posts_analyzed += 1
        recent_posts.append({
            "likes": likes,
            "comments": comments,
            "timestamp": post.get("timestamp"),
            "caption": (post.get("caption") or "")[:150],
            "url": post.get("url"),
        })

    followers = user_data.get("followersCount", 0) or 0
    avg_likes = total_likes / max(posts_analyzed, 1)
    avg_comments = total_comments / max(posts_analyzed, 1)
    engagement_rate = round(((avg_likes + avg_comments) / followers) * 100, 2) if followers > 0 else 0

    return {
        "source": "instagram",
        "found": True,
        "username": user_data.get("username", ""),
        "full_name": user_data.get("fullName", ""),
        "biography": user_data.get("biography", ""),
        "followers": followers,
        "following": user_data.get("followsCount", 0),
        "posts_count": user_data.get("postsCount", 0),
        "is_verified": user_data.get("verified", False),
        "is_business": user_data.get("isBusinessAccount", False),
        "external_url": user_data.get("externalUrl", ""),
        "profile_pic_url": user_data.get("profilePicUrl", ""),
        "engagement_rate": engagement_rate,
        "avg_likes_per_post": round(avg_likes),
        "avg_comments_per_post": round(avg_comments),
        "recent_posts": recent_posts,
    }


def scrape_facebook(page_url: str = "", company_name: str = "") -> dict[str, Any]:
    """
    Scraping Facebook Page via Apify.
    Actor: apify/facebook-pages-scraper (4Hv5RhChiaDk6iwad)
    """
    if not page_url and not company_name:
        return {"source": "facebook", "found": False, "error": "Nessun URL o nome"}

    search_term = page_url if page_url else company_name
    logger.info(f"[APIFY] Facebook scraping: '{search_term}'")

    if page_url:
        run_input = {
            "startUrls": [{"url": page_url}],
            "maxPosts": 10,
        }
    else:
        run_input = {
            "search": company_name,
            "maxResults": 1,
            "maxPosts": 10,
        }

    results = _run_actor("4Hv5RhChiaDk6iwad", run_input)

    if not results:
        return {"source": "facebook", "found": False, "error": "Pagina non trovata"}

    page = results[0]
    
    # Estrai dati PAGINA (Fix 2)
    likes = page.get("likes") or page.get("likesCount") or 0
    followers = page.get("followers") or page.get("followersCount") or 0
    rating = page.get("rating")
    address = page.get("address")
    phone = page.get("phone")
    email = page.get("email")
    website = page.get("website")
    categories = page.get("categories", [])

    # Analisi post (se presenti nel risultato dell'actor)
    posts = []
    total_likes = 0
    total_comments = 0
    total_shares = 0
    
    # Alcuni actor ritornano i post dentro l'oggetto pagina, altri come oggetti separati
    raw_posts = page.get("latestPosts", []) or results
    if raw_posts and isinstance(raw_posts[0], dict) and "text" in raw_posts[0]:
        for post in raw_posts[:10]:
            l = post.get("likes", 0) or 0
            c = post.get("comments", 0) or 0
            s = post.get("shares", 0) or 0
            total_likes += l
            total_comments += c
            total_shares += s
            posts.append({
                "text": (post.get("text") or "")[:150],
                "likes": l,
                "comments": c,
                "shares": s,
                "date": post.get("time"),
            })

    num_posts = max(len(posts), 1)
    avg_engagement = round((total_likes + total_comments + total_shares) / num_posts, 2)

    return {
        "source": "facebook",
        "found": True,
        "name": page.get("name") or page.get("pageName", ""),
        "likes": likes,
        "followers": followers,
        "rating": rating,
        "address": address,
        "phone": phone,
        "email": email,
        "website": website,
        "categories": categories,
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
    city: str,
    sector: str = "",
    website: str = "",
    social_links: dict = None,
) -> dict[str, Any]:
    """
    Funzione principale: esegue scraping Apify completo per una PMI.
    
    Chiama Google Maps sempre, poi i social solo se ha i link.
    
    Args:
        company_name: Nome dell'azienda
        city: Città
        sector: Settore di attività
        website: URL del sito web
        social_links: Dict con chiavi "instagram", "facebook", "tiktok" (URL o username)
    
    Returns:
        Dict con tutti i dati raccolti da Apify
    """
    if social_links is None:
        social_links = {}

    logger.info(f"[APIFY] === Inizio scraping completo per {company_name} ({city}) ===")

    result = {
        "company_name": company_name,
        "city": city,
        "google_maps": {},
        "instagram": {},
        "facebook": {},
        "linkedin": {},
        "errors": [],
    }

    # 1. Google Maps — SEMPRE (Fix 3)
    try:
        result["google_maps"] = scrape_google_maps(company_name, city, sector)
    except Exception as e:
        logger.error(f"[APIFY] Errore Google Maps: {e}")
        result["errors"].append(f"Google Maps: {str(e)}")
        result["google_maps"] = {"source": "google_maps", "found": False, "error": str(e)}

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
