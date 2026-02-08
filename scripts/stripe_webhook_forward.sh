#!/bin/bash
# ============================================================
# DigIdentity Engine — Stripe CLI Webhook Forwarding
# ============================================================
#
# Questo script avvia il forwarding dei webhook Stripe verso
# il backend locale per lo sviluppo.
#
# PREREQUISITI:
#   1. Stripe CLI installata:
#      - macOS: brew install stripe/stripe-cli/stripe
#      - Linux: vedi https://stripe.com/docs/stripe-cli#install
#      - Windows: scoop install stripe
#
#   2. Login effettuato:
#      stripe login
#
# USO:
#   ./scripts/stripe_webhook_forward.sh
#
# Il webhook secret verrà stampato a schermo. Copialo nel .env:
#   STRIPE_WEBHOOK_SECRET=whsec_...
#
# ============================================================

set -e

# Configurazione
BACKEND_URL="http://127.0.0.1:8080/api/payment/webhook"
EVENTS="checkout.session.completed,payment_intent.succeeded,payment_intent.payment_failed"

echo "============================================================"
echo "  DigIdentity Engine — Stripe Webhook Forwarding"
echo "============================================================"
echo ""
echo "  Endpoint: ${BACKEND_URL}"
echo "  Eventi:   ${EVENTS}"
echo ""
echo "============================================================"

# Verifica che Stripe CLI sia installata
if ! command -v stripe &> /dev/null; then
    echo ""
    echo "❌ ERRORE: Stripe CLI non trovata!"
    echo ""
    echo "Installa Stripe CLI:"
    echo "  macOS:   brew install stripe/stripe-cli/stripe"
    echo "  Linux:   Scarica da https://github.com/stripe/stripe-cli/releases"
    echo "  Windows: scoop install stripe"
    echo ""
    echo "Poi esegui: stripe login"
    exit 1
fi

# Verifica che il backend sia raggiungibile
echo "Verifico connessione al backend..."
if curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8080/health" | grep -q "200\|503"; then
    echo "✅ Backend raggiungibile"
else
    echo "⚠️  ATTENZIONE: Il backend non sembra raggiungibile su http://127.0.0.1:8080"
    echo "   Assicurati che il server FastAPI sia avviato:"
    echo "   uvicorn backend.app.main:app --host 0.0.0.0 --port 8080 --reload"
    echo ""
    echo "   Proseguo comunque con il forwarding..."
fi

echo ""
echo "🚀 Avvio forwarding webhook..."
echo ""
echo "⚠️  IMPORTANTE: Copia il 'webhook signing secret' (whsec_...) che appare"
echo "   qui sotto e aggiornalo nel file .env come STRIPE_WEBHOOK_SECRET"
echo ""
echo "------------------------------------------------------------"

# Avvia il forwarding
stripe listen \
    --forward-to "${BACKEND_URL}" \
    --events "${EVENTS}"
