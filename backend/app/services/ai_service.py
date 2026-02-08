"""
DigIdentity Engine — AI Service
Generazione report con Claude API (Anthropic).
Versione 3.0 — 11 chiamate singole per premium, token calibrati.
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


def extract_html_from_text(text: str) -> str:
    """
    Estrae contenuto HTML dalla risposta Claude.
    Gestisce i casi in cui Claude wrappa l'HTML in backtick o aggiunge testo.
    """
    # Tentativo 1: cerca HTML tra backtick ```html ... ```
    match = re.search(r'```(?:html)?\s*([\s\S]*?)\s*```', text)
    if match:
        return match.group(1).strip()

    # Tentativo 2: cerca il primo <div e l'ultimo </div>
    first_div = text.find('<div')
    if first_div == -1:
        first_div = text.find('<section')
    if first_div == -1:
        first_div = text.find('<h')

    if first_div != -1:
        return text[first_div:].strip()

    # Tentativo 3: restituisci tutto il testo (Claude ha generato HTML puro)
    return text.strip()


async def generate_free_report_ai(
    lead_data: Dict[str, Any],
    analysis_data: Dict[str, Any],
    scores: Dict[str, int]
) -> Dict[str, Any]:
    """
    Genera report gratuito (6 sezioni HTML) usando Claude API.
    Target: 8-10 pagine, 20.000-25.000 caratteri totali.
    """
    settings = get_settings()

    print(f"[AI] Generazione report GRATUITO AI con Claude...")
    print(f"   Modello: {settings.anthropic_model}")
    print(f"   Target: 8-10 pagine, 6 sezioni")

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

    data_json = json.dumps(input_data, ensure_ascii=False, indent=2)

    # ── 6 sezioni FREE, una chiamata per sezione ──
    free_sections = [
        {
            "key": "section_1",
            "max_tokens": 4000,
            "instruction": """Genera la SEZIONE 1: "La Tua Fotografia Digitale" (circa 1.5 pagine).
Contenuto: saluto personalizzato, contesto settore/città nel 2026, Score Totale con metafora concreta,
tabella riassuntiva 5 scores con emoji colorate (verde/giallo/rosso), chiusura che invita a leggere.
Genera HTML con grafici visivi per gli score: usa barre di progresso CSS colorate."""
        },
        {
            "key": "section_2",
            "max_tokens": 5000,
            "instruction": """Genera la SEZIONE 2: "Come Ti Vede il Mondo" (circa 2 pagine).
Contenuto: analisi sito web (velocità tradotta in linguaggio umano, mobile, problemi),
Google My Business (scheda, recensioni, foto, confronto competitor),
Social Media (attivi? frequenza? piattaforme giuste per il settore?).
Per ogni punto problematico, aggiungi un box "Cosa Significa Per Te" con impatto concreto sul business.
Genera HTML ricco con box colorati, icone, tabelle confronto."""
        },
        {
            "key": "section_3",
            "max_tokens": 5000,
            "instruction": """Genera la SEZIONE 3: "Tu vs I Tuoi Competitor" (circa 2 pagine).
Contenuto: domanda diretta "Quando qualcuno cerca [settore] vicino a me...",
top 3 competitor in modo narrativo (nome, rating, recensioni, posizione),
Local Pack di Google Maps spiegato con metafora,
vantaggi e punti deboli dei competitor dove il lead può superarli,
costo dell'inazione, chiusura positiva.
Genera HTML con cards per ogni competitor, barra confronto visiva."""
        },
        {
            "key": "section_4",
            "max_tokens": 5000,
            "instruction": """Genera la SEZIONE 4: "Le 5 Cose Che Puoi Fare Subito" (circa 2 pagine).
Contenuto: 5 azioni concrete ordinate per impatto/facilità.
Per ogni azione: titolo, perché è importante (dato reale), come farlo (3-4 step),
impatto stimato, difficoltà (Facile/Media/Difficile), costo (Gratuito/Basso/Medio).
Almeno 2 azioni gratuite. Per quelle complesse, far capire il valore di un professionista.
Genera HTML con cards numerate, badge difficoltà colorati, icone."""
        },
        {
            "key": "section_5",
            "max_tokens": 3000,
            "instruction": """Genera la SEZIONE 5: "Quanto Ti Costa Non Fare Nulla" (circa 1.5 pagine).
