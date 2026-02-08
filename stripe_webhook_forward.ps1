# ==============================================================================
# DigIdentity Engine — Stripe Webhook Forwarding (sviluppo locale)
# ==============================================================================
#
# PREREQUISITI:
#   1. Installa Stripe CLI: https://stripe.com/docs/stripe-cli
#      - Windows:  scoop install stripe  (oppure scarica da GitHub Releases)
#      - macOS:    brew install stripe/stripe-cli/stripe
#      - Linux:    vedi docs Stripe CLI
#
#   2. Effettua il login la prima volta:
#      stripe login
#      (si aprira' il browser — autorizza l'accesso al tuo account Stripe)
#
#   3. Assicurati che il backend FastAPI sia in esecuzione su porta 8080:
#      uvicorn backend.app.main:app --host 127.0.0.1 --port 8080 --reload
#
# USO:
#   .\stripe_webhook_forward.ps1
#
# NOTA IMPORTANTE:
#   Quando lanci questo script, Stripe CLI stampera' in console un
#   webhook signing secret (whsec_...). Copia quel valore e incollalo
#   nel tuo file .env alla voce STRIPE_WEBHOOK_SECRET, poi riavvia il backend.
#
#   Esempio output:
#     > Ready! Your webhook signing secret is whsec_xxxxxxxxxxxxx
#
# NOTA: Esiste anche una versione Bash in scripts/stripe_webhook_forward.sh
#
# ==============================================================================

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  DigIdentity Engine - Stripe Webhook Forward" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Configurazione
$BackendUrl = "http://127.0.0.1:8080/api/payment/webhook"
$Events = "checkout.session.completed,payment_intent.succeeded,payment_intent.payment_failed"

# Verifica che Stripe CLI sia installato
try {
    $stripeVersion = & stripe --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Stripe CLI non trovato" }
    Write-Host "[OK] Stripe CLI trovato: $stripeVersion" -ForegroundColor Green
}
catch {
    Write-Host "[ERRORE] Stripe CLI non trovato!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Installa Stripe CLI:" -ForegroundColor Yellow
    Write-Host "  Windows: scoop install stripe" -ForegroundColor Gray
    Write-Host "  macOS:   brew install stripe/stripe-cli/stripe" -ForegroundColor Gray
    Write-Host "  Linux:   https://stripe.com/docs/stripe-cli" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Poi esegui: stripe login" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# Verifica che il backend sia raggiungibile
Write-Host ""
Write-Host "Verifico connessione al backend..." -ForegroundColor Gray
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8080/health" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "[OK] Backend raggiungibile (status: $($health.status))" -ForegroundColor Green
}
catch {
    Write-Host "[ATTENZIONE] Backend non raggiungibile su http://127.0.0.1:8080" -ForegroundColor Yellow
    Write-Host "  Assicurati che il server sia avviato:" -ForegroundColor Gray
    Write-Host "  uvicorn backend.app.main:app --host 127.0.0.1 --port 8080 --reload" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Proseguo comunque con il forwarding..." -ForegroundColor Gray
}

Write-Host ""
Write-Host "Endpoint:  $BackendUrl" -ForegroundColor Gray
Write-Host "Eventi:    $Events" -ForegroundColor Gray
Write-Host ""
Write-Host "IMPORTANTE: Copia il 'webhook signing secret' (whsec_...) mostrato qui sotto" -ForegroundColor Magenta
Write-Host "e aggiornalo nel file .env alla voce STRIPE_WEBHOOK_SECRET." -ForegroundColor Magenta
Write-Host ""
Write-Host "Premi Ctrl+C per interrompere il forwarding." -ForegroundColor Gray
Write-Host "-------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""

# Avvia Stripe CLI in modalita' listen + forward
stripe listen `
    --forward-to $BackendUrl `
    --events $Events
