"""
DigIdentity Engine — Google My Business Scraper
Analizza scheda GMB tramite SerpAPI Google Maps.
"""

import httpx
from typing import Dict, Any
from app.config import get_settings


async def scrape_gmb(nome_azienda: str, citta: str) -> Dict[str, Any]:
    """
    Cerca e analizza la scheda Google My Business di un'azienda.
    
    Args:
        nome_azienda: Nome dell'azienda
        citta: Città
        
    Returns:
        dict: Dati GMB (rating, recensioni, completezza scheda)
    """
    settings = get_settings()
    
    print(f"[GMB] Ricerca GMB per: {nome_azienda} a {citta}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Ricerca su Google Maps
            query = f"{nome_azienda} {citta}"
            
            response = await client.get(
                "https://serpapi.com/search",
                params={
                    "engine": "google_maps",
                    "q": query,
                    "hl": "it",
                    "gl": "it",
                    "api_key": settings.serp_api_key
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Estrai primo risultato (dovrebbe essere l'azienda cercata)
            local_results = data.get("local_results", [])
            
            if not local_results:
                print(f"[WARN] GMB non trovato per {nome_azienda}")
                return {
                    "success": True,
                    "found": False,
                    "data": None
                }
            
            # Prendi il primo risultato
            gmb = local_results[0]
            
            result = {
                "success": True,
                "found": True,
                "data": {
                    "name": gmb.get("title"),
                    "rating": gmb.get("rating"),
                    "reviews_count": gmb.get("reviews", 0),
                    "type": gmb.get("type"),
                    "address": gmb.get("address"),
                    "phone": gmb.get("phone"),
                    "website": gmb.get("website"),
                    "hours": gmb.get("hours"),
                    "description": gmb.get("description"),
                    "service_options": gmb.get("service_options", {}),
                    "thumbnail": gmb.get("thumbnail"),
                    "place_id": gmb.get("place_id"),
                    
                    # Completezza scheda (calcolata)
                    "completeness": calculate_gmb_completeness(gmb)
                }
            }
            
            print(f"[OK] GMB trovato - Rating: {result['data']['rating']}/5 ({result['data']['reviews_count']} recensioni)")
            print(f"   Completezza scheda: {result['data']['completeness']}%")
            
            return result
    
    except httpx.HTTPStatusError as e:
        error_msg = f"Errore HTTP {e.response.status_code}: {e.response.text}"
        print(f"[ERROR] {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "found": False
        }
    
    except httpx.TimeoutException:
        error_msg = "Timeout nella chiamata a SerpAPI Maps (30s)"
        print(f"[ERROR] {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "found": False
        }
    
    except Exception as e:
        error_msg = f"Errore generico: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "found": False
        }


def calculate_gmb_completeness(gmb_data: Dict[str, Any]) -> int:
    """
    Calcola percentuale di completezza della scheda GMB.
    
    Args:
        gmb_data: Dati GMB da SerpAPI
        
    Returns:
        int: Percentuale completezza (0-100)
    """
    score = 0
    max_score = 10
    
    # Nome (obbligatorio, sempre presente)
    if gmb_data.get("title"):
        score += 1
    
    # Indirizzo
    if gmb_data.get("address"):
        score += 1
    
    # Telefono
    if gmb_data.get("phone"):
        score += 1
    
    # Sito web
    if gmb_data.get("website"):
        score += 1
    
    # Orari
    if gmb_data.get("hours"):
        score += 1
    
    # Descrizione
    if gmb_data.get("description"):
        score += 1
    
    # Categoria/Tipo
    if gmb_data.get("type"):
        score += 1
    
    # Foto (thumbnail presente)
    if gmb_data.get("thumbnail"):
        score += 1
    
    # Recensioni (almeno 1)
    if gmb_data.get("reviews", 0) > 0:
        score += 1
    
    # Service options
    if gmb_data.get("service_options"):
        score += 1
    
    return int((score / max_score) * 100)
