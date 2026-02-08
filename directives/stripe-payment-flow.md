# DIRETTIVA: Flusso Pagamento Stripe

## Versione
v1.0 — Febbraio 2026

## Obiettivo
Gestire il pagamento di 99 euro per la Diagnosi Premium tramite Stripe Checkout, con webhook per attivare la pipeline premium.

## Trigger
Lead clicca CTA "Ottieni la Diagnosi Completa" nel report gratuito o nella email.

## Flusso

### 1. Creazione Checkout Session
- Endpoint: POST /api/create-checkout-session/{lead_id}
- Verifica che lead esista e abbia status "free_report_sent"
- Crea Stripe Checkout Session:
  - Importo: 99.00 EUR
  - Prodotto: "Diagnosi Strategica Digitale Premium"
  - Descrizione: "Report completo 40-50 pagine con piano strategico e preventivo personalizzato"
  - success_url: https://digidentityagency.it/diagnosi-premium-confermata?session_id={CHECKOUT_SESSION_ID}
  - cancel_url: https://digidentityagency.it/diagnosi-strategica-digitale
  - metadata: lead_id
  - customer_email: email del lead (pre-compilata)
- Aggiorna status lead a "payment_pending"
- Restituisci URL checkout Stripe

### 2. Webhook Pagamento Confermato
- Endpoint: POST /api/payment-webhook
- Evento: checkout.session.completed
- Verifica firma webhook Stripe (STRIPE_WEBHOOK_SECRET)
- Estrai lead_id da metadata
- Salva pagamento in tabella payments:
  - lead_id
  - stripe_session_id
  - stripe_payment_intent
  - amount: 99.00
  - currency: EUR
  - status: "completed"
  - created_at
- Aggiorna status lead a "payment_confirmed"
- Trigger task Celery task_premium_report con lead_id
- Rispondi 200 a Stripe

### 3. Pagina Conferma
- URL: /diagnosi-premium-confermata
- Mostra messaggio di conferma pagamento
- Avvia polling su /api/report-status/{lead_id} per mostrare progress bar
- Quando report pronto: mostra link download + conferma invio email

## Gestione Errori
- Webhook firma non valida: 400, logga tentativo sospetto
- Lead non trovato: 404, logga e notifica admin
- Pagamento duplicato (stesso lead): ignora, logga
- Stripe down: pagina di errore con messaggio "riprova tra qualche minuto"

## Sicurezza
- Webhook endpoint: verifica SEMPRE la firma Stripe
- Rate limit webhook: 30/s (separato dalle altre API)
- Non esporre mai Stripe secret key nel frontend
- Loggare ogni evento pagamento per audit

## Metodi di Pagamento Futuri
- PayPal: da integrare in Fase 2
- Klarna: da integrare in Fase 2
- Per ora solo Stripe (carta di credito/debito + Apple Pay + Google Pay)