Contenuto: calcolo concreto di cosa perde ogni mese restando fermo.
Clienti persi, fatturato mancato, vantaggio competitor che cresce.
Usa numeri specifici basati sui dati del settore e della città.
NON essere catastrofista ma realistico. Chiudi con speranza.
Genera HTML con box rosso "costo inazione", grafico barre semplice CSS."""
        },
        {
            "key": "section_6",
            "max_tokens": 3500,
            "instruction": """Genera la SEZIONE 6: "Vuoi il Quadro Completo?" (circa 1.5 pagine).
Contenuto: riassunto situazione in 3 frasi, perché serve un professionista (metafora mestiere),
cosa rende DigIdentity diversa (AI e automazioni come vantaggio, non come prodotto tech),
Diagnosi Premium a 99€ come passo logico (lista cosa include in più),
valore percepito "costerebbe 500-1000€, la offriamo a 99€",
CTA finale, firma Stefano Corda, contatti.
NON suggerire di andare da altre agenzie. Il report deve portare a DigIdentity.
Genera HTML con box CTA rosso prominente, lista benefici premium."""
        }
    ]

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    all_sections = {}
    total_input_tokens = 0
    total_output_tokens = 0

    for i, section in enumerate(free_sections):
        key = section["key"]
        user_message = f"""Genera questa sezione del report Diagnosi Strategica Digitale GRATUITA.

DATI AZIENDA:
{data_json}

{section["instruction"]}

REGOLE IMPORTANTI:
- HTML pulito e semantico, NO tag <style> o <script>
- Usa classi CSS: .score-badge, .highlight-box, .cta-box, .progress-bar
- Colori brand: Rosso #F90100, Nero #000000, Grigio #444444
- Tono: semplice, diretto, come spiegare a un imprenditore non tecnico
- OGNI affermazione basata su dati reali forniti
- Includi grafici visivi con CSS inline dove indicato (barre progresso, badge score)
- La sezione deve essere SOSTANZIOSA e ben formattata

FORMATO OUTPUT: Rispondi SOLO con il codice HTML della sezione, senza wrapping JSON, senza backtick, senza commenti. Solo HTML puro che inizia con <div>."""

        print(f"   [CALL {i+1}/6] Generazione {key}...")

        try:
            message = client.messages.create(
                model=settings.anthropic_model,
                max_tokens=section["max_tokens"],
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )

            content = message.content[0].text
            html_content = extract_html_from_text(content)

            if html_content and len(html_content) > 100:
                all_sections[key] = html_content
                print(f"      ✅ {key}: {len(html_content)} caratteri")
            else:
                all_sections[key] = f'<div><h2>Sezione non disponibile</h2><p>Questa sezione non è stata generata correttamente.</p></div>'
                print(f"      ❌ {key}: contenuto troppo corto ({len(html_content)} car)")

            total_input_tokens += message.usage.input_tokens
            total_output_tokens += message.usage.output_tokens
            print(f"      Tokens: {message.usage.input_tokens} in / {message.usage.output_tokens} out")

        except Exception as e:
            print(f"      ❌ Errore {key}: {e}")
            all_sections[key] = f'<div><h2>Sezione non disponibile</h2><p>Errore nella generazione: {str(e)}</p></div>'

    # Calcola costo totale
    cost = (total_input_tokens / 1_000_000 * 3.0) + (total_output_tokens / 1_000_000 * 15.0)

    generated_count = sum(1 for k, v in all_sections.items() if 'non disponibile' not in v)
    total_chars = sum(len(v) for v in all_sections.values())

    print(f"\n[OK] Report GRATUITO AI completato")
    print(f"   Sezioni generate: {generated_count}/6")
    print(f"   Caratteri totali: {total_chars}")
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


async def generate_premium_report_ai(
    lead_data: Dict[str, Any],
    free_analysis: Dict[str, Any],
    premium_analysis: Dict[str, Any],
    scores: Dict[str, int]
) -> Dict[str, Any]:
    """
    Genera report premium (40-50 pagine HTML, 11 sezioni) usando Claude API.
    UNA chiamata per sezione — nessuna sezione persa.
    """
    settings = get_settings()

    print(f"[AI] Generazione report PREMIUM AI con Claude...")
    print(f"   Modello: {settings.anthropic_model}")
    print(f"   Target: 40-50 pagine, 11 sezioni (11 chiamate singole)")

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

    # ── 11 sezioni PREMIUM, una chiamata per sezione ──
    premium_sections = [
        {
            "key": "section_1",
            "max_tokens": 6000,
            "instruction": """Genera la SEZIONE 1: EXECUTIVE SUMMARY — "La Tua Attività in Numeri: Dove Sei e Dove Puoi Arrivare" (3-4 pagine).

