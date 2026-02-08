#!/bin/bash
# ============================================================
# DigIdentity Engine — Test Trigger Stripe Webhook
# ============================================================
#
# Invia eventi di test per verificare che il webhook handler
# funzioni correttamente.
#
# PREREQUISITI:
#   1. stripe_webhook_forward.sh in esecuzione in un altro terminale
#   2. Backend FastAPI avviato su porta 8080
#
# USO:
#   ./scripts/stripe_trigger_test.sh
# ============================================================

set -e

echo "============================================================"
echo "  DigIdentity Engine — Test Webhook Events"
echo "============================================================"
echo ""

# Verifica Stripe CLI
if ! command -v stripe &> /dev/null; then
    echo "❌ Stripe CLI non trovata. Installa e riprova."
    exit 1
fi

# Test 1: checkout.session.completed
echo "📤 Test 1: Invio checkout.session.completed..."
stripe trigger checkout.session.completed 2>&1
echo ""
echo "✅ Evento checkout.session.completed inviato"
echo ""

sleep 2

# Test 2: payment_intent.succeeded
echo "📤 Test 2: Invio payment_intent.succeeded..."
stripe trigger payment_intent.succeeded 2>&1
echo ""
echo "✅ Evento payment_intent.succeeded inviato"
echo ""

echo "============================================================"
echo "  Test completati!"
echo ""
echo "  Controlla i log del backend per verificare la ricezione:"
echo "  - Cerca 'Webhook Stripe ricevuto' nei log"
echo "  - Verifica lo stato del lead su Supabase"
echo "============================================================"
