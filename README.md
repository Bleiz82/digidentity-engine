# DigIdentity Engine

**Backend per la Diagnosi Strategica Digitale automatizzata**

Sistema automatizzato per generare diagnosi digitali per MPMI (Micro, Piccole e Medie Imprese) italiane, con AI e automazioni.

---

## 🏗️ Architettura

Il sistema segue l'architettura **DOE (DigIdentity Operating Engine)** a 3 livelli:

1. **Directive** (`directives/`) — SOP in Markdown che definiscono cosa fare
2. **Orchestration** (Agente AI) — Interpreta le direttive e chiama gli script
3. **Execution** (`execution/`) — Script Python deterministici che eseguono il lavoro

---

## 🚀 Quick Start

### 1. Prerequisiti

- Python 3.11+
- Redis (per Celery)
- Account Supabase (database)
- API Keys: Anthropic Claude, SerpAPI, Stripe, Gmail SMTP, WhatsApp Meta

### 2. Setup Database

Esegui lo schema SQL su Supabase:

```bash
# Copia il contenuto di execution/migrations/001_initial_schema.sql
# ed eseguilo nel Supabase SQL Editor
```

### 3. Configurazione

```bash
# Copia .env.example in .env
cp .env.example .env

# Modifica .env con le tue chiavi API reali
```

### 4. Installazione Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Su Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Avvio Backend

```bash
# Dalla directory backend/
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

L'API sarà disponibile su `http://localhost:8000`

- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### 6. Test Endpoint

```bash
# Test health check
curl http://localhost:8000/health

# Test submit lead (esempio)
curl -X POST http://localhost:8000/api/lead-workflow \
  -H "Content-Type: application/json" \
  -d '{
    "nome_azienda": "Test Azienda",
    "settore_attivita": "Ristorazione",
    "citta": "Cagliari",
    "provincia": "CA",
    "ha_sito_web": true,
    "urgenza": 3,
    "nome_contatto": "Mario Rossi",
    "email": "test@example.com",
    "telefono": "+39 340 123 4567",
    "consenso_privacy": true
  }'
```

---

## 📁 Struttura Progetto

```
digidentity-projects/
├── backend/              # API FastAPI
│   ├── app/
│   │   ├── api/         # Route handlers
│   │   ├── services/    # Business logic
│   │   ├── models/      # Pydantic schemas
│   │   ├── db/          # Database client
│   │   ├── config.py    # Settings
│   │   └── main.py      # Entry point
│   └── requirements.txt
├── execution/           # Script Python deterministici
│   ├── migrations/      # SQL migrations
│   └── validators.py    # Validazione input
├── directives/          # SOP in Markdown
├── reports/             # Output PDF
├── .env                 # Variabili d'ambiente (MAI committare)
└── .env.example         # Template variabili
```

---

## 🔑 Variabili d'Ambiente Richieste

Vedi `.env.example` per la lista completa. Le principali:

- `SUPABASE_URL` e `SUPABASE_SERVICE_KEY`
- `ANTHROPIC_API_KEY` (Claude)
- `SERP_API_KEY` (SerpAPI)
- `STRIPE_SECRET_KEY` e `STRIPE_WEBHOOK_SECRET`
- `GMAIL_SMTP_PASSWORD` (App password Gmail)
- `WHATSAPP_ACCESS_TOKEN` e `WHATSAPP_PHONE_NUMBER_ID`

---

## 🧪 Testing

```bash
# TODO: Aggiungere test con pytest in Fase 2
```

---

## 📦 Deploy

```bash
# TODO: Docker Compose in Fase 3
```

---

## 📚 Documentazione

- **Direttive:** Vedi `directives/` per le SOP operative
- **Brand Guidelines:** `brand-guidelines.md`
- **Agent Instructions:** `AGENT_INSTRUCTIONS.md`

---

## 🛠️ Sviluppo

### Fase 1 (Completata)
- ✅ Schema database Supabase
- ✅ Backend FastAPI base
- ✅ Endpoint `/api/lead-workflow`
- ✅ Validazione e deduplicazione lead

### Fase 2 (In corso)
- ⏳ Script scraping (PageSpeed, SERP, GMB, Social, Competitors)
- ⏳ Calcolo score
- ⏳ Generazione report AI (Claude)
- ⏳ Generazione PDF (WeasyPrint)
- ⏳ Invio email (Gmail SMTP) e WhatsApp (Meta API)
- ⏳ Task Celery per pipeline asincrona

### Fase 3 (TODO)
- ⏳ Stripe integration
- ⏳ Pipeline premium
- ⏳ Frontend Next.js
- ⏳ Docker + Deploy

---

## 👤 Autore

**Stefano Corda** — DigIdentity Agency  
Specialista AI & Automazioni per MPMI

- 📧 info@digidentityagency.it
- 🌐 https://digidentityagency.it
- 📱 +39 392 199 0215

---

## 📄 Licenza

Proprietario — DigIdentity Agency © 2026