Contenuto richiesto:
- Saluto personalizzato e contesto azienda/settore/città
- Score Digitale Complessivo con GRAFICO VISIVO: barra di progresso CSS per ogni area (sito, SEO, GMB, social, competitivo) con colori verde/giallo/rosso
- Per ogni score: spiegazione in 2-3 righe di cosa significa concretamente
- "La Situazione in Sintesi": paragrafo narrativo che racconta la storia digitale dell'azienda come se parlassi con un amico imprenditore
- "Il Potenziale": stima concreta di cosa può ottenere (nuovi clienti/mese, fatturato aggiuntivo) con i calcoli spiegati
- "La Roadmap": le 3 priorità strategiche del report (anteprima)
- "I 3 Numeri Che Contano": i dati più impattanti presentati in box grandi
- "Cosa Troverai nei Prossimi Capitoli": lista visiva delle 10 sezioni successive

Genera HTML ricco con: barre di progresso CSS colorate, box numerici grandi, cards con icone, tabelle confronto. Ogni dato deve avere un riferimento concreto ai dati di analisi forniti."""
        },
        {
            "key": "section_2",
            "max_tokens": 8000,
            "instruction": """Genera la SEZIONE 2: ANALISI IDENTITÀ DIGITALE — "Il Tuo Brand Online: Come Ti Percepisce Chi Ti Cerca" (4-5 pagine).

Contenuto richiesto:
- Coerenza visiva: analisi logo, colori, messaggi tra sito, GMB e social. Tabella confronto visiva
- Naming e messaging: il nome dell'azienda è efficace? SEO-friendly? Memorabile? Tabella valutazione
- Primo impatto: cosa vede chi cerca il nome azienda su Google? Screenshot testuale dei risultati
- Confronto competitor: come si posizionano i competitor in termini di brand? Tabella con nome, rating, posizionamento
- Caso pratico: prendi il competitor più forte e analizza cosa fa meglio in termini di identità digitale
- Raccomandazioni specifiche per allineare l'identità digitale: azioni concrete numerate

Genera HTML con: tabelle comparative, box valutazione con score, cards competitor, checklist visive (✅/❌/⚠️)."""
        },
        {
            "key": "section_3",
            "max_tokens": 10000,
            "instruction": """Genera la SEZIONE 3: AUDIT SITO WEB COMPLETO — "Il Tuo Sito Web: Analisi Pagina per Pagina" (6-7 pagine).

Contenuto richiesto:
- Performance overview: PageSpeed score desktop e mobile con BARRE DI PROGRESSO CSS colorate
- Core Web Vitals spiegati come a un non tecnico: LCP (tempo caricamento), FID/INP (reattività), CLS (stabilità visiva). Per ognuno: valore attuale, soglia Google, cosa significa per i visitatori
- Analisi pagina per pagina: per ogni pagina analizzata dal deep scraping, una mini-scheda con: URL, titolo, meta description, conteggio parole, H1, immagini con/senza alt, schema markup
- SEO tecnico on-page: title tags, meta descriptions, heading structure, immagini alt, internal linking. Per ogni elemento: stato attuale + come dovrebbe essere
- Mobile responsiveness: come appare su telefono? Problemi trovati?
- Sicurezza: SSL, GDPR/cookie banner, headers sicurezza
- Tecnologie rilevate: lista con commento su ciascuna
- Score complessivo sito con barra di progresso grande

Genera HTML con: barre progresso CSS per ogni metrica, tabelle analisi pagine, box verdi (ok) e rossi (problemi), grafici a barre CSS per confronto desktop/mobile."""
        },
        {
            "key": "section_4",
            "max_tokens": 10000,
            "instruction": """Genera la SEZIONE 4: ANALISI SEO E POSIZIONAMENTO — "Farsi Trovare su Google: La Tua Situazione e la Strategia" (6-7 pagine).

