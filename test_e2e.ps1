# ==============================================================================
# DigIdentity Engine — Test End-to-End della Pipeline (PowerShell)
# ==============================================================================
#
# Testa il flusso completo:
#   1. Health check del backend
#   2. Verifica pagina di successo pagamento
#   3. POST di un lead di test a /api/leads/
#   4. Attesa per il completamento della pipeline free
#   5. Verifica dello stato del lead
#   6. Istruzioni per il test del flusso premium (manuale)
#
# PREREQUISITI:
#   - Backend FastAPI in esecuzione su http://127.0.0.1:8080
#     uvicorn backend.app.main:app --host 127.0.0.1 --port 8080 --reload
#   - Redis in esecuzione (per Celery)
#   - Worker Celery avviato:
#     celery -A backend.app.core.celery_app worker --loglevel=info
#   - Per il flusso premium: avviare anche .\stripe_webhook_forward.ps1
#
# USO:
#   .\test_e2e.ps1                            # Test completo con attesa 120s
#   .\test_e2e.ps1 -SkipWait                  # Solo submit, nessuna attesa
#   .\test_e2e.ps1 -WaitSeconds 300           # Attesa 5 minuti
#   .\test_e2e.ps1 -BaseUrl "http://localhost:3000"
#
# NOTA: Esiste anche una versione Python piu' completa:
#   python scripts/test_pipeline_e2e.py --mode free
#   python scripts/test_pipeline_e2e.py --mode full
#
# ==============================================================================

param(
    [string]$BaseUrl = "http://127.0.0.1:8080",
    [switch]$SkipWait,
    [int]$WaitSeconds = 120
)

function Write-Step($step, $message) {
    Write-Host ""
    Write-Host "[$step] $message" -ForegroundColor Cyan
    Write-Host ("-" * 60) -ForegroundColor DarkGray
}

function Write-Ok($message) {
    Write-Host "  [OK] $message" -ForegroundColor Green
}

function Write-Fail($message) {
    Write-Host "  [FAIL] $message" -ForegroundColor Red
}

function Write-Info($message) {
    Write-Host "  [INFO] $message" -ForegroundColor Yellow
}

# ==============================================================================
# Banner
# ==============================================================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "  DigIdentity Engine - Test End-to-End Pipeline" -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "  Base URL: $BaseUrl" -ForegroundColor Gray
Write-Host "  Data:     $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

# ==============================================================================
# STEP 0 - Health check
# ==============================================================================
Write-Step "0" "Verifica connessione al backend..."

try {
    $healthCheck = Invoke-RestMethod -Uri "$BaseUrl/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Ok "Backend raggiungibile. Status: $($healthCheck.status)"

    if ($healthCheck.checks) {
        foreach ($prop in $healthCheck.checks.PSObject.Properties) {
            $icon = if ($prop.Value -ne "missing") { "[+]" } else { "[-]" }
            $color = if ($prop.Value -ne "missing") { "Green" } else { "Red" }
            Write-Host "       $icon $($prop.Name): $($prop.Value)" -ForegroundColor $color
        }
    }
}
catch {
    Write-Fail "Backend NON raggiungibile su $BaseUrl"
    Write-Info "Assicurati che il backend sia avviato:"
    Write-Info "  uvicorn backend.app.main:app --host 127.0.0.1 --port 8080 --reload"
    exit 1
}

# ==============================================================================
# STEP 0.5 - Verifica pagina di successo
# ==============================================================================
Write-Step "0.5" "Verifica pagina di successo /api/payment/success..."

try {
    $successPage = Invoke-WebRequest -Uri "$BaseUrl/api/payment/success?session_id=cs_test_dummy" -Method GET -TimeoutSec 5 -ErrorAction Stop -UseBasicParsing
    if ($successPage.StatusCode -eq 200 -and $successPage.Content -match "Pagamento Confermato") {
        Write-Ok "Pagina di successo funzionante (HTTP 200)"
    }
    else {
        Write-Fail "Pagina di successo: contenuto inatteso (HTTP $($successPage.StatusCode))"
    }
}
catch {
    Write-Fail "Pagina di successo non raggiungibile: $($_.Exception.Message)"
}

# ==============================================================================
# STEP 1 - Submit lead di test
# ==============================================================================
Write-Step "1" "Submit lead di test a POST /api/leads/ ..."

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$testLead = @{
    company_name = "Test PMI S.r.l. - $timestamp"
    website_url  = "https://www.example-pmi.it"
    email        = "test@digidentity-test.com"
    contact_name = "Mario Rossi"
    phone        = "+39 02 1234567"
    sector       = "Ristorazione"
    notes        = "Lead di test automatico E2E - $timestamp"
} | ConvertTo-Json -Depth 3

Write-Info "Payload:"
Write-Host $testLead -ForegroundColor DarkGray

try {
    $response = Invoke-RestMethod `
        -Uri "$BaseUrl/api/leads/" `
        -Method POST `
        -ContentType "application/json" `
        -Body $testLead `
        -TimeoutSec 30 `
        -ErrorAction Stop

    $leadId = $response.id

    if ($leadId) {
        Write-Ok "Lead creato con successo!"
        Write-Ok "Lead ID: $leadId"
        Write-Ok "Status:  $($response.status)"
        Write-Ok "Message: $($response.message)"
    }
    else {
        Write-Fail "Risposta ricevuta ma campo 'id' non trovato."
        Write-Info "Risposta:"
        Write-Host ($response | ConvertTo-Json -Depth 5) -ForegroundColor DarkGray
        exit 1
    }
}
catch {
    Write-Fail "Errore nella creazione del lead: $($_.Exception.Message)"
    if ($_.Exception.Response) {
        try {
            $statusCode = [int]$_.Exception.Response.StatusCode
            Write-Info "HTTP Status: $statusCode"
        } catch {}
    }
    exit 1
}

