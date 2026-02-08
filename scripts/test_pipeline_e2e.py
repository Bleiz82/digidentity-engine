#!/usr/bin/env python3
"""
DigIdentity Engine — Test End-to-End della Pipeline

Testa il flusso completo:
1. Submit lead via API
2. Verifica stato su Supabase
3. (Opzionale) Simula pagamento Stripe
4. Verifica generazione report

USO:
    # Test pipeline free
    python scripts/test_pipeline_e2e.py --mode free

    # Test pipeline completa (richiede Stripe CLI attivo)
    python scripts/test_pipeline_e2e.py --mode full

    # Test solo webhook
    python scripts/test_pipeline_e2e.py --mode webhook --lead-id <UUID>
"""

import argparse
import json
import sys
import time
from pathlib import Path

import requests

# Aggiungi la root del progetto al path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BASE_URL = "http://127.0.0.1:8080"


def test_health():
    """Verifica che il backend sia attivo."""
    print("\n{'='*60}")
    print("  TEST 1: Health Check")
    print("{'='*60}")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        data = resp.json()
        print(f"  Status: {data.get('status')}")
        for key, val in data.get("checks", {}).items():
            icon = "✅" if val not in ("missing",) else "❌"
            print(f"  {icon} {key}: {val}")
        return resp.status_code in (200, 503)
    except Exception as e:
        print(f"  ❌ Backend non raggiungibile: {e}")
        return False


def test_create_lead(
    company_name: str = "Test Pizzeria Da Mario",
    website_url: str = "https://www.example.com",
    email: str = "test@example.com",
):
    """Crea un lead di test via API."""
    print(f"\n{'='*60}")
    print("  TEST 2: Creazione Lead")
    print(f"{'='*60}")

    payload = {
        "company_name": company_name,
        "website_url": website_url,
        "email": email,
        "contact_name": "Mario Rossi",
        "sector": "Ristorazione",
    }

    try:
        resp = requests.post(
            f"{BASE_URL}/api/leads/",
            json=payload,
            timeout=10,
        )
        data = resp.json()
        print(f"  Status code: {resp.status_code}")
        print(f"  Response: {json.dumps(data, indent=2)}")

        if resp.status_code == 201:
            lead_id = data.get("id")
            print(f"  ✅ Lead creato: {lead_id}")
            return lead_id
        else:
            print(f"  ❌ Errore creazione lead: {data}")
            return None
    except Exception as e:
        print(f"  ❌ Errore: {e}")
        return None


def test_lead_status(lead_id: str):
    """Controlla lo stato di un lead."""
    print(f"\n{'='*60}")
    print(f"  TEST 3: Stato Lead {lead_id[:8]}...")
    print(f"{'='*60}")

    try:
        resp = requests.get(f"{BASE_URL}/api/leads/{lead_id}", timeout=5)
        data = resp.json()
        status = data.get("status", "unknown")
        print(f"  Status: {status}")
        print(f"  Company: {data.get('company_name')}")
        print(f"  Email: {data.get('email')}")

        if data.get("stripe_session_id"):
            print(f"  Stripe Session: {data['stripe_session_id']}")
        if data.get("error_message"):
            print(f"  ⚠️  Errore: {data['error_message']}")

        return data
    except Exception as e:
        print(f"  ❌ Errore: {e}")
        return None


def test_poll_status(lead_id: str, target_status: str, timeout: int = 300):
    """Polling dello stato del lead fino al raggiungimento dello stato target."""
    print(f"\n{'='*60}")
    print(f"  POLLING: Attendo stato '{target_status}' (timeout: {timeout}s)")
    print(f"{'='*60}")

    start = time.time()
    last_status = ""

    while time.time() - start < timeout:
        try:
            resp = requests.get(f"{BASE_URL}/api/leads/{lead_id}", timeout=5)
            data = resp.json()
            current_status = data.get("status", "unknown")

            if current_status != last_status:
                elapsed = int(time.time() - start)
                print(f"  [{elapsed:3d}s] Status: {current_status}")
                last_status = current_status

            if current_status == target_status:
                print(f"  ✅ Stato '{target_status}' raggiunto!")
                return True

            if current_status == "error":
                print(f"  ❌ Pipeline in errore: {data.get('error_message')}")
                return False

        except Exception:
            pass

        time.sleep(5)

    print(f"  ⏰ Timeout raggiunto. Ultimo stato: {last_status}")
    return False


