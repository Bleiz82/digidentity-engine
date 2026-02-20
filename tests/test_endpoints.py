"""
DigIdentity Engine — Test unitari per endpoint principali.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Client di test FastAPI."""
    from backend.app.main import app
    return TestClient(app)


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
        assert "openai" in data["checks"]
        assert "redis" in data["checks"]

    def test_security_headers(self, client):
        """Verifica che gli header di sicurezza siano presenti."""
        resp = client.get("/")
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "DENY"
        assert resp.headers.get("x-xss-protection") == "1; mode=block"
        assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


class TestPaymentPages:
    """Test per le pagine di pagamento."""

    def test_success_page_renders(self, client):
        """La pagina /api/payment/success deve restituire HTML valido."""
        resp = client.get("/api/payment/success")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_cancel_page_renders(self, client):
        """La pagina /api/payment/cancel deve restituire HTML valido."""
        resp = client.get("/api/payment/cancel")
        assert resp.status_code == 200
        assert "Annullato" in resp.text

    def test_webhook_missing_signature(self, client):
        """Senza header stripe-signature deve restituire 400."""
        resp = client.post("/api/payment/webhook", content=b"{}")
        assert resp.status_code == 400

    def test_create_checkout_missing_params(self, client):
        """Senza lead_id e email deve restituire 400."""
        resp = client.post("/api/payment/create-checkout", json={})
        assert resp.status_code == 400
