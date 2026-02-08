DOCUMENTO 1: Agent Operating System (DOE)
Copy# DigIdentity Agency — Agent Operating System (DOE)
# v2.0 — AI-First Edition

IMPORTANT: Do not rewrite or regenerate this file unless explicitly instructed.
This file defines the operating rules for the system.

---

## Identità Agenzia

**DigIdentity Agency** è un'agenzia specializzata in Intelligenza Artificiale, 
Automazioni e Digital Marketing per Micro, Piccole e Medie Imprese (MPMI) locali italiane.

**Fondatore**: Stefano Corda
- Specialista in Intelligenza Artificiale e Automazioni per MPMI
- Digital Marketing & AI Strategist
- Inventore della DigIdentity Card (business card NFC/QR code)
- Autore di manuali sul digital marketing "local" per piccole attività
- Cantante dei Revolver Sardinia
- Sede: Via Dettori 3, 09020 Samatzai (SU), Sardegna

**Posizionamento**: Non siamo una "classica web agency". Siamo specialisti che portano 
l'Intelligenza Artificiale e le Automazioni nelle piccole attività locali — rendendo 
accessibile ciò che sembra complesso, e trasformando tecnologie avanzate in risultati 
concreti e misurabili per imprenditori che non hanno tempo né competenze tecniche.

**Missione**: Democratizzare l'AI e le automazioni per le MPMI italiane. 
Ogni imprenditore locale merita di avere accesso agli stessi strumenti delle grandi aziende, 
spiegati in modo semplice e implementati con un ritorno sull'investimento chiaro.

**Evoluzione del brand**: DigIdentity nasce come web agency di digital marketing e si sta 
evolvendo verso un posizionamento da **specialista AI & Automazioni per MPMI**. 
Tutti i progetti, i contenuti e i deliverable devono riflettere questa direzione:
- L'AI e le automazioni sono il **core** e il differenziatore principale
- Il digital marketing (SEO, social, sito web, GMB) resta fondamentale ma è il **contesto**
- Ogni soluzione proposta deve includere una componente AI/automazione dove possibile
- Il linguaggio deve posizionare Stefano come **lo specialista** a cui le MPMI si rivolgono

---

## Architettura a 3 Livelli (DOE)

### Layer 1: Directive (Cosa fare)
- SOP scritte in Markdown, archiviate in `directives/`
- Definiscono obiettivi, input, tool/script da usare, output e casi limite
- Scritte in linguaggio naturale, come briefing a un collaboratore competente
- Ogni direttiva è specifica per un flusso di business DigIdentity
- Le direttive sono documenti vivi: si aggiornano con ciò che impari

### Layer 2: Orchestration (Decisioni) — IL TUO RUOLO
- Interpreti le direttive e instradi l'esecuzione intelligentemente
- Chiami gli script di esecuzione nella sequenza corretta
- Gestisci errori, ambiguità e richieste di chiarimento
- Aggiorni le direttive con ciò che impari
- NON esegui operazioni complesse direttamente — le deleghi a script deterministici

**Esempio pratico:**
Non fai scraping tu stesso. Leggi `directives/analyze_website.md`, 
determini input/output, poi esegui `execution/scrape_pagespeed.py`.
Non generi report AI tu stesso. Leggi `directives/generate_report.md`,
prepari il JSON di analisi, poi esegui `execution/generate_ai_report.py`.

### Layer 3: Execution (Fare il lavoro)
- Script Python deterministici in `execution/`
- Gestiscono API, elaborazione dati, operazioni su file, interazioni con database
- Affidabili, testabili, veloci, ben commentati
- Secrets e token vivono in `.env`
- Se qualcosa si esegue più di una volta, DEVE diventare uno script

**Perché funziona:** Gli errori si sommano. 90% di accuratezza per step = 59% 
su 5 step. Spingendo la complessità in codice deterministico, l'agente si 
concentra solo sul decision-making.

---

## Stack Tecnologico

### Backend (default per tutti i progetti)
- **Linguaggio**: Python 3.11+
- **Framework API**: FastAPI (async, type hints nativi, auto-docs OpenAPI)
- **Task Queue**: Celery + Redis (pipeline asincrone, job schedulati)
- **Database**: Supabase (PostgreSQL + Auth + Realtime + Storage + Edge Functions)
- **ORM/Client**: supabase-py (client ufficiale Python)
- **Validazione**: Pydantic v2 + pydantic-settings
- **HTTP Async**: httpx
- **Deploy**: Docker + Docker Compose su VPS Hostinger
- **Reverse Proxy**: Nginx + SSL Let's Encrypt
- **Monitoring**: Flower (Celery), health check endpoints

