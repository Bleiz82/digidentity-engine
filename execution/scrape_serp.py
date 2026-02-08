"""
DigIdentity Engine — SerpAPI Scraper
Analizza posizionamento Google e Local Pack per query specifiche.
OTTIMIZZATO: max 2-3 query per diagnosi (limite 250/mese gratuito).
"""

import httpx
from typing import Dict, Any, List
from app.config import get_settings


async def scrape_serp(nome_azienda: str, settore: str, citta: str) -> Dict[str, Any]:
    """
    Esegue ricerca su Google per verificare posizionamento dell'azienda.
    
    OTTIMIZZAZIONE: Esegue SOLO 2 query per risparmiare crediti SerpAPI:
    1. "{nome_azienda} {citta}" — posizionamento brand
    2. "{settore} {citta}" — posizionamento settore + local pack
    
    Args:
        nome_azienda: Nome dell'azienda
        settore: Settore di attività
        citta: Città
        
    Returns:
        dict: Risultati con posizionamento e competitor visibili
    """
    settings = get_settings()
    
    print(f"[SERP] Analisi SERP per: {nome_azienda} ({settore} a {citta})")
    print(f"[WARN] SerpAPI: 2 query consumate (limite mensile: {settings.serp_api_monthly_limit})")
    
    results = {
        "success": True,
        "queries_used": 2,
        "brand_query": {},
        "sector_query": {},
        "local_pack": {},
        "competitor_count": 0
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            
            # Query 1: Ricerca brand "{nome_azienda} {citta}"
            brand_query = f"{nome_azienda} {citta}"
            print(f"[INFO] Query 1/2: '{brand_query}'")
            
            brand_response = await client.get(
                "https://serpapi.com/search",
                params={
                    "q": brand_query,
                    "location": f"{citta}, Italy",
                    "hl": "it",
                    "gl": "it",
                    "api_key": settings.serp_api_key,
                    "num": 10
                }
            )
            brand_response.raise_for_status()
            brand_data = brand_response.json()
            
            # Estrai posizione organica per l'azienda
            organic_results = brand_data.get("organic_results", [])
            brand_position = None
            for idx, result in enumerate(organic_results, start=1):
                if nome_azienda.lower() in result.get("title", "").lower() or \
                   nome_azienda.lower() in result.get("link", "").lower():
                    brand_position = idx
                    break
            
            results["brand_query"] = {
                "query": brand_query,
                "position": brand_position,
                "found": brand_position is not None,
                "total_results": len(organic_results)
            }
            
            print(f"   → Posizione brand: {brand_position if brand_position else 'Non trovato in top 10'}")
            
            # Query 2: Ricerca settore "{settore} {citta}" + Local Pack
            sector_query = f"{settore} {citta}"
            print(f"[INFO] Query 2/2: '{sector_query}'")
            
            sector_response = await client.get(
                "https://serpapi.com/search",
                params={
                    "q": sector_query,
                    "location": f"{citta}, Italy",
                    "hl": "it",
                    "gl": "it",
                    "api_key": settings.serp_api_key,
                    "num": 10
                }
            )
            sector_response.raise_for_status()
            sector_data = sector_response.json()
            
            # Estrai posizione organica nel settore
            sector_organic = sector_data.get("organic_results", [])
            sector_position = None
            for idx, result in enumerate(sector_organic, start=1):
                if nome_azienda.lower() in result.get("title", "").lower() or \
                   nome_azienda.lower() in result.get("link", "").lower():
                    sector_position = idx
                    break
            
            results["sector_query"] = {
                "query": sector_query,
                "position": sector_position,
                "found": sector_position is not None,
                "total_results": len(sector_organic)
            }
            
            print(f"   → Posizione settore: {sector_position if sector_position else 'Non trovato in top 10'}")
            
            # Estrai Local Pack (Google Maps results)
            local_results = sector_data.get("local_results", {})
            local_places = local_results.get("places", [])
            
            in_local_pack = False
            local_pack_position = None
            
            for idx, place in enumerate(local_places, start=1):
                if nome_azienda.lower() in place.get("title", "").lower():
                    in_local_pack = True
                    local_pack_position = idx
                    break
            
            results["local_pack"] = {
                "present": in_local_pack,
                "position": local_pack_position,
                "total_places": len(local_places),
                "competitors": [
                    {
                        "name": place.get("title"),
                        "rating": place.get("rating"),
                        "reviews": place.get("reviews")
                    }
                    for place in local_places[:5]  # Top 5 nel local pack
                ]
            }
            
            results["competitor_count"] = len(local_places)
            
            print(f"   → Local Pack: {'Sì (pos. {})'.format(local_pack_position) if in_local_pack else 'No'}")
            print(f"   → Competitor visibili: {results['competitor_count']}")
            
            print(f"[OK] SERP analysis completata (2 query SerpAPI consumate)")
            
            return results
    
    except httpx.HTTPStatusError as e:
        error_msg = f"Errore HTTP {e.response.status_code}: {e.response.text}"
        print(f"[ERROR] {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "queries_used": 0
        }
    
    except httpx.TimeoutException:
        error_msg = "Timeout nella chiamata a SerpAPI (30s)"
        print(f"[ERROR] {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "queries_used": 0
        }
    
    except Exception as e:
        error_msg = f"Errore generico: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "queries_used": 0
        }
