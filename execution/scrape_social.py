"""
DigIdentity Engine — Social Media Scraper (sostituto Apify)
Raccoglie: follower, engagement rate, frequenza post, bio
Piattaforme: Instagram, Facebook (pagine pubbliche), LinkedIn (base)
"""

import logging
import time
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

HEADERS_MOBILE = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 "
        "Mobile/15E148 Safari/604.1"
    ),
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

HEADERS_DESKTOP = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "it-IT,it;q=0.9",
}


# ─────────────────────────────────────────────
# INSTAGRAM — via Instaloader (nessun login)
# ─────────────────────────────────────────────

def scrape_instagram(instagram_url: str) -> dict:
    """
    Scrape dati profilo Instagram pubblico.
    Usa Instaloader senza login (solo profili pubblici).
    """
    result = {
        "platform": "instagram",
        "found": False,
        "url": instagram_url,
        "followers": None,
        "following": None,
        "post_count": None,
        "bio": None,
        "engagement_rate": None,
        "avg_likes": None,
        "avg_comments": None,
        "posting_frequency_per_week": None,
        "last_post_date": None,
        "error": None,
    }

    try:
        import instaloader
        L = instaloader.Instaloader(
            quiet=True,
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
        )

        username = _extract_instagram_username(instagram_url)
        if not username:
            result["error"] = "Username non estratto dall'URL"
            return result

        logger.info(f"[INSTAGRAM] Analizzando @{username}...")

        profile = instaloader.Profile.from_username(L.context, username)

        result["found"] = True
        result["followers"] = profile.followers
        result["following"] = profile.followees
        result["post_count"] = profile.mediacount
        result["bio"] = profile.biography

        # Analisi ultimi 12 post per engagement e frequenza
        likes_list = []
        comments_list = []
        dates_list = []
        post_limit = 12

        for post in profile.get_posts():
            likes_list.append(post.likes)
            comments_list.append(post.comments)
            dates_list.append(post.date_utc)
            if len(likes_list) >= post_limit:
                break
            time.sleep(0.8)  # Rate limiting gentile

        if likes_list and profile.followers > 0:
            avg_likes = sum(likes_list) / len(likes_list)
            avg_comments = sum(comments_list) / len(comments_list)
            result["avg_likes"] = round(avg_likes)
            result["avg_comments"] = round(avg_comments)
            result["engagement_rate"] = round(
                (avg_likes + avg_comments) / profile.followers * 100, 2
            )

        if len(dates_list) >= 2:
            oldest = min(dates_list)
            newest = max(dates_list)
            delta_days = max((newest - oldest).days, 1)
            weeks = delta_days / 7
            result["posting_frequency_per_week"] = round(len(dates_list) / weeks, 1)
            result["last_post_date"] = newest.strftime("%Y-%m-%d")

        logger.info(
            f"[INSTAGRAM] @{username} — "
            f"Follower: {result['followers']:,} | "
            f"ER: {result['engagement_rate']}% | "
            f"Freq: {result['posting_frequency_per_week']} post/sett"
        )

    except Exception as e:
        result["error"] = str(e)
        logger.warning(f"[INSTAGRAM] Errore per {instagram_url}: {e}")

    return result


def _extract_instagram_username(url: str) -> str | None:
    """Estrae lo username dall'URL Instagram."""
    if url.startswith("@"):
        return url[1:].strip("/")
    if "instagram.com" in url:
        parts = urlparse(url).path.strip("/").split("/")
        return parts[0] if parts and parts[0] else None
    if re.match(r'^[a-zA-Z0-9._]+$', url.strip()):
        return url.strip()
    return None


# ─────────────────────────────────────────────
# FACEBOOK — via scraping HTML pagine pubbliche
# ─────────────────────────────────────────────

def scrape_facebook(facebook_url: str) -> dict:
    """
    Scrape dati base da pagina Facebook pubblica.
    """
    result = {
        "platform": "facebook",
        "found": False,
        "url": facebook_url,
        "followers": None,
        "likes": None,
        "bio": None,
        "engagement_rate": None,
        "posting_frequency_per_week": None,
        "error": None,
    }

    try:
        mobile_url = facebook_url.replace(
            "www.facebook.com", "m.facebook.com"
        ).replace("facebook.com", "m.facebook.com")

        resp = requests.get(
            mobile_url,
            headers=HEADERS_MOBILE,
            timeout=15,
            allow_redirects=True,
        )

        if resp.status_code != 200:
            result["error"] = f"HTTP {resp.status_code}"
            return result

        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)

        result["found"] = True

        follower_patterns = [
            r'([\d.,]+)\s*(?:persone seguono|followers?|seguaci)',
            r'([\d.,]+)\s*(?:Mi piace|like)',
            r'([\d]+[.,]?[\d]*[KMk]?)\s*followers?',
        ]
        for pattern in follower_patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                raw = m.group(1).replace(".", "").replace(",", "")
                if "K" in raw.upper():
                    result["followers"] = int(float(raw.upper().replace("K", "")) * 1000)
                elif "M" in raw.upper():
                    result["followers"] = int(float(raw.upper().replace("M", "")) * 1_000_000)
                else:
                    try:
                        result["followers"] = int(raw)
                    except ValueError:
                        pass
                if result["followers"]:
                    break

        desc_tag = soup.find("meta", attrs={"name": "description"})
        if desc_tag and desc_tag.get("content"):
            result["bio"] = desc_tag["content"][:300]

        logger.info(f"[FACEBOOK] {facebook_url} — Follower: {result['followers']}")

    except Exception as e:
        result["error"] = str(e)
        logger.warning(f"[FACEBOOK] Errore per {facebook_url}: {e}")

    return result


