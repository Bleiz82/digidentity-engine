FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpango-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 libffi-dev shared-mime-info \
    libcairo2 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir apify-client requests beautifulsoup4 markdown

COPY backend/ /app/backend/
COPY execution/ /app/execution/
COPY engine/ /app/engine/
COPY assets/ /app/assets/

RUN mkdir -p /app/reports/free /app/reports/premium

ENV PYTHONPATH=/app:/app/backend
EXPOSE 8080

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
