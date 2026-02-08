"""
DigIdentity Engine — AI Service
Generazione report con Claude API (Anthropic).
"""

import anthropic
import json
import re
import os
import asyncio
from typing import Dict, Any
from app.config import get_settings


def extract_json_from_text(text: str) -> dict:
    """
    Estrae un oggetto JSON da testo che potrebbe contenere altro contenuto.
    Gestisce i casi in cui Claude aggiunge testo prima/dopo il JSON.
    """
    # Tentativo 1: parse diretto
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Tentativo 2: cerca JSON tra backtick ```json ... ```
    match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Tentativo 3: cerca il primo { e l'ultimo } nel testo
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace:last_brace + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # Tentativo 4: costruisci JSON dalle sezioni trovate con regex
    sections = {}
    pattern = r'"(section_\d+)"\s*:\s*"((?:[^"\\]|\\.)*)"|"(section_\d+)"\s*:\s*"([\s\S]*?)"(?=\s*,\s*"section_|\s*\})'
    matches = re.finditer(pattern, text)
    for m in matches:
        key = m.group(1) or m.group(3)
        value = m.group(2) or m.group(4)
        if key and value:
            sections[key] = value

    if sections:
        return sections

    raise ValueError(f"Impossibile estrarre JSON dalla risposta Claude. Primi 500 caratteri: {text[:500]}")


async def generate_free_report_ai(
    lead_data: Dict[str, Any],
    analysis_data: Dict[str, Any],
    scores: Dict[str, int]
) -> Dict[str, Any]:
    """
    Genera report gratuito (5 sezioni HTML) usando Claude API.
    """
    settings = get_settings()

    print(f"[AI] Generazione report AI con Claude...")
    print(f"   Modello: {settings.anthropic_model}")
    print(f"   Max tokens: {settings.anthropic_max_tokens}")

    # Carica prompt da file
    prompt_path = os.path.join(os.path.dirname(__file__), "../../../directives/prompts/free-report-prompt.md")
    # Fallback path per struttura diversa
    if not os.path.exists(prompt_path):
        prompt_path = "c:/Users/stefa/Desktop/digidentity-projects/directives/prompts/free-report-prompt.md"

    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    # Prepara input dati per Claude
    input_data = {
        "lead": {
            "nome_azienda": lead_data.get("nome_azienda"),
            "settore_attivita": lead_data.get("settore_attivita"),
            "citta": lead_data.get("citta"),
            "provincia": lead_data.get("provincia"),
            "sito_web": lead_data.get("sito_web"),
            "nome_contatto": lead_data.get("nome_contatto")
        },
        "analysis": analysis_data,
        "scores": scores
    }

    user_message = f"""Genera il report di Diagnosi Strategica Digitale GRATUITA (5 pagine HTML) per questa azienda.

DATI INPUT:
{json.dumps(input_data, ensure_ascii=False, indent=2)}

ISTRUZIONI:
- Genera 5 sezioni HTML separate (section_1, section_2, section_3, section_4, section_5)
- Ogni sezione deve essere HTML completo e standalone
- Usa i colori brand: Rosso #F90100, Nero #000000
- Tono: semplice, diretto, come spiegare a una nonna
- Focus su AZIONI CONCRETE e ROI
- Includi emoji dove appropriato
- Ogni sezione max 800 parole

IMPORTANTE: Rispondi SOLO con JSON valido, senza testo prima o dopo. Formato esatto:
{{
  "section_1": "<div>...</div>",
  "section_2": "<div>...</div>",
  "section_3": "<div>...</div>",
  "section_4": "<div>...</div>",
  "section_5": "<div>...</div>"
}}
"""

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        message = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=settings.anthropic_max_tokens,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        # Estrai contenuto
        content = message.content[0].text

        # Parse JSON con fallback robusti
        sections = extract_json_from_text(content)

        # Verifica che ci siano le sezioni attese
        expected_keys = [f"section_{i}" for i in range(1, 6)]
        for key in expected_keys:
            if key not in sections:
                sections[key] = f"<div><h2>Sezione non disponibile</h2><p>Questa sezione non è stata generata correttamente.</p></div>"

        # Calcola costo stimato
        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens

        # Prezzi Claude Sonnet 4 (Feb 2026)
        cost = (input_tokens / 1_000_000 * 3.0) + (output_tokens / 1_000_000 * 15.0)

        print(f"[OK] Report AI generato")
        print(f"   Input tokens: {input_tokens}")
        print(f"   Output tokens: {output_tokens}")
        print(f"   Costo stimato: ${cost:.4f}")

        return {
            "success": True,
            "sections": sections,
            "metadata": {
                "model": settings.anthropic_model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "cost_usd": round(cost, 4)
            }
        }

    except anthropic.RateLimitError as e:
        print(f"❌ Rate limit Claude API: {str(e)}")
        await asyncio.sleep(5)
        return await generate_free_report_ai(lead_data, analysis_data, scores)

    except anthropic.APIError as e:
        error_msg = f"Errore Claude API: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}

    except Exception as e:
        error_msg = f"Errore generico: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}


async def generate_premium_report_ai(
    lead_data: Dict[str, Any],
    free_analysis: Dict[str, Any],
    premium_analysis: Dict[str, Any],
    scores: Dict[str, int]
) -> Dict[str, Any]:
    """
    Genera report premium (40-50 pagine HTML, 11 sezioni) usando Claude API.
    """
    settings = get_settings()

    print(f"[AI] Generazione report PREMIUM AI con Claude...")
    print(f"   Modello: {settings.anthropic_model}")
    print(f"   Target: 40-50 pagine, 11 sezioni")

    # Carica prompt premium
    prompt_path = os.path.join(os.path.dirname(__file__), "../../../directives/prompts/premium-report-prompt.md")
    if not os.path.exists(prompt_path):
        prompt_path = "c:/Users/stefa/Desktop/digidentity-projects/directives/prompts/premium-report-prompt.md"

    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    input_data = {
        "lead": {
            "nome_azienda": lead_data.get("nome_azienda"),
            "settore_attivita": lead_data.get("settore_attivita"),
            "citta": lead_data.get("citta"),
            "provincia": lead_data.get("provincia"),
            "sito_web": lead_data.get("sito_web"),
            "nome_contatto": lead_data.get("nome_contatto"),
            "obiettivo_principale": lead_data.get("obiettivo_principale"),
            "budget_mensile_indicativo": lead_data.get("budget_mensile_indicativo")
        },
        "free_analysis": free_analysis,
        "premium_analysis": premium_analysis,
        "scores": scores
    }

    user_message = f"""Genera il report di Diagnosi Strategica Digitale PREMIUM (40-50 pagine HTML) per questa azienda.

DATI INPUT:
{json.dumps(input_data, ensure_ascii=False, indent=2)}

ISTRUZIONI:
- Genera 11 sezioni HTML separate (section_1 ... section_11)
- Ogni sezione deve essere HTML completo e standalone
- Usa i colori brand: Rosso #F90100, Nero #000000
- Tono: professionale ma accessibile, orientato all'azione
- Focus su STRATEGIA CONCRETA, ROI e PIANO OPERATIVO
- Includi grafici, tabelle, timeline dove appropriato
- Sezione 11 (Proposta) deve includere preventivo dettagliato

IMPORTANTE: Rispondi SOLO con JSON valido, senza testo prima o dopo. Formato esatto:
{{
  "section_1": "<div>...</div>",
  "section_2": "<div>...</div>",
  "section_3": "<div>...</div>",
  "section_4": "<div>...</div>",
  "section_5": "<div>...</div>",
  "section_6": "<div>...</div>",
  "section_7": "<div>...</div>",
  "section_8": "<div>...</div>",
  "section_9": "<div>...</div>",
  "section_10": "<div>...</div>",
  "section_11": "<div>...</div>"
}}
"""

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        message = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=8000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        content = message.content[0].text

        # Parse JSON con fallback robusti
        sections = extract_json_from_text(content)

        # Verifica sezioni attese
        expected_keys = [f"section_{i}" for i in range(1, 12)]
        for key in expected_keys:
            if key not in sections:
                sections[key] = f"<div><h2>Sezione non disponibile</h2><p>Questa sezione non è stata generata correttamente.</p></div>"

        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens
        cost = (input_tokens / 1_000_000 * 3.0) + (output_tokens / 1_000_000 * 15.0)

        print(f"[OK] Report PREMIUM AI generato")
        print(f"   Input tokens: {input_tokens}")
        print(f"   Output tokens: {output_tokens}")
        print(f"   Costo stimato: ${cost:.4f}")

        return {
            "success": True,
            "sections": sections,
            "metadata": {
                "model": settings.anthropic_model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "cost_usd": round(cost, 4)
            }
        }

    except anthropic.RateLimitError as e:
        print(f"❌ Rate limit Claude API: {str(e)}")
        await asyncio.sleep(10)
        return await generate_premium_report_ai(lead_data, free_analysis, premium_analysis, scores)

    except Exception as e:
        error_msg = f"Errore Claude API: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "error": error_msg}
