"""
DigIdentity Engine — Generazione report AI con fallback.

Ordine di priorità:
- Report FREE: OpenAI GPT-4o (più economico) → Claude Sonnet (fallback)
- Report PREMIUM: Claude Sonnet (qualità superiore) → OpenAI GPT-4o (fallback)
"""

import json
import logging
from pathlib import Path
from typing import Any

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "directives" / "prompts"


def load_prompt(prompt_name: str) -> str:
    """Carica un prompt dalla directory directives/prompts/."""
    prompt_path = PROMPTS_DIR / f"{prompt_name}.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt non trovato: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")


def _call_openai(system_prompt: str, user_message: str, max_tokens: int = 16000) -> dict:
    """Chiama OpenAI GPT-4o."""
    import openai
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        max_tokens=max_tokens,
        temperature=0.7,
    )
    
    return {
        "text": response.choices[0].message.content,
        "model": response.model,
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
    }


def _call_claude(system_prompt: str, user_message: str, max_tokens: int = 16000) -> dict:
    """Chiama Claude Sonnet."""
    import anthropic
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
        temperature=0.7,
    )
    
    return {
        "text": response.content[0].text,
        "model": response.model,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }


def _call_ai(system_prompt: str, user_message: str, max_tokens: int = 16000, prefer: str = "openai") -> dict:
    """
    Chiama AI con fallback automatico.
    prefer="openai" → prova OpenAI prima, poi Claude
    prefer="claude" → prova Claude prima, poi OpenAI
    """
    if prefer == "openai":
        providers = [
            ("OpenAI", _call_openai, bool(settings.OPENAI_API_KEY)),
            ("Claude", _call_claude, bool(settings.ANTHROPIC_API_KEY)),
        ]
    else:
        providers = [
            ("Claude", _call_claude, bool(settings.ANTHROPIC_API_KEY)),
            ("OpenAI", _call_openai, bool(settings.OPENAI_API_KEY)),
        ]
    
    last_error = None
    for name, func, available in providers:
        if not available:
            logger.info(f"[AI] {name} non configurato, skip")
            continue
        try:
            logger.info(f"[AI] Chiamata {name}...")
            result = func(system_prompt, user_message, max_tokens)
            logger.info(f"[AI] {name} OK — {result['output_tokens']} tokens output")
            return result
        except Exception as e:
            logger.warning(f"[AI] {name} fallito: {e}")
            last_error = e
    
    raise Exception(f"Tutti i provider AI hanno fallito. Ultimo errore: {last_error}")


def generate_free_report(scraping_data: dict[str, Any]) -> str:
    """
    Genera il report gratuito di diagnosi digitale.
    Usa OpenAI come prima scelta (più economico per il free).
    """
    company_name = scraping_data.get("company_name", "Azienda")
    logger.info(f"[FREE] Generazione report per {company_name}")

    system_prompt = load_prompt("free_report_system")
    user_prompt_template = load_prompt("free_report_user")

    # Costruiamo il messaggio utente appendendo il JSON (Fix critico)
    user_message = user_prompt_template + "\n\n---\n\n"
    user_message += "Ecco i dati di scraping dell'azienda in formato JSON:\n\n"
    user_message += "```json\n"
    user_message += json.dumps(scraping_data, indent=2, default=str, ensure_ascii=False)
    user_message += "\n```"

    result = _call_ai(system_prompt, user_message, max_tokens=16000, prefer="openai")
    
    logger.info(
        f"[FREE] Report generato per {company_name}: "
        f"{len(result['text'])} car, modello={result['model']}, "
        f"input={result['input_tokens']}, output={result['output_tokens']}"
    )
    return result["text"]


def generate_premium_report(scraping_data: dict[str, Any], free_report: str = "") -> str:
    """
    Genera il report premium (40-50 pagine).
    Usa Claude come prima scelta (qualità superiore per il premium).
    Genera in 3 parti per gestire la lunghezza.
    """
    company_name = scraping_data.get("company_name", "Azienda")
    logger.info(f"[PREMIUM] Generazione report per {company_name}")

    system_prompt = load_prompt("premium_report_system")
    user_prompt = load_prompt("premium_report_user")

    user_message = user_prompt.replace(
        "{{SCRAPING_DATA}}", json.dumps(scraping_data, indent=2, ensure_ascii=False)
    ).replace(
        "{{COMPANY_NAME}}", company_name
    ).replace(
        "{{WEBSITE_URL}}", scraping_data.get("website_url", "N/D")
    ).replace(
        "{{FREE_REPORT}}", free_report
    )

    # Parte 1: Executive Summary → Analisi SEO/SEM
    part1_prompt = user_message + "\n\n**ISTRUZIONE: Genera le PARTI 1-5 del report (dall'Executive Summary fino all'Analisi SEO/SEM inclusa).**"
    result1 = _call_ai(system_prompt, part1_prompt, max_tokens=16000, prefer="claude")
    logger.info(f"[PREMIUM] Parte 1 completata: {result1['output_tokens']} tokens")

    # Parte 2: Social Media → Strategia AI
    part2_prompt = (
        f"Hai già generato le parti 1-5:\n\n{result1['text']}\n\n"
        f"Ora genera le PARTI 6-8 (Social Media, Content Strategy, Strategia AI/Automazioni) "
        f"basandoti sugli stessi dati:\n\n{user_message}"
    )
    result2 = _call_ai(system_prompt, part2_prompt, max_tokens=16000, prefer="claude")
    logger.info(f"[PREMIUM] Parte 2 completata: {result2['output_tokens']} tokens")

    # Parte 3: Piano 90gg → Conclusioni
    part3_prompt = (
        f"Hai già generato le parti 1-8:\n\n{result1['text']}\n\n{result2['text']}\n\n"
        f"Ora genera le PARTI 9-11 (Piano Operativo 90 giorni, Budget/ROI, Conclusioni con CTA consulenza 199€) "
        f"basandoti sugli stessi dati:\n\n{user_message}"
    )
    result3 = _call_ai(system_prompt, part3_prompt, max_tokens=16000, prefer="claude")
    logger.info(f"[PREMIUM] Parte 3 completata: {result3['output_tokens']} tokens")

    full_report = f"{result1['text']}\n\n{result2['text']}\n\n{result3['text']}"
    
    total_input = result1['input_tokens'] + result2['input_tokens'] + result3['input_tokens']
    total_output = result1['output_tokens'] + result2['output_tokens'] + result3['output_tokens']
    
    logger.info(
        f"[PREMIUM] Report completo per {company_name}: "
        f"{len(full_report)} car, input_tot={total_input}, output_tot={total_output}"
    )
    return full_report