Contenuto richiesto:
- Stato attuale su Google: per quali ricerche appari? Per quali NO? Box visivo "TROVATO/NON TROVATO"
- Analisi keyword: tabella delle keyword strategiche per il settore/città con volume ricerca stimato, difficoltà, posizione attuale, chi è primo
- Keyword opportunity: keyword a bassa competizione dove posizionarsi rapidamente
- Local SEO: analisi Local Pack (mappa Google), chi ci appare e perché, come entrarci
- Strategia SEO 90 giorni: roadmap mese per mese con azioni specifiche
- Contenuti strategici: per ogni keyword target, che tipo di contenuto creare (pagina servizi, articolo blog, landing page)
- Potenziale di traffico: stima visite mensili raggiungibili con calcoli

Genera HTML con: tabelle keyword colorate, box "TROVATO/NON TROVATO", roadmap visiva con timeline CSS, grafici barre per volumi ricerca. Usa dati REALI dalle analisi SERP fornite."""
        },
        {
            "key": "section_5",
            "max_tokens": 7000,
            "instruction": """Genera la SEZIONE 5: GOOGLE MY BUSINESS AUDIT — "La Tua Vetrina su Google: Analisi Completa della Scheda" (4-5 pagine).

Contenuto richiesto:
- Stato attuale della scheda: presente/assente, completezza %, categoria, descrizione, foto, orari
- Analisi recensioni: numero, rating medio, trend, analisi sentiment delle ultime recensioni se disponibili
- Confronto con competitor: tabella con rating, numero recensioni, completezza per ogni competitor
- Strategia recensioni: piano per ottenere più recensioni positive (template richiesta, timing, follow-up)
- Ottimizzazione scheda: checklist completa di cosa migliorare con priorità
- Google Posts: strategia di pubblicazione settimanale con esempi di post
- Q&A: domande frequenti da aggiungere alla scheda

Se la scheda NON esiste: spiegare perché è critico con dati concreti (% ricerche locali, impatto su visibilità) e guida passo-passo per crearla.

Genera HTML con: checklist con ✅/❌, barra completezza scheda, tabella confronto competitor, cards per le azioni prioritarie."""
        },
        {
            "key": "section_6",
            "max_tokens": 8000,
            "instruction": """Genera la SEZIONE 6: SOCIAL MEDIA AUDIT — "I Tuoi Social: Analisi, Strategia e Calendario" (5-6 pagine).

Contenuto richiesto:
- Stato attuale per piattaforma: tabella con piattaforma, presente sì/no, follower, frequenza post, ultimo post, engagement
- Analisi per piattaforma: per ogni social rilevante al settore, analisi dettagliata con raccomandazioni
- Piattaforme prioritarie: quali usare e perché, basato sul settore specifico
- Strategia contenuti per piattaforma: tipo di contenuti, frequenza, orari migliori
- Calendario editoriale 4 settimane: tabella dettagliata con giorno, piattaforma, tipo contenuto, tema, orario pubblicazione
- Esempi di post: 3-4 esempi concreti di post che l'azienda potrebbe pubblicare
- Strumenti consigliati: tool per scheduling, creazione contenuti, analytics

Se NON ha social: spiegare l'impatto con dati del settore e piano di lancio step-by-step.

Genera HTML con: tabelle per calendario editoriale, cards per ogni piattaforma, box con esempi post, timeline di lancio."""
        },
        {
            "key": "section_7",
            "max_tokens": 8000,
            "instruction": """Genera la SEZIONE 7: ANALISI CONCORRENZA — "La Mappa Competitiva: Chi Sono i Tuoi Veri Competitor Online" (5-6 pagine).

Contenuto richiesto:
- Top 5 competitor: per ognuno una card dettagliata con nome, rating, recensioni, posizione SERP, punti di forza e debolezza
- Matrice comparativa: tabella grande con tutte le metriche (rating, recensioni, presenza social, SEO, sito) per ogni competitor vs l'azienda
- Analisi SWOT digitale: Strengths, Weaknesses, Opportunities, Threats in formato visivo con 4 box colorati
- Gap analysis: dove l'azienda è indietro e dove è avanti rispetto ai competitor
- Strategia di differenziazione: come posizionarsi in modo unico (focus su AI e automazioni come differenziante)
- Azioni concrete per superare ogni competitor: per i top 3, una strategia specifica

Genera HTML con: cards competitor con badge posizione (🥇🥈🥉), tabella matrice grande, 4 box SWOT colorati (verde/giallo/blu/rosso), barre confronto visive."""
        },
        {
            "key": "section_8",
            "max_tokens": 7000,
            "instruction": """Genera la SEZIONE 8: OPPORTUNITÀ AI E AUTOMAZIONI — "Intelligenza Artificiale e Automazioni: Il Tuo Vantaggio Competitivo del 2026" (4-5 pagine).

