"""
DigIdentity Engine — AI Opportunities Analyzer (Premium)
Analisi opportunità AI con Perplexity AI.
"""

import httpx
import json
from typing import Dict, Any
from app.config import get_settings


async def analyze_ai_opportunities(
    nome_azienda: str,
    settore: str,
    citta: str,
    free_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analizza opportunità AI specifiche per l'azienda usando Perplexity AI.
    
    Perplexity fornisce:
    - Ricerca contestuale su trend AI nel settore
    - Casi d'uso AI specifici per il business
    - ROI stimato per ogni opportunità
    - Competitor che usano già AI
    - Tool e piattaforme consigliate
    
    Args:
        nome_azienda: Nome azienda
        settore: Settore di attività
        citta: Città
        free_analysis: Dati dalla diagnosi gratuita
        
    Returns:
        dict: Opportunità AI personalizzate con ROI e priorità
    """
    settings = get_settings()
    
    print(f"🤖 Analisi opportunità AI per: {nome_azienda} ({settore})")
    
    # Prepara prompt per Perplexity
    prompt = f"""Analizza le opportunità di Intelligenza Artificiale e Automazioni per questa azienda italiana:

**Azienda:** {nome_azienda}
**Settore:** {settore}
**Località:** {citta}

**Contesto attuale:**
- Score sito web: {free_analysis.get('scores', {}).get('score_sito_web', 'N/A')}/100
- Score SEO: {free_analysis.get('scores', {}).get('score_seo', 'N/A')}/100
- Score GMB: {free_analysis.get('scores', {}).get('score_gmb', 'N/A')}/100
- Score Social: {free_analysis.get('scores', {}).get('score_social', 'N/A')}/100

**Richiesta:**
Identifica 5-7 opportunità concrete di AI e automazioni specifiche per questo business, considerando:
1. Trend AI nel settore {settore} in Italia
2. Casi d'uso già adottati da competitor
3. Quick wins (implementabili in 1-2 mesi)
4. Opportunità a medio termine (3-6 mesi)
5. ROI stimato per ogni opportunità
6. Tool/piattaforme consigliate (con costi indicativi)

Per ogni opportunità fornisci:
- Nome e descrizione
- Benefici concreti (tempo risparmiato, clienti in più, etc.)
- ROI stimato (€ o % incremento revenue)
- Complessità implementazione (bassa/media/alta)
- Costo stimato implementazione
- Tempo implementazione
- Priorità (alta/media/bassa)

Rispondi in formato JSON strutturato."""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.perplexity_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.perplexity_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Sei un consulente esperto di AI e automazioni per PMI italiane. Fornisci analisi concrete, pratiche e orientate al ROI."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.2,
                    "max_tokens": 2000
                }
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Estrai contenuto
            content = data["choices"][0]["message"]["content"]
            
            # Prova a parsare JSON
            try:
                opportunities = json.loads(content)
            except json.JSONDecodeError:
                # Se non è JSON, usa il testo raw
                opportunities = {
                    "raw_analysis": content,
                    "note": "Analisi in formato testo, non JSON strutturato"
                }
            
            # Metadata
            usage = data.get("usage", {})
            
            result = {
                "success": True,
                "opportunities": opportunities,
                "metadata": {
                    "model": settings.perplexity_model,
                    "tokens_used": usage.get("total_tokens", 0),
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0)
                }
            }
            
            print(f"✅ Analisi AI completata")
            print(f"   Tokens: {usage.get('total_tokens', 0)}")
            
            return result
    
    except httpx.HTTPStatusError as e:
        error_msg = f"Errore HTTP Perplexity: {e.response.status_code} - {e.response.text}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }
    
    except Exception as e:
        error_msg = f"Errore analisi AI: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }
