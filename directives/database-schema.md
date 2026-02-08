# DIRETTIVA: Schema Database Supabase

## Versione
v1.0 — Febbraio 2026

## Obiettivo
Definire lo schema del database PostgreSQL su Supabase per gestire lead, report, pagamenti e analytics.

## Tabelle

### leads

Campi principali:
- id: UUID, PK, default gen_random_uuid()
- nome_contatto: TEXT, NOT NULL
- email: TEXT, NOT NULL
- telefono: TEXT, NOT NULL
- nome_azienda: TEXT, NOT NULL
- settore_attivita: TEXT, NOT NULL
- sito_web: TEXT, nullable
- citta: TEXT, NOT NULL
- provincia: TEXT, NOT NULL
- ha_google_my_business: BOOLEAN, default false
- ha_social_attivi: BOOLEAN, default false
- piattaforme_social: JSONB, array di stringhe
- ha_sito_web: BOOLEAN, default false
- obiettivo_principale: TEXT
- urgenza: INTEGER, 1-5
- budget_mensile_indicativo: TEXT, range come stringa
- consenso_privacy: BOOLEAN, NOT NULL, default false
- consenso_marketing: BOOLEAN, default false
- status: TEXT, NOT NULL, default 'new'

Campi analisi gratuita:
- analysis_pagespeed: JSONB, nullable
- analysis_serp: JSONB, nullable
- analysis_gmb: JSONB, nullable
- analysis_social: JSONB, nullable
- analysis_competitors: JSONB, nullable

Campi analisi premium:
- analysis_site_deep: JSONB, nullable
- analysis_seo_deep: JSONB, nullable
- analysis_reputation: JSONB, nullable
- analysis_social_deep: JSONB, nullable
- analysis_ai_opportunities: JSONB, nullable

Campi score:
- score_sito_web: INTEGER, 0-100, nullable
- score_seo: INTEGER, 0-100, nullable
- score_gmb: INTEGER, 0-100, nullable
- score_social: INTEGER, 0-100, nullable
- score_competitivo: INTEGER, 0-100, nullable
- score_totale: INTEGER, 0-100, nullable

Campi tracking:
- ip_address: TEXT, per rate limiting
- user_agent: TEXT, per analytics
- utm_source: TEXT, nullable
- utm_medium: TEXT, nullable
- utm_campaign: TEXT, nullable

Campi temporali:
- created_at: TIMESTAMPTZ, default now()
- updated_at: TIMESTAMPTZ, default now(), auto-update
- report_sent_at: TIMESTAMPTZ, nullable
- premium_sent_at: TIMESTAMPTZ, nullable

### Stati possibili del lead (campo status)
- new: appena inserito
- processing: pipeline gratuita in corso
- analysis_complete: analisi finite, report in generazione
- free_report_generated: PDF pronto
- free_report_sent: email/WhatsApp inviati
- payment_pending: ha cliccato su paga
- payment_confirmed: pagamento ricevuto
- premium_processing: pipeline premium in corso
- premium_report_generated: PDF premium pronto
- premium_report_sent: report premium inviato
- converted: è diventato cliente (aggiornamento manuale o CRM)
- error: errore nel processo

### reports
- id: UUID, PK
- lead_id: UUID, FK verso leads.id
- report_type: TEXT, 'free' o 'premium'
- html_content: TEXT, contenuto HTML generato
- pdf_path: TEXT, percorso file PDF
- ai_model_used: TEXT, es. 'claude-sonnet-4-20250514'
- ai_tokens_used: INTEGER, per tracking costi
- ai_cost_estimated: DECIMAL, costo stimato in EUR
- generation_time_seconds: INTEGER
- status: TEXT, 'generating', 'completed', 'error'
- error_message: TEXT, nullable
- created_at: TIMESTAMPTZ, default now()

### payments
- id: UUID, PK
- lead_id: UUID, FK verso leads.id
- stripe_session_id: TEXT
- stripe_payment_intent: TEXT
- amount: DECIMAL, 99.00
- currency: TEXT, 'EUR'
- status: TEXT, 'pending', 'completed', 'failed', 'refunded'
- payment_method: TEXT, 'stripe', 'paypal', 'klarna'
- created_at: TIMESTAMPTZ, default now()
- completed_at: TIMESTAMPTZ, nullable

### analytics_events
- id: UUID, PK
- lead_id: UUID, FK verso leads.id, nullable
- event_type: TEXT, es. 'form_start', 'form_complete', 'report_generated', 'email_opened', 'cta_clicked', 'payment_started', 'payment_completed'
- event_data: JSONB, dati aggiuntivi
- ip_address: TEXT
- created_at: TIMESTAMPTZ, default now()

## Indici
- leads: email (UNIQUE), status, created_at, citta, settore_attivita
- reports: lead_id, report_type, status
- payments: lead_id, stripe_session_id, status
- analytics_events: lead_id, event_type, created_at

## RLS (Row Level Security)
- Abilitare RLS su tutte le tabelle
- Accesso solo tramite service_role key dal backend
- Nessun accesso diretto dal frontend (tutto passa per FastAPI)

## View per Dashboard
- view_kpi_summary: total leads, leads this month, conversions, revenue
- view_funnel: conteggio lead per ogni status
- view_daily_stats: lead e revenue per giorno (ultimi 30/60/90 giorni)

## Migration
- Script SQL in execution/migrations/001_initial_schema.sql
- Eseguire tramite Supabase SQL Editor o CLI