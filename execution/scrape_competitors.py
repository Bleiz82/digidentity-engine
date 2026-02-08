"""
DigIdentity Engine — Competitors Scraper
Analizza competitor locali tramite dati già raccolti da SERP/GMB.
OTTIMIZZATO: Riutilizza dati da scrape_serp per non consumare query extra.
"""

from typing import Dict, Any, List


def analyze_competitors(
    serp_data: Dict[str, Any],
    gmb_data: Dict[str, Any],
    nome_azienda: str
) -> Dict[str, Any]:
    """
    Analizza competitor basandosi sui dati SERP e GMB già raccolti.
    
    OTTIMIZZAZIONE: Non fa nuove chiamate API, riutilizza dati esistenti
    per evitare di consumare crediti SerpAPI aggiuntivi.
    
    Args:
        serp_data: Dati da scrape_serp (include local pack)
        gmb_data: Dati da scrape_gmb
        nome_azienda: Nome dell'azienda analizzata
        
    Returns:
        dict: Lista competitor con rating, recensioni, posizionamento
    """
    print(f"[COMPETITORS] Analisi competitor per: {nome_azienda}")
    
    competitors = []
    
    # Estrai competitor dal Local Pack (già in serp_data)
    if serp_data.get("success") and serp_data.get("local_pack"):
        local_competitors = serp_data["local_pack"].get("competitors", [])
        
        for comp in local_competitors:
            # Salta se è l'azienda stessa
            if nome_azienda.lower() in comp.get("name", "").lower():
                continue
            
            competitors.append({
                "name": comp.get("name"),
                "rating": comp.get("rating"),
                "reviews": comp.get("reviews"),
                "source": "Google Local Pack",
                "position_local_pack": local_competitors.index(comp) + 1
            })
    
    # Ordina per numero recensioni (proxy per dimensione/presenza)
    competitors.sort(key=lambda x: x.get("reviews", 0), reverse=True)
    
    # Limita ai top 5
    top_competitors = competitors[:5]
    
    # Calcola medie competitor
    if top_competitors:
        avg_rating = sum(c.get("rating", 0) for c in top_competitors) / len(top_competitors)
        avg_reviews = sum(c.get("reviews", 0) for c in top_competitors) / len(top_competitors)
    else:
        avg_rating = 0
        avg_reviews = 0
    
    # Confronto con l'azienda analizzata
    own_rating = gmb_data.get("data", {}).get("rating", 0) if gmb_data.get("found") else 0
    own_reviews = gmb_data.get("data", {}).get("reviews_count", 0) if gmb_data.get("found") else 0
    
    result = {
        "success": True,
        "total_competitors_found": len(competitors),
        "top_competitors": top_competitors,
        "benchmarks": {
            "avg_competitor_rating": round(avg_rating, 1),
            "avg_competitor_reviews": int(avg_reviews),
            "own_rating": own_rating,
            "own_reviews": own_reviews,
            "rating_gap": round(own_rating - avg_rating, 1) if own_rating else None,
            "reviews_gap": int(own_reviews - avg_reviews) if own_reviews else None
        },
        "competitive_position": calculate_competitive_position(
            own_rating, own_reviews, avg_rating, avg_reviews
        )
    }
    
    print(f"[OK] Competitor analysis completata")
    print(f"   Competitor trovati: {len(top_competitors)}")
    print(f"   Rating medio competitor: {avg_rating:.1f}/5")
    print(f"   Posizione competitiva: {result['competitive_position']}")
    
    return result


def calculate_competitive_position(
    own_rating: float,
    own_reviews: int,
    avg_rating: float,
    avg_reviews: int
) -> str:
    """
    Calcola posizione competitiva dell'azienda.
    
    Args:
        own_rating: Rating dell'azienda
        own_reviews: Numero recensioni dell'azienda
        avg_rating: Rating medio competitor
        avg_reviews: Numero medio recensioni competitor
        
    Returns:
        str: Posizione competitiva (leader/strong/average/weak/new)
    """
    if not own_rating or not own_reviews:
        return "new"  # Nessuna presenza GMB
    
    # Leader: rating sopra media E recensioni sopra media
    if own_rating >= avg_rating and own_reviews >= avg_reviews:
        if own_rating >= avg_rating + 0.5 and own_reviews >= avg_reviews * 1.5:
            return "leader"
        return "strong"
    
    # Weak: rating sotto media E recensioni sotto media
    if own_rating < avg_rating and own_reviews < avg_reviews:
        return "weak"
    
    # Average: mix
    return "average"