# ==============================================================================
# STEP 2 - Attesa pipeline free
# ==============================================================================
if ($SkipWait) {
    Write-Step "2" "Attesa SALTATA (-SkipWait)."
    Write-Info "Lead ID: $leadId"
}
else {
    Write-Step "2" "Attesa completamento pipeline free ($WaitSeconds secondi)..."
    Write-Info "Pipeline: scraping -> Claude AI report -> PDF -> invio email con CTA"
    Write-Info "Monitorare i log Celery in un terminale separato."
    Write-Host ""

    for ($i = 0; $i -lt $WaitSeconds; $i++) {
        $percent = [math]::Round(($i / $WaitSeconds) * 100)
        $bar = "#" * [math]::Floor($percent / 2)
        $empty = "-" * (50 - [math]::Floor($percent / 2))
        Write-Host "`r  [$bar$empty] $percent% ($i/$WaitSeconds s)" -NoNewline -ForegroundColor DarkYellow
        Start-Sleep -Seconds 1
    }
    Write-Host "`r  [##################################################] 100%                    " -ForegroundColor Green
    Write-Host ""
}

# ==============================================================================
# STEP 3 - Verifica stato del lead
# ==============================================================================
Write-Step "3" "Verifica stato del lead..."

try {
    $lead = Invoke-RestMethod `
        -Uri "$BaseUrl/api/leads/$leadId" `
        -Method GET `
        -TimeoutSec 10 `
        -ErrorAction Stop

    Write-Ok "Lead trovato nel sistema."
    Write-Host ""
    Write-Host "  Dettagli Lead:" -ForegroundColor White
    Write-Host "  |-- ID:        $($lead.id)" -ForegroundColor Gray
    Write-Host "  |-- Azienda:   $($lead.company_name)" -ForegroundColor Gray
    Write-Host "  |-- Status:    $($lead.status)" -ForegroundColor Gray
    Write-Host "  |-- Email:     $($lead.email)" -ForegroundColor Gray
    Write-Host "  |-- Creato:    $($lead.created_at)" -ForegroundColor Gray

    if ($lead.error_message) {
        Write-Host "  |-- ERRORE:    $($lead.error_message)" -ForegroundColor Red
    }
    if ($lead.stripe_session_id) {
        Write-Host "  |-- Stripe:    $($lead.stripe_session_id)" -ForegroundColor Gray
    }

    switch ($lead.status) {
        "free_sent" {
            Write-Host ""
            Write-Ok "PIPELINE FREE COMPLETATA CON SUCCESSO!"
            Write-Ok "Email con report free + CTA premium inviata a $($lead.email)"
        }
        "scraping"         { Write-Info "Scraping in corso. Aumentare -WaitSeconds." }
        "generating_free"  { Write-Info "Report AI in generazione. Quasi completato." }
        "error"            { Write-Fail "Pipeline in errore. Controllare log Celery." }
        "new"              { Write-Info "Lead in coda. Worker Celery attivo?" }
        "payment_completed" { Write-Info "Pagamento completato, report premium in generazione." }
        "generating_premium" { Write-Info "Report premium in generazione con Claude AI." }
        "premium_sent"     { Write-Ok "PIPELINE PREMIUM COMPLETATA!" }
        default            { Write-Info "Status: $($lead.status)" }
    }
}
catch {
    Write-Fail "Impossibile recuperare il lead: $($_.Exception.Message)"
    Write-Info "Verificare su Supabase: SELECT * FROM leads WHERE id = '$leadId'"
}

# ==============================================================================
# STEP 4 - Istruzioni test premium (manuale)
# ==============================================================================
Write-Step "4" "Per testare il flusso PREMIUM (manuale)"

Write-Host ""
Write-Host "  1. Avvia Stripe CLI webhook forwarding:" -ForegroundColor White
Write-Host "     .\stripe_webhook_forward.ps1" -ForegroundColor DarkCyan
Write-Host ""
Write-Host "  2. Crea checkout session:" -ForegroundColor White
Write-Host "     Invoke-RestMethod -Uri '$BaseUrl/api/payment/create-checkout' ``" -ForegroundColor DarkCyan
Write-Host "       -Method POST -ContentType 'application/json' ``" -ForegroundColor DarkCyan
Write-Host "       -Body '{""lead_id"":""$leadId"",""email"":""test@digidentity-test.com""}'" -ForegroundColor DarkCyan
Write-Host ""
Write-Host "  3. Apri la checkout_url nel browser e paga con:" -ForegroundColor White
Write-Host "     Numero:    4242 4242 4242 4242" -ForegroundColor Yellow
Write-Host "     Scadenza:  12/34" -ForegroundColor Yellow
Write-Host "     CVC:       123" -ForegroundColor Yellow
Write-Host ""
Write-Host "  4. Verifica:" -ForegroundColor White
Write-Host "     - Redirect a /api/payment/success" -ForegroundColor Gray
Write-Host "     - Webhook nel terminale Stripe CLI" -ForegroundColor Gray
Write-Host "     - task_premium_report nei log Celery" -ForegroundColor Gray
Write-Host ""
Write-Host "  5. Monitora premium:" -ForegroundColor White
Write-Host "     python scripts/test_pipeline_e2e.py --mode webhook --lead-id $leadId" -ForegroundColor DarkCyan

# ==============================================================================
# Risultato
# ==============================================================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "  Test completato. Lead ID: $leadId" -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host ""
