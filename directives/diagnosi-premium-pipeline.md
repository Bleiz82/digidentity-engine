# DIRETTIVA: Pipeline Diagnosi Premium (99 euro)

## Versione
v1.0 — Febbraio 2026

## Obiettivo
Generare un report premium di 40-50 pagine dopo conferma pagamento Stripe. Riutilizza i dati già raccolti nella diagnosi gratuita e approfondisce con analisi aggiuntive.

## Trigger
Webhook Stripe checkout.session.completed che attiva task Celery task_premium_report con lead_id.

## Pre-condizione
- Lead deve avere status "free_report_sent" (ha già ricevuto il report gratuito)
- Pagamento confermato da Stripe (verificato via webhook signature)

## Flusso di Esecuzione

### Fase 1 — Recupero Dati Esistenti
- Leggi da Supabase tutti i dati di analisi già salvati (pagespeed, serp, gmb, social, competitors)
- NON ripetere scraping già fatti (risparmio token e tempo)

### Fase 2 — Analisi Aggiuntive Premium

#### 2.1 Analisi Approfondita Sito Web
- Script: execution/scrape_site_deep.py
- Crawl fino a 10 pagine interne del sito
- Analisi struttura heading (H1, H2, H3)
- Meta tag per ogni pagina
- Immagini senza alt text
- Link rotti
- Schema markup presente/assente
- Tempo di caricamento per pagina
- Mobile-friendliness dettagliato

#### 2.2 Analisi SEO Avanzata
- Script: execution/scrape_serp_deep.py
- Keywords per cui l'azienda è visibile (top 20)
- Keywords dei competitor per cui il lead NON è visibile
- Trend di ricerca locali nel settore
- Opportunità keyword a bassa competizione

#### 2.3 Analisi Reputazione Online
- Script: execution/scrape_reputation.py
- Recensioni Google (ultime 20, sentiment analysis)
- Menzioni online del brand
- Presenza su directory locali (PagineGialle, Yelp, TripAdvisor se pertinente)

#### 2.4 Analisi Social Approfondita
- Script: execution/scrape_social_deep.py
- Content analysis ultimi 30 post (tipo, engagement, orari)
- Hashtag utilizzati vs efficaci nel settore
- Competitor social comparison
- Tone of voice attuale

#### 2.5 Analisi AI e Automazioni
- Script: execution/analyze_ai_opportunities.py
- Chatbot/assistenti AI presenti sul sito
- Automazioni email/marketing rilevate
- Opportunità di automazione specifiche per il settore
- Stima ROI implementazione AI

### Fase 3 — Generazione Report Premium AI
- Script: execution/generate_premium_report.py
- AI: Claude API (claude-sonnet-4-20250514)
- Metodo: Generazione a sezioni (per non superare limiti token)
- Prompt: Segui template in directives/prompts/premium-report-prompt.md
- Sezioni del Report Premium (40-50 pagine):
  1. Executive Summary (2 pag) — Panoramica, score, situazione attuale, potenziale
  2. Analisi Identità Digitale (4 pag) — Brand online, coerenza visiva, messaging
  3. Audit Sito Web Completo (6 pag) — Performance, UX, SEO on-page, contenuti, struttura
  4. Analisi SEO e Posizionamento (6 pag) — Keywords, SERP, opportunità, strategia
  5. Google My Business Audit (4 pag) — Ottimizzazione scheda, recensioni, strategie local
  6. Social Media Audit (5 pag) — Performance per piattaforma, content strategy, competitor
  7. Analisi Concorrenza (4 pag) — Mappa competitiva, punti di forza/debolezza, differenziazione
  8. Opportunità AI e Automazioni (4 pag) — Chatbot, automazioni, AI tools specifici per settore
  9. Piano Strategico 90 Giorni (5 pag) — Calendario editoriale, azioni prioritarie, milestone
  10. Stima ROI e Budget (3 pag) — Investimento suggerito, ritorno atteso, scenari
  11. Preventivo DigIdentity (2 pag) — Servizi proposti con pricing, pacchetti, CTA

### Fase 4 — Generazione PDF Premium
- Script: execution/generate_premium_pdf.py
- Template premium con copertina, indice, header/footer, numerazione pagine
- Grafici e visualizzazioni (radar chart, bar chart, trend)
- Branding DigIdentity completo
- Output: /reports/premium/{lead_id}_diagnosi_premium.pdf

### Fase 5 — Invio Premium
- Email dedicata con tono "premium" + PDF allegato
- WhatsApp con messaggio personalizzato
- Status aggiornato a "premium_report_sent"
- Registra in analytics_events

## Timing Target
- Fase 1-2 (analisi aggiuntive): max 3 minuti
- Fase 3 (AI generazione sezioni): max 2 minuti
- Fase 4 (PDF): max 30 secondi
- Fase 5 (invio): max 15 secondi
- Totale: sotto i 6 minuti

## Costo Stimato per Report Premium
- Claude API (multi-sezione): circa 0.30-0.50 euro
- SerpAPI (query aggiuntive): circa 0.05 euro
- Scraping aggiuntivo: circa 0.02 euro
- Totale: circa 0.40-0.60 euro per report premium (margine su 99 euro: circa 98%)

## Note
- I token AI si consumano SOLO dopo pagamento confermato
- Se la generazione fallisce dopo il pagamento: notifica admin immediata + refund automatico se non risolto entro 1 ora
- Il report premium contiene un preventivo personalizzato: questo è il vero asset commerciale