# ─────────────────────────────────────────────
# RAPIDAPI — Fallback per Facebook/TikTok
# Gratuito: 100 req/mese sul piano free
# ─────────────────────────────────────────────

def scrape_via_rapidapi(platform: str, url_or_username: str, rapidapi_key: str) -> dict:
    """
    Fallback via RapidAPI (facebook-tiktok-instagram-scraper).
    Piano FREE: 100 req/mese.
    Chiave gratis su: rapidapi.com/andryerics/api/facebook-tiktok-instagram-scraper
    """
    result = {
        "platform": platform,
        "found": False,
        "source": "rapidapi",
        "followers": None,
        "engagement_rate": None,
        "error": None,
    }

    try:
        endpoint_map = {
            "facebook": "https://facebook-tiktok-instagram-scraper.p.rapidapi.com/facebook/page",
            "instagram": "https://facebook-tiktok-instagram-scraper.p.rapidapi.com/instagram/profile",
            "tiktok": "https://facebook-tiktok-instagram-scraper.p.rapidapi.com/tiktok/profile",
        }

        endpoint = endpoint_map.get(platform)
        if not endpoint:
            result["error"] = f"Piattaforma non supportata: {platform}"
            return result

        resp = requests.get(
            endpoint,
            headers={
                "X-RapidAPI-Key": rapidapi_key,
                "X-RapidAPI-Host": "facebook-tiktok-instagram-scraper.p.rapidapi.com",
            },
            params={"url": url_or_username},
            timeout=20,
        )

        data = resp.json()
        if data:
            result["found"] = True
            result["followers"] = data.get("followers") or data.get("follower_count")
            result["likes"] = data.get("likes")
            result["bio"] = data.get("bio") or data.get("description")
            result["post_count"] = data.get("post_count") or data.get("media_count")
            result["raw"] = data

        logger.info(f"[RAPIDAPI] {platform} — Follower: {result['followers']}")

    except Exception as e:
        result["error"] = str(e)
        logger.warning(f"[RAPIDAPI] Errore {platform}: {e}")

    return result


# ─────────────────────────────────────────────
# ENTRY POINT — drop-in replacement di run_apify_scraping()
# ─────────────────────────────────────────────

def run_social_scraping(
    company_name: str,
    city: str,
    website: str,
    social_links: dict,
    sector: str = "",
    rapidapi_key: str = None,
) -> dict:
    """
    Sostituto drop-in di run_apify_scraping().
    Stessa firma, stesso output strutturato.
    """
    results = {
        "source": "scrape_social_noapify",
        "instagram": {},
        "facebook": {},
        "linkedin": {},
        "tiktok": {},
        "google_maps": {},
        "errors": [],
    }

    # ── INSTAGRAM ──────────────────────────────
    ig_url = social_links.get("instagram")
    if ig_url:
        logger.info(f"[SOCIAL] Avvio scraping Instagram: {ig_url}")
        ig_data = scrape_instagram(ig_url)

        if not ig_data.get("found") and rapidapi_key:
            logger.info("[SOCIAL] Instaloader fallito — tentativo RapidAPI Instagram")
            ig_data = scrape_via_rapidapi("instagram", ig_url, rapidapi_key)

        results["instagram"] = ig_data
        if ig_data.get("error"):
            results["errors"].append(f"Instagram: {ig_data['error']}")

    # ── FACEBOOK ───────────────────────────────
    fb_url = social_links.get("facebook")
    if fb_url:
        logger.info(f"[SOCIAL] Avvio scraping Facebook: {fb_url}")
        fb_data = scrape_facebook(fb_url)

        if not fb_data.get("followers") and rapidapi_key:
            logger.info("[SOCIAL] Facebook HTML fallito — tentativo RapidAPI")
            fb_data = scrape_via_rapidapi("facebook", fb_url, rapidapi_key)

        results["facebook"] = fb_data
        if fb_data.get("error"):
            results["errors"].append(f"Facebook: {fb_data['error']}")

    # ── TIKTOK ─────────────────────────────────
    tt_url = social_links.get("tiktok")
    if tt_url and rapidapi_key:
        logger.info(f"[SOCIAL] Avvio scraping TikTok: {tt_url}")
        tt_data = scrape_via_rapidapi("tiktok", tt_url, rapidapi_key)
        results["tiktok"] = tt_data

    logger.info(
        f"[SOCIAL] Scraping completato per {company_name} — "
        f"IG: {'✅' if results['instagram'].get('found') else '❌'} | "
        f"FB: {'✅' if results['facebook'].get('found') else '❌'}"
    )

    return results
