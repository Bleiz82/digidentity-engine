# DIRETTIVA: Lead Intake

## Versione
v1.0 — Febbraio 2026

## Obiettivo
Ricevere, validare e salvare i dati di un lead che compila il form a 4 step sulla landing page della Diagnosi Strategica Digitale.

## Trigger
POST su /api/lead-workflow dal form della landing page.

## Input Atteso (4 Step del Form)

### Step 1 — Dati Azienda
- nome_azienda (obbligatorio)
- settore_attivita (obbligatorio, dropdown)
- sito_web (opzionale ma consigliato)
- citta (obbligatorio)
- provincia (obbligatorio)

### Step 2 — Presenza Online Attuale
- ha_google_my_business (sì/no)
- ha_social_attivi (sì/no)
- piattaforme_social (multi-select: Facebook, Instagram, TikTok, LinkedIn, YouTube, Altro)
- ha_sito_web (sì/no)

### Step 3 — Obiettivi e Urgenza
- obiettivo_principale (dropdown: più clienti, più visibilità online, migliorare reputazione, automatizzare processi, altro)
- urgenza (1-5 scala)
- budget_mensile_indicativo (range: 0-200, 200-500, 500-1000, 1000+)

### Step 4 — Contatto
- nome_contatto (obbligatorio)
- email (obbligatorio, validazione formato)
- telefono (obbligatorio, validazione formato italiano)
- consenso_privacy (checkbox obbligatoria)
- consenso_marketing (checkbox opzionale)

## Flusso di Esecuzione

1. Validazione — Controlla campi obbligatori e formati (email, telefono). Se errore, risposta 422 con dettagli.
2. Deduplicazione — Cerca in Supabase lead con stessa email. Se esiste e status diverso da "errore", aggiorna record esistente. Se esiste con status "errore", resetta e riprocessa.
3. Salvataggio — Inserisci in tabella leads su Supabase con status = "new".
4. Trigger Pipeline — Invia task Celery task_free_report con lead_id. Aggiorna status = "processing".
5. Risposta — Restituisci JSON con workflow_id e redirect URL per pagina di attesa.

## Output
Risposta JSON:
- status: "accepted"
- workflow_id: "uuid-del-lead"
- redirect: "/diagnosi-completata?id=uuid-del-lead"

## Gestione Errori
- Validazione fallita: 422 + dettagli campo
- Supabase non raggiungibile: 503 + retry automatico (max 3)
- Celery non raggiungibile: salva lead con status "queued", cron job riprova ogni 5 minuti

## Sicurezza
- Rate limit: max 5 richieste per IP al minuto
- Honeypot field nascosto per bot
- Validazione server-side (mai fidarsi del frontend)
- Sanitizzazione input (no SQL injection, no XSS)

## File di Esecuzione Collegati
- execution/lead_intake.py
- execution/validators.py

## Metriche da Tracciare
- Numero lead/giorno
- Tasso completamento form (step 1 a 4)
- Lead duplicati
- Errori di validazione più frequenti