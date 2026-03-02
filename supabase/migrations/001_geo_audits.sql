-- Create geo_audits table
CREATE TABLE IF NOT EXISTS geo_audits (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url_sito              TEXT NOT NULL,
    email_cliente         TEXT NOT NULL,
    piano                 TEXT NOT NULL DEFAULT 'singolo',
    stripe_session_id     TEXT,
    stripe_payment_intent TEXT,
    status                TEXT NOT NULL DEFAULT 'pending',
    geo_score             INTEGER,
    pdf_path              TEXT,
    pdf_size_bytes        INTEGER,
    risultati_json        JSONB,
    email_sent            BOOLEAN DEFAULT FALSE,
    error_message         TEXT,
    created_at            TIMESTAMPTZ DEFAULT now(),
    started_at            TIMESTAMPTZ,
    completed_at          TIMESTAMPTZ
);

-- Indices for better performance
CREATE INDEX IF NOT EXISTS idx_geo_audits_email   ON geo_audits(email_cliente);
CREATE INDEX IF NOT EXISTS idx_geo_audits_status  ON geo_audits(status);
CREATE INDEX IF NOT EXISTS idx_geo_audits_created ON geo_audits(created_at DESC);

-- Update existing reports table
ALTER TABLE reports ADD COLUMN IF NOT EXISTS geo_audit_id UUID REFERENCES geo_audits(id);
ALTER TABLE reports ALTER COLUMN lead_id DROP NOT NULL;
