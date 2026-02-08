# DigIdentity Engine — Makefile
# Comandi rapidi per sviluppo e deployment

.PHONY: help install run worker webhook test test-free test-full

help: ## Mostra questo help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Installa dipendenze Python
	pip install -r requirements.txt

run: ## Avvia il backend FastAPI
	uvicorn backend.app.main:app --host 0.0.0.0 --port 8080 --reload

worker: ## Avvia il worker Celery
	celery -A backend.app.core.celery_app worker --loglevel=info --concurrency=2

webhook: ## Avvia Stripe CLI webhook forwarding
	bash scripts/stripe_webhook_forward.sh

test: ## Esegui health check
	python scripts/test_pipeline_e2e.py --mode health

test-free: ## Testa la pipeline free end-to-end
	python scripts/test_pipeline_e2e.py --mode free

test-full: ## Testa la pipeline completa (free + premium)
	python scripts/test_pipeline_e2e.py --mode full

stripe-test: ## Invia eventi di test Stripe
	bash scripts/stripe_trigger_test.sh

redis: ## Avvia Redis (se non già in esecuzione)
	redis-server --daemonize yes

status: ## Controlla lo stato dei servizi
	@echo "=== Backend FastAPI ==="
	@curl -s http://127.0.0.1:8080/health | python -m json.tool 2>/dev/null || echo "❌ Non raggiungibile"
	@echo ""
	@echo "=== Redis ==="
	@redis-cli ping 2>/dev/null || echo "❌ Non raggiungibile"
	@echo ""
	@echo "=== Celery Workers ==="
	@celery -A backend.app.core.celery_app inspect ping 2>/dev/null || echo "❌ Nessun worker attivo"
