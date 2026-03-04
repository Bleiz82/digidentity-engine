"""
DigIdentity Engine — Smart Discovery (Layer 0)

Prima di qualsiasi scraping, esegue una ricerca intelligente per trovare
tutte le varianti reali dell'attività sul web.

Flusso:
1. Serper.dev (3-4 query mirate) → risultati reali da Google
2. Claude AI analizza e struttura i risultati in JSON pulito

Output: dizionario con nomi reali, URL social verificati, place_id, settore, ecc.
"""

import logging
import json
import re
import requests
from typing import Any

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

SERPER_URL = "https://google.serper.dev/search"
SERPER_TIMEOUT = 15


def _serper_search(query: str, num: int = 10) -> dict:
    """Esegue una singola ricerca Serper.dev"""
    if not settings.SERPER_KEY:
        logger.warning("[DISCOVERY] SERPER_KEY non configurata")
        return {}
    try:
        resp = requests.post(
            SERPER_URL,
            headers={"X-API-KEY": settings.SERPER_KEY, "Content-Type": "application/json"},
            json={"q": query, "gl": "it", "hl": "it", "num": num},
            timeout=SERPER_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"[DISCOVERY] Errore Serper query '{query}': {e}")
        return {}


def smart_discovery(
    nome_azienda: str,
    indirizzo: str = "",
    email: str = "",
    telefono: str = "",
    nome_titolare: str = "",
    sito_web: str = "",
    citta: str = "",
    settore: str = "",
) -> dict[str, Any]:
    """
    Ricerca intelligente pre-scraping.
    Trova tutte le varianti reali dell'attività e i profili social corretti.
    
    Returns:
        dict con chiavi:
        - nome_google_business: str
        - varianti_nome: list[str]
        - facebook_url: str
        - facebook_type: "pagina"|"profilo_personale"|null
        - instagram_username: str
        - linkedin_url: str
        - youtube_url: str
        - tiktok_url: str
        - google_maps_place_id: str
        - sito_web_confermato: str
        - settore_rilevato: str
        - citta_confermata: str
        - telefono_trovato: str
        - email_trovata: str
    """
    logger.info(f"[DISCOVERY] === Inizio Smart Discovery per '{nome_azienda}' ===")

    # Costruisci contesto di ricerca
    search_parts = [nome_azienda]
    if citta:
        search_parts.append(citta)
    elif indirizzo:
        # Estrai città dall'indirizzo
        parti = [p.strip() for p in indirizzo.split(",")]
        if len(parti) >= 2:
            search_parts.append(parti[-1].strip())

    base_query = " ".join(search_parts)

    # === STEP 1: Serper.dev — 4 query mirate ===
    all_results = {}

    # Query 1: Ricerca brand generica (cattura KG, local pack, organic)
    logger.info(f"[DISCOVERY] Query 1: '{base_query}'")
    all_results["brand"] = _serper_search(base_query)

    # Query 2: Brand + nome titolare (per trovare profili personali usati come business)
    if nome_titolare:
        q2 = f"{nome_azienda} {nome_titolare}"
        logger.info(f"[DISCOVERY] Query 2: '{q2}'")
        all_results["titolare"] = _serper_search(q2)

    # Query 3: Cerca specificamente i social
    q3 = f"{nome_azienda} {citta or ''} site:facebook.com OR site:instagram.com OR site:linkedin.com"
    logger.info(f"[DISCOVERY] Query 3: '{q3}'")
    all_results["social"] = _serper_search(q3)

    # Query 4: Google Maps / local business
    q4 = f"{nome_azienda} {citta or ''} google maps"
    logger.info(f"[DISCOVERY] Query 4: '{q4}'")
    all_results["maps"] = _serper_search(q4)

    # Conta risultati totali
    total_organic = sum(
        len(r.get("organic", [])) for r in all_results.values()
    )
    has_kg = bool(all_results.get("brand", {}).get("knowledgeGraph"))
    has_local = bool(all_results.get("brand", {}).get("places"))
    logger.info(f"[DISCOVERY] Serper: {total_organic} risultati organici, KG={has_kg}, LocalPack={has_local}")

    # === STEP 2: Claude analizza e struttura ===
    discovery_result = _analyze_with_claude(
        nome_azienda=nome_azienda,
        indirizzo=indirizzo,
        email=email,
        telefono=telefono,
        nome_titolare=nome_titolare,
        sito_web=sito_web,
        citta=citta,
        settore=settore,
        serper_results=all_results,
    )

    logger.info(f"[DISCOVERY] === Discovery completato: {len(discovery_result.get('varianti_nome', []))} varianti trovate ===")
    return discovery_result


