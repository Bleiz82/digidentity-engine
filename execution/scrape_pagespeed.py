"""
DigIdentity Engine — Google PageSpeed Insights Scraper
Analizza performance, accessibility, best practices e SEO di un sito web.
"""

import httpx
from typing import Dict, Any, Optional
from app.config import get_settings


async def scrape_pagespeed(url: str) -> Dict[str, Any]:
    """
    Esegue analisi PageSpeed Insights su un URL.
    
    Args:
        url: URL del sito web da analizzare
        
    Returns:
        dict: Risultati analisi con scores e Core Web Vitals
        
    Raises:
        Exception: Se errore nella chiamata API
    """
    settings = get_settings()
    
    if not url:
        return {
            "success": False,
            "error": "URL non fornito",
            "data": None
        }
    
    print(f"[PAGE-SPEED] Analisi PageSpeed per: {url}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Analisi desktop
            print(f"[INFO] Analisi desktop...")
            desktop_response = await client.get(
                "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
                params={
                    "url": url,
                    "key": settings.google_pagespeed_api_key,
                    "strategy": "desktop",
                    "category": ["performance", "accessibility", "best-practices", "seo"]
                }
            )
            desktop_response.raise_for_status()
            desktop_data = desktop_response.json()
            
            # Analisi mobile
            print(f"[INFO] Analisi mobile...")
            mobile_response = await client.get(
                "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
                params={
                    "url": url,
                    "key": settings.google_pagespeed_api_key,
                    "strategy": "mobile",
                    "category": ["performance", "accessibility", "best-practices", "seo"]
                }
            )
            mobile_response.raise_for_status()
            mobile_data = mobile_response.json()
            
            # Estrai scores
            desktop_scores = desktop_data.get("lighthouseResult", {}).get("categories", {})
            mobile_scores = mobile_data.get("lighthouseResult", {}).get("categories", {})
            
            # Estrai Core Web Vitals (mobile)
            mobile_audits = mobile_data.get("lighthouseResult", {}).get("audits", {})
            
            result = {
                "success": True,
                "url": url,
                "desktop": {
                    "performance": int(desktop_scores.get("performance", {}).get("score", 0) * 100),
                    "accessibility": int(desktop_scores.get("accessibility", {}).get("score", 0) * 100),
                    "best_practices": int(desktop_scores.get("best-practices", {}).get("score", 0) * 100),
                    "seo": int(desktop_scores.get("seo", {}).get("score", 0) * 100),
                },
                "mobile": {
                    "performance": int(mobile_scores.get("performance", {}).get("score", 0) * 100),
                    "accessibility": int(mobile_scores.get("accessibility", {}).get("score", 0) * 100),
                    "best_practices": int(mobile_scores.get("best-practices", {}).get("score", 0) * 100),
                    "seo": int(mobile_scores.get("seo", {}).get("score", 0) * 100),
                },
                "core_web_vitals": {
                    "lcp": mobile_audits.get("largest-contentful-paint", {}).get("displayValue", "N/A"),
                    "fid": mobile_audits.get("max-potential-fid", {}).get("displayValue", "N/A"),
                    "cls": mobile_audits.get("cumulative-layout-shift", {}).get("displayValue", "N/A"),
                },
                "screenshot": mobile_data.get("lighthouseResult", {}).get("audits", {}).get("final-screenshot", {}).get("details", {}).get("data", None)
            }
            
            print(f"[OK] PageSpeed completato - Performance Desktop: {result['desktop']['performance']}/100, Mobile: {result['mobile']['performance']}/100")
            
            return result
    
    except httpx.HTTPStatusError as e:
        error_msg = f"Errore HTTP {e.response.status_code}: {e.response.text}"
        print(f"[ERROR] {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "data": None
        }
    
    except httpx.TimeoutException:
        error_msg = "Timeout nella chiamata a PageSpeed Insights (30s)"
        print(f"[ERROR] {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "data": None
        }
    
    except Exception as e:
        error_msg = f"Errore generico: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "data": None
        }
