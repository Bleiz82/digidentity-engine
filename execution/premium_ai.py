"""
DigIdentity Premium — AI Report Generator
Genera il report premium chiamando Claude sezione per sezione.
"""
import os
import time
import logging
from pathlib import Path
from anthropic import Anthropic

logger = logging.getLogger(__name__)

CLAUDE_MODEL_STANDARD = "claude-sonnet-4-20250514"
CLAUDE_MODEL_PREMIUM = "claude-opus-4-20250514"

PROMPTS_DIR = Path(__file__).parent.parent / "directives" / "prompts" / "premium"

SECTIONS = [
    {"id": "01_apertura_dashboard", "max_tokens": 2500, "model": "standard"},
    {"id": "02_sito_web", "max_tokens": 3500, "model": "standard"},
    {"id": "03_pagespeed_seo", "max_tokens": 3000, "model": "standard"},
    {"id": "04_keyword", "max_tokens": 2500, "model": "standard"},
    {"id": "05_google_business_reputazione", "max_tokens": 4000, "model": "standard"},
    {"id": "06_competitor", "max_tokens": 3500, "model": "standard"},
    {"id": "07_social_bio", "max_tokens": 4000, "model": "standard"},
    {"id": "08_branding_ai", "max_tokens": 3000, "model": "standard"},
    {"id": "09_ads", "max_tokens": 2500, "model": "standard"},
    {"id": "10_piano_90_giorni", "max_tokens": 5000, "model": "premium"},
    {"id": "11_relazione_punteggio", "max_tokens": 3500, "model": "premium"},
]

MAX_RETRIES = 3
RETRY_DELAY = 5


def _get_client() -> Anthropic:
    """Inizializza il client Anthropic."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY non configurata")
    return Anthropic(api_key=api_key)


def _load_prompt(filename: str) -> str:
    """Carica un file prompt dalla directory premium."""
    filepath = PROMPTS_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Prompt non trovato: {filepath}")
    return filepath.read_text(encoding="utf-8")


def _load_system_prompt() -> str:
    """Carica il system prompt."""
    return _load_prompt("00_system.md")


def call_claude(system_prompt: str, user_prompt: str, max_tokens: int, model_type: str = "standard") -> str:
    """Chiama Claude con retry e backoff."""
    client = _get_client()
    model = CLAUDE_MODEL_PREMIUM if model_type == "premium" else CLAUDE_MODEL_STANDARD

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Chiamata Claude ({model}) - tentativo {attempt}")
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            text = response.content[0].text
            input_tok = getattr(response.usage, 'input_tokens', 0)
            output_tok = getattr(response.usage, 'output_tokens', 0)
            logger.info(f"Risposta ricevuta: {len(text)} car, tokens={input_tok+output_tok}")
            return {"text": text, "input_tokens": input_tok, "output_tokens": output_tok, "model": model}
        except Exception as e:
            logger.error(f"Errore tentativo {attempt}: {e}")
            if attempt < MAX_RETRIES:
                wait = RETRY_DELAY * attempt
                logger.info(f"Retry tra {wait}s...")
                time.sleep(wait)
            else:
                logger.error(f"Fallito dopo {MAX_RETRIES} tentativi")
                return f"[ERRORE: Sezione non generata dopo {MAX_RETRIES} tentativi. Errore: {e}]"


def generate_section(section: dict, system_prompt: str, ctx: dict, data_map: dict) -> dict:
    """Genera una singola sezione del report."""
    section_id = section["id"]
    logger.info(f"Generazione sezione: {section_id}")

    # Carica il prompt template
    prompt_template = _load_prompt(f"{section_id}.md")

    # Ottieni i dati specifici per questa sezione
    data_fn = data_map.get(section_id)
    if data_fn:
        section_data = data_fn(ctx)
    else:
        section_data = "Nessun dato specifico disponibile."

    # Sostituisci il placeholder con i dati reali
    user_prompt = prompt_template.replace("{dati_sezione}", section_data)

    # Chiama Claude
    result = call_claude(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=section["max_tokens"],
        model_type=section.get("model", "standard"),
    )
    if isinstance(result, dict):
        text = result["text"]
        _tokens = {"input": result.get("input_tokens", 0), "output": result.get("output_tokens", 0), "model": result.get("model", "")}
    else:
        text = result
        _tokens = {"input": 0, "output": 0, "model": ""}

    return {"id": section_id, "text": text, "_tokens": _tokens}


def generate_all_sections(ctx: dict, data_map: dict) -> list:
    """Genera tutte le sezioni del report in sequenza."""
    system_prompt = _load_system_prompt()
    results = []

    for section in SECTIONS:
        result = generate_section(section, system_prompt, ctx, data_map)
        results.append(result)
        logger.info(f"Sezione {result['id']} completata ({len(result['text'])} chars)")
        # Pausa tra le chiamate per evitare rate limiting
        time.sleep(1)

    return results


def load_static_content() -> str:
    """Carica il contenuto statico 'Chi e DigIdentity'."""
    try:
        return _load_prompt("static_chi_siamo.md")
    except FileNotFoundError:
        logger.warning("static_chi_siamo.md non trovato, uso placeholder")
        return "## Chi e DigIdentity Agency\n\nDigIdentity Agency e la prima agenzia italiana specializzata in diagnosi digitale automatizzata per attivita locali."


def assemble_premium_report(sections: list, ctx: dict) -> str:
    """Assembla tutte le sezioni in un unico documento markdown."""
    report_parts = []

    # Header
    report_parts.append(f"# DIAGNOSI DIGITALE PREMIUM")
    report_parts.append(f"## {ctx['nome_attivita']}")
    report_parts.append(f"**{ctx['citta']}** | **{ctx['data_odierna']}**")
    report_parts.append(f"**Punteggio DigIdentity: {ctx['punteggio_globale']}/100**")
    report_parts.append("")
    report_parts.append("---")
    report_parts.append("")

    # Sezioni generate da Claude
    for section in sections:
        report_parts.append(section["text"])
        report_parts.append("")
        report_parts.append("---")
        report_parts.append("")

    # Contenuto statico
    static = load_static_content()
    report_parts.append(static)
    report_parts.append("")
    report_parts.append("---")
    report_parts.append("")

    # Footer
    report_parts.append("*Questa diagnosi e stata generata da DigIdentity Engine™ — il primo sistema italiano di diagnosi digitale automatizzata con intelligenza artificiale per attivita locali.*")
    report_parts.append("")
    report_parts.append(f"*Report generato il {ctx['data_odierna']} per {ctx['nome_attivita']}*")

    return "\n".join(report_parts)