def _analyze_with_claude(
    nome_azienda: str,
    indirizzo: str,
    email: str,
    telefono: str,
    nome_titolare: str,
    sito_web: str,
    citta: str,
    settore: str,
    serper_results: dict,
) -> dict[str, Any]:
    """
    Claude analizza i risultati Serper e produce un JSON strutturato
    con tutti i dati reali trovati.
    """
    if not settings.ANTHROPIC_API_KEY:
        logger.error("[DISCOVERY] ANTHROPIC_API_KEY mancante — uso fallback")
        return _fallback_discovery(nome_azienda, serper_results)

    # Prepara i dati Serper in formato leggibile per Claude
    serper_summary = _summarize_serper_results(serper_results)

    prompt = f"""Analizza questi risultati di ricerca Google per identificare TUTTE le presenze online reali di un'attività.

DATI DAL FORM:
- Nome attività: {nome_azienda}
- Indirizzo: {indirizzo or 'non fornito'}
- Email: {email or 'non fornita'}
- Telefono: {telefono or 'non fornito'}
- Nome titolare: {nome_titolare or 'non fornito'}
- Sito web: {sito_web or 'non fornito'}
- Città: {citta or 'non fornita'}
- Settore: {settore or 'non fornito'}

RISULTATI DI RICERCA GOOGLE:
{serper_summary}

ISTRUZIONI:
1. Identifica il NOME ESATTO con cui l'attività è registrata su Google Business (spesso diverso dal nome fornito)
2. Trova TUTTI i profili social REALI — attenzione: molte PMI italiane usano un PROFILO PERSONALE Facebook invece di una pagina aziendale
3. Per Facebook: distingui se è una pagina (facebook.com/nomeazienda) o un profilo personale (facebook.com/nome.cognome o profile.php?id=)
4. Per Instagram: estrai solo lo username (senza URL completo)
5. Identifica SEMPRE il settore/categoria merceologica reale dell'attivita (es: "Falegnameria", "Ristorante", "Idraulico", "Parrucchiere", "Autofficina", "Web Agency", "Studio legale"). Basati sul nome dell'attivita, sui risultati di ricerca Google, sulle descrizioni trovate e sul contesto. NON restituire mai null, "Da identificare" o "Altro". Se il settore non e evidente dal nome, DEDUCILO dai servizi offerti, dalla descrizione Google Business, dai post social o dalle pagine trovate
6. Trova tutte le VARIANTI DEL NOME usate online (es: "Sardegna Restauri", "Sardegna Restauri Srls", "Sardegna Restauri di Mario Rossi")

RISPONDI ESCLUSIVAMENTE con un JSON valido, senza markdown, senza commenti:
{{
    "nome_google_business": "nome esatto su Google Business o null",
    "varianti_nome": ["variante1", "variante2"],
    "facebook_url": "URL completo o null",
    "facebook_type": "pagina" | "profilo_personale" | null,
    "instagram_username": "username senza @ o null",
    "linkedin_url": "URL completo o null",
    "youtube_url": "URL completo o null",
    "tiktok_url": "URL completo o null",
    "google_maps_place_id": "place_id se trovato o null",
    "sito_web_confermato": "URL confermato o null",
    "settore_rilevato": "settore identificato o null",
    "citta_confermata": "città confermata o null",
    "telefono_trovato": "telefono trovato online o null",
    "email_trovata": "email trovata online o null",
    "rating_google": numero o null,
    "reviews_count_google": numero o null,
    "descrizione_breve": "breve descrizione dell'attività basata su ciò che hai trovato"
}}"""

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1500,
                "temperature": 0.1,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["content"][0]["text"].strip()

        # Pulisci eventuale markdown wrapper
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)

        result = json.loads(content)
        
        # Assicurati che tutte le chiavi esistano
        defaults = {
            "nome_google_business": None,
            "varianti_nome": [],
            "facebook_url": None,
            "facebook_type": None,
            "instagram_username": None,
            "linkedin_url": None,
            "youtube_url": None,
            "tiktok_url": None,
            "google_maps_place_id": None,
            "sito_web_confermato": sito_web or None,
            "settore_rilevato": settore or None,
            "citta_confermata": citta or None,
            "telefono_trovato": telefono or None,
            "email_trovata": email or None,
            "rating_google": None,
            "reviews_count_google": None,
            "descrizione_breve": None,
        }
        for k, v in defaults.items():
            if k not in result or result[k] is None:
                result[k] = v

        # Aggiungi sempre il nome originale alle varianti
        if nome_azienda not in result["varianti_nome"]:
            result["varianti_nome"].insert(0, nome_azienda)

        tokens_in = data.get("usage", {}).get("input_tokens", 0)
        tokens_out = data.get("usage", {}).get("output_tokens", 0)
        logger.info(f"[DISCOVERY] Claude: {tokens_in}+{tokens_out} tokens, GMB='{result.get('nome_google_business')}', FB={result.get('facebook_url')}, IG=@{result.get('instagram_username')}")

        return result

    except json.JSONDecodeError as e:
        logger.error(f"[DISCOVERY] Claude ha restituito JSON non valido: {e}")
        return _fallback_discovery(nome_azienda, serper_results)
    except Exception as e:
        logger.error(f"[DISCOVERY] Errore Claude: {e}")
        return _fallback_discovery(nome_azienda, serper_results)


