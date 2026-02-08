# DIRETTIVA: Pipeline Diagnosi Gratuita

## Versione
v1.0 — Febbraio 2026

## Obiettivo
Eseguire analisi automatiche sulla presenza digitale del lead e generare un report gratuito di 5 pagine in PDF brandizzato DigIdentity.

## Trigger
Task Celery task_free_report ricevuto con lead_id dopo il salvataggio del lead.

## Flusso di Esecuzione

### Fase 1 — Raccolta Dati (Parallela)
Esegui tutti gli scraping/API in parallelo per velocità. Timeout massimo per singolo servizio: 30 secondi. Se un servizio fallisce, continua con gli altri e segna come "non disponibile" nel report.

#### 1.1 Analisi Sito Web (se sito_web fornito)
- Script: execution/scrape_pagespeed.py
- API: Google PageSpeed Insights (desktop + mobile)
- Dati raccolti: Performance score, Accessibility score, Best Practices, SEO score, Core Web Vitals (LCP, FID, CLS), screenshot della pagina
- Salva in: campo analysis_pagespeed (JSON) nella tabella leads

#### 1.2 Analisi SERP / Posizionamento
- Script: execution/scrape_serp.py
- API: SerpAPI
- Query: "{nome_azienda} {citta}", "{settore_attivita} {citta}"
- Dati raccolti: posizione organica, presence in Local Pack, numero competitor visibili, snippet in evidenza
- Salva in: campo analysis_serp (JSON)

#### 1.3 Analisi Google My Business
- Script: execution/scrape_gmb.py
- Metodo: SerpAPI Google Maps oppure scraping Google Maps
- Dati raccolti: presente/non presente, rating, numero recensioni, foto caricate, orari compilati, categorie, link sito, descrizione
- Salva in: campo analysis_gmb (JSON)

#### 1.4 Analisi Social Media
- Script: execution/scrape_social.py
- Metodo: Meta Graph API (se disponibile) + scraping pubblico profili
- Piattaforme: quelle indicate nel form (piattaforme_social)
- Dati raccolti: follower count, frequenza post (ultimi 30 giorni), engagement medio, bio/descrizione, link al sito presente
- Salva in: campo analysis_social (JSON)

#### 1.5 Analisi Concorrenza Locale
- Script: execution/scrape_competitors.py
- Metodo: SerpAPI per query "{settore_attivita} {citta}"
- Dati raccolti: top 3-5 competitor visibili, loro rating GMB, loro posizionamento, punti di forza visibili
- Salva in: campo analysis_competitors (JSON)

### Fase 2 — Calcolo Score
- Script: execution/calculate_scores.py
- Genera un punteggio 0-100 per ogni area:
  - score_sito_web (da PageSpeed)
  - score_seo (da SERP + PageSpeed SEO)
  - score_gmb (da analisi GMB)
  - score_social (da analisi social)
  - score_competitivo (da analisi concorrenza)
  - score_totale (media ponderata: sito 20%, SEO 25%, GMB 25%, social 15%, competitivo 15%)
- Salva scores in tabella leads

### Fase 3 — Generazione Report AI
- Script: execution/generate_ai_report.py
- AI: Claude API (claude-sonnet-4-20250514)
- Input: JSON strutturato con tutti i dati delle analisi + scores + dati lead
- Prompt: Segui template in directives/prompts/free-report-prompt.md
- Output: HTML strutturato (5 sezioni)
- Sezioni del Report Gratuito:
  1. Panoramica — Chi è l'azienda, settore, contesto locale, score totale con grafico radar
  2. Presenza Online — Stato attuale sito + social + GMB, cosa funziona e cosa no
  3. Posizionamento e Concorrenza — Dove si posiziona rispetto ai competitor locali
  4. Opportunità Immediate — 3-5 azioni concrete che possono fare subito (gratuite o low-cost)
  5. Prossimi Passi — CTA verso Diagnosi Premium a 99 euro con preview di cosa include

### Fase 4 — Generazione PDF
- Script: execution/generate_pdf.py
- Strumento: WeasyPrint
- Template: HTML con branding DigIdentity (colori, logo, font)
- Output: PDF salvato in /reports/free/{lead_id}_diagnosi_gratuita.pdf

### Fase 5 — Invio
- Script: execution/send_report.py
- Email: SendGrid — template brandizzato con PDF allegato
- WhatsApp: Twilio — messaggio con link download (se telefono valido)
- Aggiorna status lead in Supabase a "free_report_sent"
- Registra evento in tabella analytics_events

## Timing Target
- Fase 1 (scraping): max 60 secondi
- Fase 2 (scores): max 5 secondi
- Fase 3 (AI): max 30 secondi
- Fase 4 (PDF): max 10 secondi
- Fase 5 (invio): max 15 secondi
- Totale: sotto i 2 minuti dal form submit

## Gestione Errori
- Singolo scraper fallisce: continua, segna "Dati non disponibili" nel report
- Claude API fallisce: retry 2 volte, poi salva errore e notifica admin
- PDF fallisce: retry, poi invia report come HTML via email
- Email fallisce: retry 3 volte con backoff, poi segna per invio manuale
- WhatsApp fallisce: ignora silenziosamente (email è il canale primario)

## Costo Stimato per Report
- Claude API: circa 0.02-0.05 euro
- SerpAPI: circa 0.01 euro
- PageSpeed: gratuito
- SendGrid: circa 0.001 euro
- Totale: circa 0.03-0.06 euro per report gratuito