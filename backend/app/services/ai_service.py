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
    print(f"   Max tokens: 8000")

    # Carica prompt da file
    prompt_path = os.path.join(os.path.dirname(__file__), "../../../directives/prompts/free-report-prompt.md")
    if not os.path.exists(prompt_path):
        prompt_path = "c:/Users/stefa/Desktop/digidentity-projects/directives/prompts/free-report-prompt.md"

    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()

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
            max_tokens=8000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        content = message.content[0].text
        sections = extract_json_from_text(content)

        expected_keys = [f"section_{i}" for i in range(1, 6)]
        for key in expected_keys:
            if key not in sections:
                sections[key] = f"<div><h2>Sezione non disponibile</h2><p>Questa sezione non è stata generata correttamente.</p></div>"

        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens
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
    Usa chiamate multiple per gestire la lunghezza.
    """
    settings = get_settings()

    print(f"[AI] Generazione report PREMIUM AI con Claude...")
    print(f"   Modello: {settings.anthropic_model}")
    print(f"   Target: 40-50 pagine, 11 sezioni (4 chiamate)")

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

    data_json = json.dumps(input_data, ensure_ascii=False, indent=2)

    # Definisci i gruppi di sezioni per ogni chiamata
    call_groups = [
        {
            "sections": ["section_1", "section_2", "section_3"],
            "instruction": """Genera le SEZIONI 1, 2 e 3 del report premium:
- section_1: Executive Summary (2 pagine) — "La Tua Attività in Numeri: Dove Sei e Dove Puoi Arrivare"
- section_2: Analisi Identità Digitale (4 pagine) — "Il Tuo Brand Online: Come Ti Percepisce Chi Ti Cerca"
- section_3: Audit Sito Web Completo (6 pagine) — "Il Tuo Sito Web: Analisi Pagina per Pagina"

Ogni sezione deve essere LUNGA e DETTAGLIATA. Minimo 1500 parole per sezione. Usa dati concreti, tabelle HTML, confronti con competitor."""
        },
        {
            "sections": ["section_4", "section_5", "section_6"],
            "instruction": """Genera le SEZIONI 4, 5 e 6 del report premium:
- section_4: Analisi SEO e Posizionamento (6 pagine) — "Farsi Trovare su Google: La Tua Situazione e la Strategia"
- section_5: Google My Business Audit (4 pagine) — "La Tua Vetrina su Google: Analisi Completa della Scheda"
- section_6: Social Media Audit (5 pagine) — "I Tuoi Social: Analisi, Strategia e Calendario"

Ogni sezione deve essere LUNGA e DETTAGLIATA. Minimo 1500 parole per sezione. Usa dati concreti, tabelle HTML, confronti con competitor."""
        },
        {
            "sections": ["section_7", "section_8"],
            "instruction": """Genera le SEZIONI 7 e 8 del report premium:
- section_7: Analisi Concorrenza (4 pagine) — "La Mappa Competitiva: Chi Sono i Tuoi Veri Competitor Online" con matrice SWOT
- section_8: Opportunità AI e Automazioni (4 pagine) — "Intelligenza Artificiale e Automazioni: Il Tuo Vantaggio Competitivo del 2026"

La sezione 8 è il DIFFERENZIANTE di DigIdentity Agency. Deve essere la sezione più innovativa e sorprendente del report.
Ogni sezione deve essere LUNGA e DETTAGLIATA. Minimo 1500 parole per sezione."""
        },
        {
            "sections": ["section_9", "section_10", "section_11"],
            "instruction": """Genera le SEZIONI 9, 10 e 11 del report premium:
- section_9: Piano Strategico 90 Giorni (5 pagine) — "Il Tuo Piano d'Azione: 90 Giorni per Trasformare la Tua Presenza Online" con calendario settimanale dettagliato
- section_10: Quanto Ti Costa Restare Fermo (3 pagine) — Calcolo concreto dei clienti e revenue persi ogni mese + come misurare i progressi con 5 KPI semplici
- section_11: Il Prossimo Passo (2 pagine) — Proposta consulenza strategica DigIdentity Agency a 199€ (45 minuti), con firma Stefano Corda

NON suggerire al cliente di fare da solo. Il report deve portare naturalmente alla consulenza con DigIdentity Agency.
Ogni sezione deve essere DETTAGLIATA. Contatti: info@digidentityagency.it, +39 392 199 0215"""
        }
    ]

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    all_sections = {}
    total_input_tokens = 0
    total_output_tokens = 0

    for i, group in enumerate(call_groups):
        section_keys = group["sections"]
        section_json_keys = ', '.join([f'"{k}": "<div>...contenuto HTML lungo e dettagliato...</div>"' for k in section_keys])

        user_message = f"""Genera le seguenti sezioni del report Diagnosi Strategica Digitale PREMIUM per questa azienda.

DATI INPUT:
{data_json}

{group["instruction"]}

REGOLE:
- HTML pulito e semantico con classi CSS
- Colori brand: Rosso #F90100, Nero #000000, Grigio #444444
- Tono: professionale ma accessibile, come spiegare a un imprenditore non tecnico
- OGNI affermazione deve essere basata su dati reali forniti
- Includi tabelle HTML, liste, box evidenziati dove appropriato
- Ogni sezione deve essere LUNGA e SOSTANZIOSA (minimo 1500 parole ciascuna)

IMPORTANTE: Rispondi SOLO con JSON valido. Formato esatto:
{{{{{section_json_keys}}}}}
"""

        print(f"   [CALL {i+1}/4] Generazione sezioni {', '.join(section_keys)}...")

        try:
            message = client.messages.create(
                model=settings.anthropic_model,
                max_tokens=16000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )

            content = message.content[0].text
            parsed = extract_json_from_text(content)

            for key in section_keys:
                if key in parsed and parsed[key]:
                    all_sections[key] = parsed[key]
                    print(f"      ✅ {key}: {len(parsed[key])} caratteri")
                else:
                    all_sections[key] = f"<div><h2>Sezione non disponibile</h2><p>Questa sezione non è stata generata correttamente.</p></div>"
                    print(f"      ❌ {key}: non generata")

            total_input_tokens += message.usage.input_tokens
            total_output_tokens += message.usage.output_tokens
            print(f"      Tokens: {message.usage.input_tokens} in / {message.usage.output_tokens} out")

        except Exception as e:
            print(f"      ❌ Errore call {i+1}: {e}")
            for key in section_keys:
                all_sections[key] = f"<div><h2>Sezione non disponibile</h2><p>Errore nella generazione: {str(e)}</p></div>"

    # Calcola costo totale
    cost = (total_input_tokens / 1_000_000 * 3.0) + (total_output_tokens / 1_000_000 * 15.0)

    print(f"\n[OK] Report PREMIUM AI completato")
    print(f"   Sezioni generate: {sum(1 for k, v in all_sections.items() if 'non disponibile' not in v)}/11")
    print(f"   Input tokens totali: {total_input_tokens}")
    print(f"   Output tokens totali: {total_output_tokens}")
    print(f"   Costo stimato totale: ${cost:.4f}")

    return {
        "success": True,
        "sections": all_sections,
        "metadata": {
            "model": settings.anthropic_model,
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "total_tokens": total_input_tokens + total_output_tokens,
            "cost_usd": round(cost, 4)
        }
    }