def _summarize_serper_results(serper_results: dict) -> str:
    """Converte i risultati Serper in testo leggibile per Claude."""
    lines = []

    for label, data in serper_results.items():
        if not data:
            continue
        lines.append(f"\n--- RICERCA: {label.upper()} ---")

        # Knowledge Graph
        kg = data.get("knowledgeGraph", {})
        if kg:
            lines.append(f"KNOWLEDGE GRAPH: {json.dumps(kg, ensure_ascii=False)[:1000]}")

        # Local Pack / Places
        places = data.get("places", [])
        if places:
            lines.append(f"LOCAL PACK ({len(places)} risultati):")
            for p in places[:5]:
                lines.append(f"  - {p.get('title', '?')} | Rating: {p.get('rating', '?')} | Reviews: {p.get('reviews', '?')} | Addr: {p.get('address', '?')} | CID: {p.get('cid', '?')}")

        # Organic Results
        organic = data.get("organic", [])
        if organic:
            lines.append(f"RISULTATI ORGANICI ({len(organic)}):")
            for r in organic[:8]:
                lines.append(f"  - [{r.get('position', '?')}] {r.get('title', '?')}")
                lines.append(f"    URL: {r.get('link', '?')}")
                lines.append(f"    Snippet: {(r.get('snippet', '') or '')[:200]}")

    return "\n".join(lines)


def _fallback_discovery(nome_azienda: str, serper_results: dict) -> dict[str, Any]:
    """
    Fallback: se Claude non è disponibile, estrae i dati base dai risultati Serper.
    Meno preciso ma meglio di niente.
    """
    logger.info("[DISCOVERY] Uso fallback senza Claude")
    result = {
        "nome_google_business": None,
        "varianti_nome": [nome_azienda],
        "facebook_url": None,
        "facebook_type": None,
        "instagram_username": None,
        "linkedin_url": None,
        "youtube_url": None,
        "tiktok_url": None,
        "google_maps_place_id": None,
        "sito_web_confermato": None,
        "settore_rilevato": None,
        "citta_confermata": None,
        "telefono_trovato": None,
        "email_trovata": None,
        "rating_google": None,
        "reviews_count_google": None,
        "descrizione_breve": None,
    }

    # Estrai da Knowledge Graph
    kg = serper_results.get("brand", {}).get("knowledgeGraph", {})
    if kg:
        result["nome_google_business"] = kg.get("title")
        result["rating_google"] = kg.get("rating")
        result["reviews_count_google"] = kg.get("ratingCount")
        if kg.get("title") and kg["title"] != nome_azienda:
            result["varianti_nome"].append(kg["title"])

    # Estrai da Local Pack
    places = serper_results.get("brand", {}).get("places", [])
    if places:
        first = places[0]
        if not result["nome_google_business"]:
            result["nome_google_business"] = first.get("title")
        result["google_maps_place_id"] = first.get("cid")
        result["citta_confermata"] = first.get("address", "").split(",")[-1].strip() if first.get("address") else None
        if first.get("title") and first["title"] not in result["varianti_nome"]:
            result["varianti_nome"].append(first["title"])

    # Estrai social da organic results
    for label, data in serper_results.items():
        for r in data.get("organic", []):
            link = r.get("link", "")
            if "facebook.com" in link and not result["facebook_url"]:
                result["facebook_url"] = link
                result["facebook_type"] = "profilo_personale" if ("profile.php" in link or "/people/" in link) else "pagina"
            elif "instagram.com" in link and not result["instagram_username"]:
                username = link.rstrip("/").split("/")[-1].split("?")[0]
                if username and username not in ("explore", "accounts", "directory", "tags", "p", "reel"):
                    result["instagram_username"] = username
            elif "linkedin.com" in link and not result["linkedin_url"]:
                result["linkedin_url"] = link
            elif "youtube.com" in link and not result["youtube_url"]:
                result["youtube_url"] = link
            elif "tiktok.com" in link and not result["tiktok_url"]:
                result["tiktok_url"] = link

    return result