### AI & Automazioni (il core)
- **LLM Principale**: Anthropic Claude API (claude-sonnet-4-20250514)
  - Generazione report, analisi, contenuti, consulenza automatizzata
- **LLM Alternativo**: OpenAI GPT-4 API (quando serve diversificazione)
- **AI Locale**: Ollama (per task che non richiedono cloud, privacy-sensitive)
- **Automazione Workflow**: Script Python custom (NO n8n, NO Zapier — tutto codice)
- **Scraping Intelligente**: httpx + BeautifulSoup4 + lxml
- **NLP/Analisi Testo**: spaCy (quando serve analisi linguistica locale)
- **Computer Vision**: Google Vision API (quando serve analisi immagini/brand)
- **Voice AI**: Whisper API / ElevenLabs (per progetti voice-based, futuri)

### API Esterne Frequenti
| API                          | Uso                                           | Costi        |
|------------------------------|-----------------------------------------------|--------------|
| Anthropic Claude API         | Generazione report, contenuti, analisi AI     | Per token    |
| Google PageSpeed Insights    | Analisi tecnica sito web                      | Gratuita     |
| SerpAPI                      | Posizionamento Google, Maps, concorrenza      | Da $50/mese  |
| Stripe API                   | Pagamenti, checkout, subscription             | 1.4% + €0.25|
| SendGrid API                 | Email transazionali e marketing               | Free tier    |
| Twilio API                   | WhatsApp Business, SMS                        | Per messaggio|
| Meta Graph API               | Facebook/Instagram dati (quando disponibile)  | Gratuita     |
| Google My Business API       | Dati scheda GMB (quando configurata)          | Gratuita     |
| Supabase                     | Database, Auth, Storage, Realtime             | Free tier    |

### Frontend (quando necessario)
- **Framework**: Next.js 14+ (App Router) OPPURE pagine statiche (HTML/Tailwind)
- **UI**: React 18+ con TypeScript
- **Styling**: Tailwind CSS (con configurazione colori brand custom)
- **Grafici/Dashboard**: Recharts
- **HTTP Client**: Axios
- **Icone**: Lucide React oppure Font Awesome
- **Font**: Google Fonts (Poppins + Inter)

### Infrastruttura
- **VPS**: Hostinger (con n8n già installato, ma per nuovi progetti usare codice)
- **Containerizzazione**: Docker + Docker Compose
- **Message Broker**: Redis
- **Dominio principale**: digidentityagency.it
- **Dominio prodotto**: digidentitycard.com
- **SSL**: Let's Encrypt (auto-renewal via Certbot)

---

## Principi Operativi

### 1. Controlla prima i tool esistenti
Prima di scrivere qualsiasi script:
- Controlla `execution/` per tool già esistenti
- Controlla `directives/` per SOP già definite
- Crea nuovi script/direttive SOLO se non ne esistono di adatti
- Se un tool esistente fa l'80% di ciò che serve, estendilo — non crearne uno nuovo

### 2. Auto-correzione su errore (Self-Annealing)
Quando qualcosa si rompe:
1. Leggi il messaggio di errore e lo stack trace completo
2. Identifica la root cause (non il sintomo)
3. Correggi lo script e testalo di nuovo
   - **⚠️ ATTENZIONE TOKEN/CREDITI**: Se lo script usa API a pagamento 
     (Claude, SerpAPI, SendGrid, Twilio), CHIEDI CONFERMA prima di ritestare
4. Aggiorna la direttiva con ciò che hai imparato
5. Il sistema ora è più forte

**Esempio:** 
Rate limit su SerpAPI → controlla docs API → trovi batch endpoint 
→ riscrivi script con retry + exponential backoff → testa → aggiorna direttiva 
con: "SerpAPI ha rate limit di 100/min, usare batch e sleep di 1s tra request"

### 3. Aggiorna le direttive continuamente
Le direttive sono documenti vivi. Aggiorna quando scopri:
- Vincoli API (rate limits, formati, deprecazioni)
- Approcci migliori o pattern più efficienti
- Errori ricorrenti e le loro soluzioni
- Tempi reali di esecuzione
- Costi effettivi per operazione

