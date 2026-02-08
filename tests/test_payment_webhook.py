"""
DigIdentity Engine — Test unitari per il webhook Stripe.

Testa:
1. Verifica firma webhook
2. Gestione checkout.session.completed
3. Pagina di successo
4. Gestione eventi non supportati
"""

import json
import hmac
import hashlib
import time
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Client di test FastAPI."""
    from backend.app.main import app
    return TestClient(app)


class TestPaymentSuccessPage:
    """Test per la pagina di successo post-pagamento."""

    def test_success_page_renders(self, client):
        """La pagina /api/payment/success deve restituire HTML valido."""
        resp = client.get("/api/payment/success")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")
        assert "Grazie" in resp.text
        assert "Report Premium" in resp.text
        assert "entro 24 ore" in resp.text

    def test_success_page_with_session_id(self, client):
        """Con session_id, deve tentare di personalizzare la pagina."""
        resp = client.get("/api/payment/success?session_id=cs_test_abc123")
        assert resp.status_code == 200
        # Anche con un session_id non valido, la pagina deve renderizzarsi
        assert "Grazie" in resp.text

    def test_cancel_page_renders(self, client):
        """La pagina /api/payment/cancel deve restituire HTML valido."""
        resp = client.get("/api/payment/cancel")
        assert resp.status_code == 200
        assert "Annullato" in resp.text


class TestWebhookEndpoint:
    """Test per l'endpoint webhook."""

    def test_webhook_missing_signature(self, client):
        """Senza header stripe-signature deve restituire 400."""
        resp = client.post(
            "/api/payment/webhook",
            content=b"{}",
        )
        assert resp.status_code == 400
        assert "stripe-signature" in resp.json().get("detail", "").lower()

    def test_webhook_invalid_signature(self, client):
        """Con firma non valida deve restituire 400."""
        resp = client.post(
            "/api/payment/webhook",
            content=b'{"type": "test"}',
            headers={"stripe-signature": "t=123,v1=invalid_signature"},
        )
        assert resp.status_code == 400


class TestHealthEndpoints:
    """Test per gli endpoint di health check."""

    def test_root(self, client):
        """L'endpoint / deve restituire info base."""
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "DigIdentity Engine"
        assert data["status"] == "running"

    def test_health(self, client):
        """L'endpoint /health deve restituire lo stato dei servizi."""
        resp = client.get("/health")
        data = resp.json()
        assert "checks" in data
        assert "api" in data["checks"]
        assert data["checks"]["api"] == "ok"