QUESTA È LA SEZIONE DIFFERENZIANTE DI DIGIDENTITY AGENCY.

Contenuto richiesto:
- Introduzione: cos'è l'AI applicata al business locale, spiegata con metafore semplici ("è come avere un dipendente instancabile che lavora 24/7")
- Opportunità specifiche per il settore dell'azienda: 5-7 automazioni concrete che può implementare
  Per ognuna: cosa fa, quanto tempo risparmia, quanto costa, ROI stimato
  Esempi: chatbot per appuntamenti, risposte automatiche recensioni, generazione contenuti social, email marketing automatico, report clienti automatici
- Casi d'uso pratici: "Un [settore] a [città] che usa l'AI per..." — 2-3 mini storie concrete
- Il vantaggio competitivo: perché implementare AI ora dà un vantaggio enorme sui competitor che non lo fanno
- DigIdentity come partner: come DigIdentity Agency implementa queste soluzioni (senza essere troppo commerciale, ma facendo capire che è il partner giusto)

NON parlare di AI come tecnologia astratta. Parla di RISULTATI CONCRETI: tempo risparmiato, clienti in più, costi ridotti.

Genera HTML con: cards per ogni automazione, box ROI, timeline implementazione, icone per ogni beneficio."""
        },
        {
            "key": "section_9",
            "max_tokens": 10000,
            "instruction": """Genera la SEZIONE 9: PIANO STRATEGICO 90 GIORNI — "Il Tuo Piano d'Azione: 90 Giorni per Trasformare la Tua Presenza Online" (6-7 pagine).

Contenuto richiesto:
- Principi guida del piano: 4 principi in box visivi (Prima le fondamenta, Massimo impatto/minimo sforzo, Tutto misurabile, Realistico)
- MESE 1 — LE FONDAMENTA (2 pagine):
  Settimana 1: azioni specifiche giorno per giorno con tempo richiesto
  Settimana 2: azioni specifiche
  Settimana 3: azioni specifiche
  Settimana 4: azioni specifiche + review
  KPI fine mese 1 con target numerici
- MESE 2 — LA CRESCITA (1.5 pagine):
  Settimane 5-6: azioni quindicinali
  Settimane 7-8: azioni quindicinali + intro automazioni AI
  KPI fine mese 2
- MESE 3 — L'ACCELERAZIONE (1.5 pagine):
  Settimane 9-10: ottimizzazione avanzata
  Settimane 11-12: scaling e automazione
  KPI fine mese 3 + risultati attesi
- Checkpoint mensili: 5 domande per valutare i progressi
- Investimento di tempo: ore/settimana per mese con riduzione grazie all'automazione

Ogni azione deve essere CONCRETA e SPECIFICA per quell'azienda/settore/città. NO azioni generiche.

Genera HTML con: timeline visiva, cards settimanali, box KPI con target, barre progresso, checklist con ✅."""
        },
        {
            "key": "section_10",
            "max_tokens": 6000,
            "instruction": """Genera la SEZIONE 10: QUANTO TI COSTA RESTARE FERMO — "I Numeri Che Non Puoi Ignorare" (3-4 pagine).

Contenuto richiesto:
- Calcolo "costo dell'inazione": quanti clienti perde ogni mese non essendo visibile online. Usa dati concreti: volume ricerche settore/città, tasso conversione medio, valore medio cliente
- Proiezione 6-12 mesi: quanto fatturato sta perdendo rimanendo fermo. Tabella con mesi e perdita cumulativa
- Confronto investimento vs perdita: "Investire X€ al mese per recuperare Y€ di fatturato perso"
- Come misurare i progressi: 5 KPI semplici che anche un non tecnico può monitorare. Per ognuno: cosa misura, dove trovarlo, con che frequenza controllarlo, qual è il valore target
- Strumenti gratuiti di monitoraggio: Google Analytics, Search Console, GMB Insights — spiegati semplicemente

NON essere catastrofista. Sii realistico e costruttivo. Il messaggio è: "Non è troppo tardi, ma ogni mese che passa il divario cresce."

