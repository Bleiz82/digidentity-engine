# DigIdentity Engine

> Sistema automatico di lead generation e diagnosi digitale per PMI italiane.

## Architettura

```
digidentity-engine/
├── backend/                    # FastAPI + Celery + Redis
│   └── app/
│       ├── api/
│       │   ├── leads.py        # CRUD lead + avvio pipeline free
│       │   └── payment.py      # Stripe checkout, webhook, success page
│       ├── tasks/
│       │   ├── free_report_task.py     # Pipeline FREE (Celery task)
│       │   └── premium_report_task.py  # Pipeline PREMIUM (Celery task)
│       ├── core/
│       │   ├── config.py        # Configurazione centralizzata (.env)
│       │   ├── celery_app.py    # Configurazione Celery
│       │   └── supabase_client.py # Client Supabase
│       ├── models/
│       │   └── lead.py          # Pydantic models
│       └── main.py              # FastAPI app entry point
├── execution/                   # Moduli di esecuzione
│   ├── scraper.py              # Scraping multi-sorgente (sito, SEO, social)
│   ├── ai_report.py            # Generazione report con Claude AI
│   ├── pdf_generator.py        # Conversione Markdown → PDF (WeasyPrint)
│   └── send_email.py           # Invio email transazionali (SMTP)
├── directives/
│   └── prompts/                # Prompt AI per i report
│       ├── free_report_system.md
│       ├── free_report_user.md
│       ├── premium_report_system.md
│       └── premium_report_user.md
├── dashboard/                   # Next.js 16 (frontend) — TBD
├── scripts/
│   ├── stripe_webhook_forward.sh  # Stripe CLI webhook forwarding
│   ├── stripe_trigger_test.sh     # Test webhook con eventi Stripe
│   └── test_pipeline_e2e.py       # Test end-to-end della pipeline
├── .env.example                 # Template variabili d'ambiente
├── requirements.txt             # Dipendenze Python
└── Makefile                     # Comandi rapidi
```

## Pipeline

### Pipeline FREE (automatica dopo submit lead)

```
Lead submit → Scraping sito web → AI Report (Claude) → PDF → Email con CTA premium
```

### Pipeline PREMIUM (dopo pagamento Stripe 99€)

```
Stripe Checkout → Webhook → Celery task → AI Report Premium (40-50pp) → PDF → Email
```

## Setup Rapido

### 1. Prerequisiti

- Python 3.11+
- Redis (in esecuzione)
- Stripe CLI (per webhook locali)

### 2. Installazione

```bash
# Clona il repo
git clone https://github.com/Bleiz82/digidentity-engine.git
cd digidentity-engine

# Copia e configura il .env
cp .env.example .env
# Compila tutte le variabili in .env

# Installa dipendenze
pip install -r requirements.txt
```

### 3. Avvio Servizi (3 terminali)

**Terminale 1 — Backend FastAPI:**
```bash
make run
# oppure: uvicorn backend.app.main:app --host 0.0.0.0 --port 8080 --reload
```

**Terminale 2 — Worker Celery:**
```bash
make worker
# oppure: celery -A backend.app.core.celery_app worker --loglevel=info
```

**Terminale 3 — Stripe CLI (webhook forwarding):**
```bash
make webhook
# oppure: bash scripts/stripe_webhook_forward.sh
```

> **IMPORTANTE:** Il webhook signing secret (`whsec_...`) stampato da Stripe CLI va copiato nel `.env` come `STRIPE_WEBHOOK_SECRET`.

### 4. Test

```bash
# Health check
make test

# Pipeline free end-to-end
make test-free

# Pipeline completa (free + premium con pagamento manuale)
make test-full
```

## API Endpoints

| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| `GET` | `/` | Health check base |
| `GET` | `/health` | Health check dettagliato |
| `POST` | `/api/leads/` | Crea un nuovo lead (avvia pipeline free) |
| `GET` | `/api/leads/{id}` | Stato del lead |
| `GET` | `/api/leads/` | Lista lead |
| `POST` | `/api/payment/create-checkout` | Crea Stripe Checkout Session |
| `POST` | `/api/payment/webhook` | Riceve webhook Stripe |
| `GET` | `/api/payment/success` | Pagina conferma pagamento |
| `GET` | `/api/payment/cancel` | Pagina annullamento pagamento |

## Stripe Webhook

Il webhook endpoint (`POST /api/payment/webhook`) gestisce:

- **`checkout.session.completed`**: Aggiorna stato lead → lancia `task_premium_report`
- **`payment_intent.succeeded`**: Log di conferma
- **`payment_intent.payment_failed`**: Log di errore

### Setup Stripe CLI per sviluppo locale

```bash
# 1. Installa Stripe CLI
brew install stripe/stripe-cli/stripe  # macOS

# 2. Login
stripe login

# 3. Avvia forwarding
stripe listen --forward-to http://127.0.0.1:8080/api/payment/webhook \
  --events checkout.session.completed,payment_intent.succeeded,payment_intent.payment_failed

# 4. Copia il whsec_... nel .env come STRIPE_WEBHOOK_SECRET

# 5. Test con evento simulato
stripe trigger checkout.session.completed
```

## Variabili d'Ambiente

Vedi `.env.example` per il template completo. Chiavi necessarie:

- `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY`
- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
- `ANTHROPIC_API_KEY`
- `SERPAPI_KEY`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`
- `REDIS_URL`

## Qualita Report AI

I prompt in `directives/prompts/` sono ottimizzati per:

- **Report Free (8-12 pagine)**: Diagnosi concreta basata su dati reali di scraping. Punteggi motivati, azioni prioritarie, CTA per premium.
- **Report Premium (40-50 pagine)**: Piano strategico completo con 14 sezioni: audit sito, SEO, social, competitor, calendario editoriale 3 mesi, preventivo dettagliato, roadmap implementazione.
