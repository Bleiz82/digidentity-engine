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
ACTOR_TIMEOUT = 120
POLL_INTERVAL = 5


def _run_actor(actor_id: str, run_input: dict, timeout: int = ACTOR_TIMEOUT) -> list[dict]:
    """
    Lancia un Actor Apify e attende i risultati.
    
    Args:
        actor_id: ID dell'actor (es. "nwua9Gu5YrADL7ZDj")
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
    
    Restituisce: rating, recensioni, orari, indirizzo, foto, categorie.
    """
    search_query = f"{company_name} {city}"
    if sector:
        search_query = f"{company_name} {sector} {city}"

    logger.info(f"[APIFY] Google Maps scraping: '{search_query}'")

    run_input = {
        "searchStringsArray": [search_query],
        "maxCrawledPlacesPerSearch": 3,
        "language": "it",
        "countryCode": "it",
        "includeHistogram": False,
        "includeOpeningHours": True,
        "includePeopleAlsoSearch": False,
        "maxReviews": 20,
        "reviewsSort": "newest",
        "scrapeReviewerName": False,
    }

    results = _run_actor("nwua9Gu5YrADL7ZDj", run_input)

    if not results:
        return {"source": "google_maps", "found": False, "error": "Nessun risultato"}

    # Trova il match migliore (primo risultato di solito è il più rilevante)
    place = results[0]

    # Estrai dati rilevanti
    reviews_summary = []
    for review in place.get("reviews", [])[:10]:
        reviews_summary.append({
            "text": (review.get("text") or "")[:200],
            "stars": review.get("stars"),
            "publishedAtDate": review.get("publishedAtDate"),
        })

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
        "photos_count": place.get("imageCount", 0),
        "latitude": place.get("location", {}).get("lat"),
        "longitude": place.get("location", {}).get("lng"),
        "place_id": place.get("placeId", ""),
        "reviews_sample": reviews_summary,
        "price_level": place.get("price", ""),
        "temporarily_closed": place.get("temporarilyClosed", False),
        "permanently_closed": place.get("permanentlyClosed", False),
    }


def scrape_instagram(username: str = "", company_name: str = "", website: str = "") -> dict[str, Any]:
    """
    Scraping Instagram via Apify.
    Actor: apify/instagram-profile-scraper (dSCLg0C3YEZ83HzYX)
    
    Se non ha lo username, cerca per nome azienda.
    """
    if not username and not company_name:
        return {"source": "instagram", "found": False, "error": "Nessun username o nome azienda"}

    # Se abbiamo lo username diretto
    if username:
        username = username.strip().lstrip("@").split("/")[-1]
        logger.info(f"[APIFY] Instagram scraping: @{username}")

        run_input = {
            "usernames": [username],
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

    results = _run_actor("dSCLg0C3YEZ83HzYX", run_input)

    if not results:
        return {"source": "instagram", "found": False, "error": "Profilo non trovato"}

    profile = results[0]

    # Analisi post recenti per engagement
    recent_posts = []
    total_likes = 0
    total_comments = 0
    posts_analyzed = 0

    for post in profile.get("latestPosts", [])[:12]:
        likes = post.get("likesCount", 0) or 0
        comments = post.get("commentsCount", 0) or 0
        total_likes += likes
        total_comments += comments
        posts_analyzed += 1
        recent_posts.append({
            "type": post.get("type", ""),
            "likes": likes,
            "comments": comments,
            "timestamp": post.get("timestamp", ""),
            "caption": (post.get("caption") or "")[:150],
        })

    followers = profile.get("followersCount", 0) or 1
    avg_likes = total_likes / max(posts_analyzed, 1)
    avg_comments = total_comments / max(posts_analyzed, 1)
    engagement_rate = round(((avg_likes + avg_comments) / followers) * 100, 2) if followers > 0 else 0

    return {
        "source": "instagram",
        "found": True,
        "username": profile.get("username", ""),
        "full_name": profile.get("fullName", ""),
        "biography": profile.get("biography", ""),
        "followers": profile.get("followersCount", 0),
        "following": profile.get("followsCount", 0),
        "posts_count": profile.get("postsCount", 0),
        "is_verified": profile.get("verified", False),
        "is_business": profile.get("isBusinessAccount", False),
        "business_category": profile.get("businessCategoryName", ""),
        "external_url": profile.get("externalUrl", ""),
        "profile_pic_url": profile.get("profilePicUrl", ""),
        "engagement_rate": engagement_rate,
        "avg_likes_per_post": round(avg_likes),
        "avg_comments_per_post": round(avg_comments),
        "recent_posts": recent_posts,
    }


def scrape_facebook(page_url: str = "", company_name: str = "") -> dict[str, Any]:
    """
    Scraping Facebook Page via Apify.
    Actor: apify/facebook-posts-scraper (KoJrdxJCTtpon81KY)
    """
    if not page_url and not company_name:
        return {"source": "facebook", "found": False, "error": "Nessun URL o nome"}

    search_term = page_url if page_url else company_name
    logger.info(f"[APIFY] Facebook scraping: '{search_term}'")

    if page_url:
        run_input = {
            "startUrls": [{"url": page_url}],
            "resultsLimit": 15,
        }
    else:
        run_input = {
            "searchTerms": [company_name],
            "resultsLimit": 15,
        }

    results = _run_actor("KoJrdxJCTtpon81KY", run_input)

    if not results:
        return {"source": "facebook", "found": False, "error": "Pagina non trovata"}

    # Analizza i post
    posts = []
    total_likes = 0
    total_comments = 0
    total_shares = 0

    for post in results[:15]:
        likes = post.get("likes", 0) or 0
        comments = post.get("comments", 0) or 0
        shares = post.get("shares", 0) or 0
        total_likes += likes
        total_comments += comments
        total_shares += shares

        posts.append({
            "text": (post.get("text") or "")[:200],
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "date": post.get("time", ""),
            "type": post.get("type", ""),
        })

    num_posts = max(len(posts), 1)

    return {
        "source": "facebook",
        "found": True,
        "page_name": results[0].get("pageName", "") if results else "",
        "posts_analyzed": len(posts),
        "avg_likes": round(total_likes / num_posts),
        "avg_comments": round(total_comments / num_posts),
        "avg_shares": round(total_shares / num_posts),
        "total_engagement": total_likes + total_comments + total_shares,
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

    results = _run_actor("heCRoeHip2BHXGCLU", run_input)

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

    # 1. Google Maps — SEMPRE
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
            result["instagram"] = scrape_instagram(company_name=company_name)
        except Exception as e:
            result["instagram"] = {"source": "instagram", "found": False, "error": str(e)}

    # 3. Facebook — se ha il link
    fb_link = social_links.get("facebook", "")
    if fb_link:
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