Genera HTML con: box grande rosso "costo mensile inazione", grafico barre CSS per proiezione perdite, cards KPI con icone, tabella investimento vs ritorno."""
        },
        {
            "key": "section_11",
            "max_tokens": 5000,
            "instruction": """Genera la SEZIONE 11: IL PROSSIMO PASSO — "Proposta di Collaborazione con DigIdentity Agency" (2-3 pagine).

Contenuto richiesto:
- Riassunto situazione: dove è ora l'azienda, dove può arrivare, cosa serve
- Perché DigIdentity Agency: non la solita web agency — integra AI e automazioni per risultati migliori, tempi più rapidi, costi più accessibili per le piccole attività
- LA PROPOSTA: Consulenza Strategica a 199€ (45 minuti con Stefano Corda)
  - Cosa include: revisione report insieme, priorità personalizzate, roadmap implementazione, preventivo dettagliato per ogni intervento, risposte a tutte le domande
  - Perché 199€: "Non è una vendita, è un investimento. In 45 minuti avrai chiarezza totale su cosa fare, in che ordine, con che budget, e soprattutto se ha senso lavorare insieme."
- Come prenotare: link/email/telefono
- Garanzia: "Se dopo la consulenza senti di non aver ricevuto valore, ti restituiamo i 199€. Zero rischi."
- Firma: Stefano Corda — Fondatore, DigIdentity Agency
- Contatti: info@digidentityagency.it, +39 392 199 0215, digidentityagency.it

NON suggerire al cliente di fare da solo o di andare da altri.
Il tono deve essere: "Hai visto i dati, hai capito il potenziale. Ora parliamone insieme."

Genera HTML con: box proposta grande con prezzo evidenziato, lista benefici, CTA prominente rossa, firma con contatti, garanzia in box verde."""
        }
    ]

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    all_sections = {}
    total_input_tokens = 0
    total_output_tokens = 0

    for i, section in enumerate(premium_sections):
        key = section["key"]
        user_message = f"""Genera questa sezione del report Diagnosi Strategica Digitale PREMIUM.

DATI AZIENDA:
{data_json}

{section["instruction"]}

REGOLE IMPORTANTI:
- HTML pulito e semantico, NO tag <style> o <script>
- Colori brand: Rosso #F90100, Nero #000000, Grigio #444444
- Tono: professionale ma accessibile, come spiegare a un imprenditore non tecnico. Linguaggio semplice, zero gergo. Usa metafore concrete.
- OGNI affermazione deve essere basata su dati reali forniti
- La sezione deve essere LUNGA, DETTAGLIATA e SOSTANZIOSA
- Includi elementi visivi HTML/CSS inline dove indicato: barre progresso, tabelle, box colorati, cards

FORMATO OUTPUT: Rispondi SOLO con il codice HTML della sezione, senza wrapping JSON, senza backtick, senza commenti. Solo HTML puro che inizia con <div>."""

        print(f"   [CALL {i+1}/11] Generazione {key}...")

        try:
            message = client.messages.create(
                model=settings.anthropic_model,
                max_tokens=section["max_tokens"],
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )

            content = message.content[0].text
            html_content = extract_html_from_text(content)

            if html_content and len(html_content) > 200:
                all_sections[key] = html_content
                print(f"      ✅ {key}: {len(html_content)} caratteri")
            else:
                all_sections[key] = f'<div><h2>Sezione non disponibile</h2><p>Questa sezione non è stata generata correttamente.</p></div>'
                print(f"      ❌ {key}: contenuto troppo corto ({len(html_content)} car)")

            total_input_tokens += message.usage.input_tokens
            total_output_tokens += message.usage.output_tokens
            print(f"      Tokens: {message.usage.input_tokens} in / {message.usage.output_tokens} out")

        except Exception as e:
            print(f"      ❌ Errore {key}: {e}")
            all_sections[key] = f'<div><h2>Sezione non disponibile</h2><p>Errore nella generazione: {str(e)}</p></div>'

    # Calcola costo totale
    cost = (total_input_tokens / 1_000_000 * 3.0) + (total_output_tokens / 1_000_000 * 15.0)

    generated_count = sum(1 for k, v in all_sections.items() if 'non disponibile' not in v)
    total_chars = sum(len(v) for v in all_sections.values())

    print(f"\n[OK] Report PREMIUM AI completato")
    print(f"   Sezioni generate: {generated_count}/11")
    print(f"   Caratteri totali: {total_chars}")
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