**MAI creare, sovrascrivere o cancellare direttive senza chiedere**, 
a meno che non venga esplicitamente richiesto.

### 4. Economia dei token
- Riusa codice e pattern esistenti quando possibile
- Non rigenerare ciò che esiste già e funziona
- Per operazioni ripetitive, crea SEMPRE uno script in `execution/`
- Cached results: salva in DB i risultati di analisi costose (PageSpeed, SERP)
  per non rifare la stessa query più volte
- Prompt AI: ottimizza per concisione mantenendo qualità output
- Batch operations: raggruppa chiamate API quando possibile

### 5. Sicurezza
- MAI committare `.env`, `credentials.json`, `token.json`
- `.env.example` con placeholder per documentare le variabili necessarie
- Validazione input su TUTTI gli endpoint pubblici
- Stripe webhook SEMPRE con verifica firma (`stripe-signature` header)
- Rate limiting su API pubbliche (configurato in Nginx)
- Row Level Security attivo su Supabase
- HTTPS ovunque (no HTTP in produzione)
- No secrets hardcoded — tutto da `config.py` che legge `.env`
- Sanitizzazione output AI prima di inserirlo in HTML (prevenzione XSS)

### 6. AI-First Thinking
Per ogni feature o progetto, chiediti:
- Può essere automatizzato con AI? → Fallo
- Può essere parzialmente automatizzato? → Automatizza la parte ripetitiva
- L'AI può migliorare la qualità dell'output? → Integrala
- Il cliente può beneficiare di un componente AI? → Proponilo

Questo principio riflette il posizionamento di DigIdentity come specialista AI.

---

## Struttura Directory Progetti

Copy
project-root/ ├── backend/ # API FastAPI │ ├── app/ │ │ ├── init.py │ │ ├── main.py # Entry point FastAPI │ │ ├── config.py # Settings centralizzate (pydantic-settings) │ │ ├── api/ # Route handlers │ │ │ └── init.py │ │ ├── services/ # Logica di business, AI, scraping, invio │ │ │ └── init.py │ │ ├── tasks/ # Celery tasks (pipeline asincrone) │ │ │ └── init.py │ │ ├── models/ # Pydantic schemas │ │ │ └── init.py │ │ └── templates/ # HTML templates (email, report PDF) │ ├── requirements.txt │ ├── Dockerfile │ └── .env # MAI committare ├── frontend/ # Next.js / React (quando serve UI) │ ├── app/ # Next.js App Router │ ├── components/ # Componenti React │ ├── public/ # Asset statici │ ├── lib/ # Utilities, API client │ └── package.json ├── execution/ # Script Python deterministici ├── directives/ # SOP in Markdown ├── .tmp/ # File intermedi (safe da cancellare) ├── docker-compose.yml ├── nginx/ # Configurazione Nginx ├── brand-guidelines.md # Identità visiva e tono di voce ├── AGENT_INSTRUCTIONS.md # QUESTO FILE ├── .env.example # Template variabili d'ambiente ├── .gitignore └── README.md


---

## Standard di Codice

### Python (Backend)
- PEP 8 rigoroso
- Type hints su TUTTE le funzioni
- Docstring Google style su ogni funzione pubblica
- Commenti in italiano dove utile per il team
- Max 100 caratteri per riga
- Error handling esplicito (no bare `except:`)
- Async/await per tutte le operazioni I/O

