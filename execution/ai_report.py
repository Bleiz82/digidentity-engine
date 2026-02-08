"""
DigIdentity Engine — Generazione report AI con Claude.

Genera report di diagnosi digitale utilizzando i dati di scraping
e i prompt specifici in directives/prompts/.
"""

import json
import logging
from pathlib import Path
from typing import Any

import anthropic

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "directives" / "prompts"


def load_prompt(prompt_name: str) -> str:
    """Carica un prompt dalla directory directives/prompts/."""
    prompt_path = PROMPTS_DIR / f"{prompt_name}.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt non trovato: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")


def generate_free_report(scraping_data: dict[str, Any]) -> str:
    """
    Genera il report gratuito di diagnosi digitale.
    Restituisce il report in formato Markdown.
    """
    company_name = scraping_data.get("company_name", "Azienda")
    logger.info(f"Generazione report FREE per {company_name}")

    system_prompt = load_prompt("free_report_system")
    user_prompt = load_prompt("free_report_user")

    # Inietta i dati di scraping nel prompt utente
    user_message = user_prompt.replace(
        "{{SCRAPING_DATA}}", json.dumps(scraping_data, indent=2, ensure_ascii=False)
    ).replace(
        "{{COMPANY_NAME}}", company_name
    ).replace(
        "{{WEBSITE_URL}}", scraping_data.get("website_url", "N/D")
    )

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
        temperature=0.3,
    )

    report_text = response.content[0].text
    logger.info(
        f"Report FREE generato per {company_name}: "
        f"{len(report_text)} caratteri, "
        f"input_tokens={response.usage.input_tokens}, "
        f"output_tokens={response.usage.output_tokens}"
    )
    return report_text


def generate_premium_report(scraping_data: dict[str, Any], free_report: str = "") -> str:
    """
    Genera il report premium completo (40-50 pagine).
    Include piano strategico, calendario editoriale, preventivo.
    Restituisce il report in formato Markdown.
    """
    company_name = scraping_data.get("company_name", "Azienda")
    logger.info(f"Generazione report PREMIUM per {company_name}")

    system_prompt = load_prompt("premium_report_system")
    user_prompt = load_prompt("premium_report_user")

    user_message = user_prompt.replace(
        "{{SCRAPING_DATA}}", json.dumps(scraping_data, indent=2, ensure_ascii=False)
    ).replace(
        "{{COMPANY_NAME}}", company_name
    ).replace(
        "{{WEBSITE_URL}}", scraping_data.get("website_url", "N/D")
    ).replace(
        "{{FREE_REPORT}}", free_report or "Non disponibile"
    )

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    # Il report premium richiede più token e più sezioni.
    # Usiamo una strategia multi-call per generare le diverse sezioni.
    sections = []

    # ── PARTE 1: Analisi e diagnosi (sezioni 1-5) ──
    part1_prompt = user_message + "\n\n**ISTRUZIONE: Genera le PARTI 1-5 del report (dall'Executive Summary fino all'Analisi SEO/SEM inclusa).**"
    resp1 = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=16000,
        system=system_prompt,
        messages=[{"role": "user", "content": part1_prompt}],
        temperature=0.25,
    )
    sections.append(resp1.content[0].text)
    logger.info(f"Premium parte 1 generata: {resp1.usage.output_tokens} tokens")

    # ── PARTE 2: Social, Reputazione, Competitor (sezioni 6-9) ──
    part2_prompt = (
        user_message
        + f"\n\n**Ecco la PARTE 1 già generata:**\n{sections[0][:3000]}...\n\n"
        + "**ISTRUZIONE: Genera le PARTI 6-9 del report (Analisi Social Media, Reputazione Online, Analisi Competitiva, Strategia Digitale). Non ripetere le sezioni precedenti.**"
    )
    resp2 = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=16000,
        system=system_prompt,
        messages=[{"role": "user", "content": part2_prompt}],
        temperature=0.25,
    )
    sections.append(resp2.content[0].text)
    logger.info(f"Premium parte 2 generata: {resp2.usage.output_tokens} tokens")

    # ── PARTE 3: Piano operativo, calendario, preventivo (sezioni 10-14) ──
    part3_prompt = (
        user_message
        + "\n\n**ISTRUZIONE: Genera le PARTI 10-14 del report (Calendario Editoriale 3 mesi dettagliato, Piano Budget e ROI, Roadmap implementazione, Preventivo dettagliato, Conclusioni). Non ripetere le sezioni precedenti.**"
    )
    resp3 = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=16000,
        system=system_prompt,
        messages=[{"role": "user", "content": part3_prompt}],
        temperature=0.25,
    )
    sections.append(resp3.content[0].text)
    logger.info(f"Premium parte 3 generata: {resp3.usage.output_tokens} tokens")

    full_report = "\n\n---\n\n".join(sections)

    logger.info(
        f"Report PREMIUM completo per {company_name}: "
        f"{len(full_report)} caratteri"
    )
    return full_report