def test_checkout_url(lead_id: str):
    """Crea una checkout session per il lead."""
    print(f"\n{'='*60}")
    print(f"  TEST: Creazione Checkout Session")
    print(f"{'='*60}")

    try:
        resp = requests.post(
            f"{BASE_URL}/api/payment/create-checkout",
            json={"lead_id": lead_id},
            timeout=10,
        )
        data = resp.json()
        print(f"  Status code: {resp.status_code}")

        if "checkout_url" in data:
            print(f"  ✅ Checkout URL: {data['checkout_url']}")
            print(f"  Session ID: {data['session_id']}")
            return data["checkout_url"]
        else:
            print(f"  ❌ Errore: {data}")
            return None
    except Exception as e:
        print(f"  ❌ Errore: {e}")
        return None


def test_success_page():
    """Verifica che la pagina di successo sia raggiungibile."""
    print(f"\n{'='*60}")
    print("  TEST: Pagina Success")
    print(f"{'='*60}")

    try:
        resp = requests.get(
            f"{BASE_URL}/api/payment/success",
            params={"session_id": "cs_test_dummy"},
            timeout=5,
        )
        print(f"  Status code: {resp.status_code}")
        print(f"  Content-Type: {resp.headers.get('content-type')}")

        if resp.status_code == 200 and "Grazie" in resp.text:
            print("  ✅ Pagina di successo funzionante")
            return True
        else:
            print("  ❌ Pagina di successo non corretta")
            return False
    except Exception as e:
        print(f"  ❌ Errore: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test E2E DigIdentity Pipeline")
    parser.add_argument(
        "--mode",
        choices=["free", "full", "webhook", "health"],
        default="health",
        help="Modalità di test",
    )
    parser.add_argument("--lead-id", help="UUID del lead (per mode=webhook)")
    parser.add_argument("--company", default="Test Pizzeria Da Mario")
    parser.add_argument("--website", default="https://www.example.com")
    parser.add_argument("--email", default="test@example.com")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  DigIdentity Engine — Test End-to-End")
    print(f"  Modalità: {args.mode}")
    print("=" * 60)

    # Health check
    if not test_health():
        print("\n❌ Backend non disponibile. Avvia il server e riprova.")
        sys.exit(1)

    if args.mode == "health":
        print("\n✅ Health check completato.")
        return

    # Test success page
    test_success_page()

    if args.mode == "free":
        # Pipeline free: submit → scraping → AI → PDF → email
        lead_id = test_create_lead(args.company, args.website, args.email)
        if not lead_id:
            sys.exit(1)

        # Poll fino a free_sent o error
        success = test_poll_status(lead_id, "free_sent", timeout=300)
        test_lead_status(lead_id)

        if success:
            print("\n" + "=" * 60)
            print("  ✅ PIPELINE FREE COMPLETATA CON SUCCESSO!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("  ❌ PIPELINE FREE FALLITA")
            print("=" * 60)
            sys.exit(1)

    elif args.mode == "full":
        # Pipeline completa: free + payment + premium
        lead_id = test_create_lead(args.company, args.website, args.email)
        if not lead_id:
            sys.exit(1)

        # Attendi completamento free
        test_poll_status(lead_id, "free_sent", timeout=300)

        # Crea checkout URL
        checkout_url = test_checkout_url(lead_id)

        if checkout_url:
            print(f"\n{'='*60}")
            print("  AZIONE MANUALE RICHIESTA")
            print(f"{'='*60}")
            print(f"\n  1. Apri questo URL nel browser:")
            print(f"     {checkout_url}")
            print(f"\n  2. Usa la carta di test Stripe:")
            print(f"     Numero: 4242 4242 4242 4242")
            print(f"     Scadenza: qualsiasi data futura")
            print(f"     CVC: qualsiasi 3 cifre")
            print(f"\n  3. Completa il pagamento")
            print(f"\n  4. Verifica che il webhook venga ricevuto nei log")
            print(f"\n  Lead ID: {lead_id}")
            print(f"\n  Dopo il pagamento, esegui:")
            print(f"  python scripts/test_pipeline_e2e.py --mode webhook --lead-id {lead_id}")

    elif args.mode == "webhook":
        if not args.lead_id:
            print("❌ Specifica --lead-id per la modalità webhook")
            sys.exit(1)

        print(f"\n  Monitoraggio lead {args.lead_id} per completamento premium...")
        success = test_poll_status(args.lead_id, "premium_sent", timeout=600)
        test_lead_status(args.lead_id)

        if success:
            print("\n" + "=" * 60)
            print("  ✅ PIPELINE PREMIUM COMPLETATA CON SUCCESSO!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("  ❌ PIPELINE PREMIUM FALLITA")
            print("=" * 60)
            sys.exit(1)


if __name__ == "__main__":
    main()