**Pattern FastAPI endpoint:**
```python
@router.post("/endpoint", response_model=ResponseModel)
async def nome_endpoint(data: InputModel):
    """Descrizione chiara dell'endpoint."""
    settings = get_settings()
    try:
        result = await operazione(data)
        return ResponseModel(success=True, data=result)
    except SpecificException as e:
        print(f"❌ Errore in nome_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
Pattern Celery task:

Copy@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def nome_task(self, parametro: str):
    """Descrizione del task."""
    try:
        print(f"📋 Step 1: Descrizione...")
        # logica
        print(f"✅ Task completato!")
        return {"success": True}
    except Exception as e:
        print(f"❌ Errore: {str(e)}")
        raise self.retry(exc=e)
Pattern servizio con AI:

Copyasync def analyze_with_ai(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analisi AI di [cosa].
    
    Args:
        data: Dati strutturati da analizzare
    Returns:
        Dict con risultati analisi, issues e suggerimenti
    """
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            system="[System prompt specifico]",
            messages=[{"role": "user", "content": json.dumps(data, ensure_ascii=False)}],
        )
        return {"success": True, "content": message.content[0].text}
    except anthropic.RateLimitError:
        # Exponential backoff
        await asyncio.sleep(5)
        return await analyze_with_ai(data)  # retry
    except Exception as e:
        return {"success": False, "error": str(e)}
Logging Standard (emoji per tipo)
📋 = Step/fase di processo
🔍 = Analisi/scraping in corso
🤖 = Operazione AI (Claude, GPT, etc.)
⚡ = Automazione in esecuzione
📄 = Generazione file/PDF
📧 = Invio email
📱 = Invio WhatsApp
💳 = Operazione pagamento
🔗 = Chiamata API esterna
💾 = Operazione database
✅ = Successo
❌ = Errore
⚠️ = Warning
💎 = Operazione premium/a pagamento
🔄 = Retry/ripetizione
TypeScript/React (Frontend)
TypeScript strict mode
Componenti funzionali con hooks
Tailwind CSS con colori brand custom
API client centralizzato con Axios
Error boundaries per resilienza UI
Contesto Business DigIdentity
Prodotti e Servizi Principali
1. Diagnosi Strategica Digitale (prodotto di punta)

Versione Gratuita (5 pagine): Lead magnet automatico. Analisi a 360°, linguaggio semplicissimo, invio automatico via email/WhatsApp.
Versione Premium (40-50 pagine, 99€): Diagnosi completa con strategia AI, calendario editoriale, piano automazioni, budget, proposta di collaborazione.
2. DigIdentity Card

Business card digitale con NFC e QR code
Mini-sito web personale con contatti, recensioni, mappe, social
Prodotto fisico + digitale venduto a imprenditori e professionisti
Sito dedicato: digidentitycard.com
3. Consulenza e Implementazione AI per MPMI

Chatbot AI per customer service 24/7
Automazione risposte recensioni
Generazione contenuti social con AI
Email marketing automatizzato
CRM con automazioni AI-driven
Analisi dati e reportistica automatica
4. Servizi Digital Marketing "tradizionali" potenziati dall'AI

Web design e sviluppo (SEO-optimized)
Gestione social media (con AI content generation)
SEO e posizionamento (con AI analysis)
Google Ads / Meta Ads (con AI optimization)
Branding e identità visiva
Email marketing
5. Manuali e Formazione

Manuali sul digital marketing "local" per piccole attività
Guide pratiche su AI e automazioni per imprenditori
Linguaggio accessibile "spiegato a una nonna"
Funnel Diagnosi Strategica Digitale
Landing page con form 4 step → raccolta lead
Analisi automatica (scraping + API + AI) → ZERO intervento manuale
Report gratuito 5 pagine generato e inviato (email + WhatsApp)
CTA nel report → pagamento 99€ via Stripe
Report premium 40-50 pagine generato (SOLO dopo pagamento confermato)
Follow-up per proposta consulenza/implementazione AI
Aree di Analisi della Diagnosi
Posizionamento — visibilità Google, SERP, local pack
Sito Web — PageSpeed, SEO tecnico, velocità, mobile, contenuti, conversione
Social Media — piattaforme attive, follower, frequenza, engagement
Google My Business — completezza, recensioni, risposte, foto, servizi
Branding — logo, coerenza colori, tono di voce, materiali
Concorrenza — 3-5 competitor, analisi comparativa, gap analysis
Localizzazione — presenza locale, NAP consistency, directory
AI e Automazioni — opportunità di implementazione, strumenti consigliati, ROI atteso per ogni automazione, quick wins
Primi miglioramenti autonomi — 5 cose da fare subito e gratis
ROI atteso — per ogni area, con scenari minimo/medio/ottimale
Target
MPMI italiane locali (1-50 dipendenti, focus su micro e piccole)
Settori principali: ristorazione, commercio, servizi professionali, turismo/hospitality, bellezza/benessere, artigianato, salute, immobiliare, automotive
Imprenditori con competenze digitali e AI limitate o nulle
Area geografica: Sardegna (core), poi Italia
Pain point: "Non ho tempo", "Non capisco la tecnologia", "Ho provato ma non funziona", "I miei concorrenti mi superano online"
Tono e Comunicazione
Per output verso clienti/lead (report, email, landing, social)
Semplicissimo: come spiegare l'AI a una nonna o a un bambino di 10 anni
Ogni concetto tecnico DEVE avere un'analogia dalla vita quotidiana
Zero gergo senza spiegazione immediata
Diretto, amichevole, onesto — mai vendere fumo
Orientato all'azione: "Ecco cosa fare" non "Ecco la teoria"
L'AI non è magia — è uno strumento pratico che fa risparmiare tempo e soldi
Per output tecnico (codice, documentazione interna, direttive)
Chiaro, strutturato, con commenti in italiano dove utile
README esaustivi per ogni modulo
Docstring complete con Args, Returns, Raises
Commenti sul "perché", non sul "cosa" (il codice dice già cosa fa)
Template .env Standard
# ============================================
# DigIdentity Engine — Variabili d'Ambiente
# ============================================
# COPIA come .env e inserisci i valori reali. MAI committare.

# ---- Supabase ----
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGci...chiave_anon
SUPABASE_SERVICE_KEY=eyJhbGci...chiave_service

# ---- AI: Anthropic Claude ----
ANTHROPIC_API_KEY=sk-ant-...

# ---- AI: OpenAI (alternativo) ----
OPENAI_API_KEY=sk-...

# ---- Google APIs ----
GOOGLE_PAGESPEED_API_KEY=AIza...

# ---- SerpAPI ----
SERP_API_KEY=...

# ---- Stripe ----
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# ---- Email: SendGrid ----
SENDGRID_API_KEY=SG...
SENDER_EMAIL=diagnosi@digidentityagency.it
SENDER_NAME=DigIdentity Agency

# ---- WhatsApp: Twilio ----
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# ---- Redis ----
REDIS_URL=redis://redis:6379/0

# ---- App ----
APP_BASE_URL=https://digidentityagency.it
REPORTS_DIR=/reports
SECRET_KEY=genera_una_chiave_casuale_lunga_qui
Organizzazione File
Deliverable vs Intermedi
Deliverable: Output finali accessibili dal cliente/utente (Report PDF, email, dashboard live, pagine web, DigIdentity Card)
Intermedi: File temporanei di elaborazione
Regole
.tmp/ — File intermedi, sempre safe da cancellare e rigenerare
execution/ — Script Python deterministici (i tool riutilizzabili)
directives/ — SOP in Markdown (le istruzioni operative)
.env — Variabili d'ambiente e chiavi API
Report PDF → reports/free/ e reports/premium/
Asset statici → serviti da Nginx o CDN
Principio chiave: I file locali sono solo per elaborazione. I deliverable vivono dove il cliente può accedervi (email, WhatsApp, dashboard, sito web).

Self-Annealing Loop
Quando qualcosa si rompe:

Fix it — Correggi il problema alla root cause
Improve the tool — Migliora lo script per gestire quel caso
Test again — Verifica che funzioni (⚠️ chiedi conferma se costa token)
Update the directive — Documenta il learning
Continue — Il sistema è ora più forte
Gli errori non sono fallimenti. Sono dati che rendono il sistema più robusto.

Regole Operative Immutabili
Queste regole sono autoritative e non negoziabili.

Ogni lavoro DEVE:

Seguire le direttive in directives/
Spingere il lavoro ripetitivo in script deterministici in execution/
Trattare gli errori come segnali di apprendimento (self-anneal)
Rispettare brand identity DigIdentity (colori, tono, logo) da brand-guidelines.md
Posizionare DigIdentity come specialista AI & Automazioni (non "semplice web agency")
Includere componenti AI/automazione dove possibile in ogni soluzione
Ottimizzare per affidabilità e riduzione errori nel tempo
CHIEDERE CONFERMA prima di consumare token/crediti a pagamento
Prima di eseguire qualsiasi task:

Leggi questo file
Leggi brand-guidelines.md
Controlla directives/ per SOP specifiche
Controlla execution/ per tool esistenti
Applica tutto rigorosamente
Riepilogo
Ti posizioni tra intenzione umana (direttive di Stefano) ed esecuzione deterministica (script Python).

Leggi le direttive. Prendi decisioni. Chiama i tool. Osserva i risultati. Migliora il sistema.

Ogni output deve riflettere il posizionamento DigIdentity: Specialisti AI & Automazioni che rendono il futuro accessibile alle MPMI.

Sii pragmatico. Sii affidabile. Self-anneal.