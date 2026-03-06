"""\nDigIdentity Premium — AI Report Generator\nGenera il report premium chiamando Claude sezione per sezione.\n"""
import os
import time
import logging
from pathlib import Path
from anthropic import Anthropic

logger = logging.getLogger(__name__)

CLAUDE_MODEL_STANDARD = "claude-sonnet-4-6"
CLAUDE_MODEL_PREMIUM = "claude-opus-4-6"

PROMPTS_DIR = Path(__file__).parent.parent / "directives" / "prompts" / "premium"

SECTIONS = [
    {"id": "01_apertura_dashboard", "max_tokens": 4000, "model": "standard"},
    {"id": "02_sito_web", "max_tokens": 6000, "model": "standard"},
    {"id": "03_pagespeed_seo", "max_tokens": 6000, "model": "standard"},
    {"id": "04_keyword", "max_tokens": 5000, "model": "standard"},
    {"id": "05_google_business_reputazione", "max_tokens": 7000, "model": "standard"},
    {"id": "06_competitor", "max_tokens": 7000, "model": "standard"},
    {"id": "07_social_bio", "max_tokens": 6000, "model": "standard"},
    {"id": "08_branding_ai", "max_tokens": 6000, "model": "standard"},
    {"id": "geo_ai_visibility", "max_tokens": 4500, "model": "standard"},
    {"id": "09_ads", "max_tokens": 5000, "model": "standard"},
    {"id": "10_piano_90_giorni", "max_tokens": 12000, "model": "standard"},
    {"id": "11_relazione_punteggio", "max_tokens": 9000, "model": "standard"},
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


def _calc_cost(input_tok: int, output_tok: int, cache_read: int, cache_write: int, model: str) -> float:
    """Calcolo costo preciso con prompt caching."""
    if "opus" in model:
        p_in, p_out = 15.0/1_000_000, 75.0/1_000_000
        p_cw, p_cr  = 18.75/1_000_000, 1.50/1_000_000
    else:
        p_in, p_out = 3.0/1_000_000, 15.0/1_000_000
        p_cw, p_cr  = 3.75/1_000_000, 0.30/1_000_000
    regular = max(0, input_tok - cache_read - cache_write)
    return regular * p_in + cache_write * p_cw + cache_read * p_cr + output_tok * p_out


def call_claude(system_prompt: str, user_prompt: str, max_tokens: int, model_type: str = "standard") -> dict:
    """Chiama Claude con prompt caching sul system prompt e retry/backoff."""
    client = _get_client()
    model = CLAUDE_MODEL_PREMIUM if model_type == "premium" else CLAUDE_MODEL_STANDARD

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Chiamata Claude ({model}) - tentativo {attempt}")
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                messages=[{"role": "user", "content": user_prompt}],
                extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"}
            )
            text = response.content[0].text
            usage = response.usage
            input_tok  = getattr(usage, "input_tokens", 0)
            output_tok = getattr(usage, "output_tokens", 0)
            cache_read  = getattr(usage, "cache_read_input_tokens", 0)
            cache_write = getattr(usage, "cache_creation_input_tokens", 0)
            cost = _calc_cost(input_tok, output_tok, cache_read, cache_write, model)
            logger.info(
                f"✅ Claude OK | in={input_tok} out={output_tok} "
                f"cache_read={cache_read} cache_write={cache_write} cost=${cost:.4f}"
            )
            return {
                "text": text,
                "input_tokens": input_tok,
                "output_tokens": output_tok,
                "cache_read_tokens": cache_read,
                "cache_write_tokens": cache_write,
                "model": model,
                "cost_usd": cost
            }
        except Exception as e:
            logger.error(f"Errore tentativo {attempt}: {e}")
            if attempt < MAX_RETRIES:
                wait = RETRY_DELAY * attempt
                logger.info(f"Retry tra {wait}s...")
                time.sleep(wait)
            else:
                logger.error(f"Fallito dopo {MAX_RETRIES} tentativi")
                return {
                    "text": f"[ERRORE: Sezione non generata dopo {MAX_RETRIES} tentativi. Errore: {e}]",
                    "input_tokens": 0, "output_tokens": 0,
                    "cache_read_tokens": 0, "cache_write_tokens": 0,
                    "model": model, "cost_usd": 0
                }


def generate_section(section: dict, system_prompt: str, ctx: dict, data_map: dict, prev_context: str = "") -> dict:
    """Genera una singola sezione del report con contesto delle sezioni precedenti."""
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

    # Aggiungi contesto sezioni precedenti se disponibile
    if prev_context:
        user_prompt = prev_context + "\n\n" + user_prompt

    # Chiama Claude
    result = call_claude(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=section["max_tokens"],
        model_type=section.get("model", "standard"),
    )
    if isinstance(result, dict):
        text = result["text"]
        _tokens = {
            "input": result.get("input_tokens", 0),
            "output": result.get("output_tokens", 0),
            "cache_read": result.get("cache_read_tokens", 0),
            "cache_write": result.get("cache_write_tokens", 0),
            "model": result.get("model", ""),
            "cost_usd": result.get("cost_usd", 0)
        }
    else:
        text = result
        _tokens = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0, "model": "", "cost_usd": 0}

    return {"id": section_id, "text": text, "_tokens": _tokens}


def generate_all_sections(ctx: dict, data_map: dict) -> list:
    """Genera tutte le sezioni con contesto progressivo delle precedenti."""
    system_prompt = _load_system_prompt()
    results = []
    running_summary = []

    for section in SECTIONS:
        # Costruisci contesto dalle ultime 2 sezioni generate
        prev_context = ""
        if running_summary:
            prev_context = "---\nRIFERIMENTO SEZIONI PRECEDENTI (non ripetere, usa per coerenza):\n"
            prev_context += "\n".join(running_summary[-2:])
            prev_context += "\n---\n"

        result = generate_section(section, system_prompt, ctx, data_map, prev_context)
        results.append(result)

        # Salva sintesi breve per le sezioni successive
        summary_line = f"[{section['id']}]: {result['text'][:200].strip().replace(chr(10), ' ')}..."
        running_summary.append(summary_line)

        _tok = result["_tokens"]
        logger.info(
            f"✅ Sezione {result['id']} | {len(result['text'])} chars | "
            f"in={_tok.get('input',0)} out={_tok.get('output',0)} "
            f"cache_r={_tok.get('cache_read',0)} cost=${_tok.get('cost_usd',0):.4f}"
        )
        time.sleep(1)

    total_cost = sum(s["_tokens"].get("cost_usd", 0) for s in results)
    logger.info(f"💰 Costo totale report premium: ${total_cost:.4f}")
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
