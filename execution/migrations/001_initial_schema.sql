-- ============================================
-- DigIdentity Engine — Schema Database Supabase
-- v1.0 — Febbraio 2026
-- ============================================

-- Abilita estensioni necessarie
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- TABELLA: leads
-- ============================================
CREATE TABLE IF NOT EXISTS leads (
    -- Identificativo
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Dati contatto
    nome_contatto TEXT NOT NULL,
    email TEXT NOT NULL,
    telefono TEXT NOT NULL,
    
    -- Dati azienda
    nome_azienda TEXT NOT NULL,
    settore_attivita TEXT NOT NULL,
    sito_web TEXT,
    citta TEXT NOT NULL,
    provincia TEXT NOT NULL,
    
    -- Presenza online attuale
    ha_google_my_business BOOLEAN DEFAULT false,
    ha_social_attivi BOOLEAN DEFAULT false,
    piattaforme_social JSONB DEFAULT '[]'::jsonb,
    ha_sito_web BOOLEAN DEFAULT false,
    
    -- Obiettivi e budget
    obiettivo_principale TEXT,
    urgenza INTEGER CHECK (urgenza >= 1 AND urgenza <= 5),
    budget_mensile_indicativo TEXT,
    
    -- Consensi
    consenso_privacy BOOLEAN NOT NULL DEFAULT false,
    consenso_marketing BOOLEAN DEFAULT false,
    
    -- Status workflow
    status TEXT NOT NULL DEFAULT 'new',
    
    -- Analisi gratuita (JSONB)
    analysis_pagespeed JSONB,
    analysis_serp JSONB,
    analysis_gmb JSONB,
    analysis_social JSONB,
    analysis_competitors JSONB,
    
    -- Analisi premium (JSONB)
    analysis_site_deep JSONB,
    analysis_seo_deep JSONB,
    analysis_reputation JSONB,
    analysis_social_deep JSONB,
    analysis_ai_opportunities JSONB,
    
    -- Score calcolati (0-100)
    score_sito_web INTEGER CHECK (score_sito_web >= 0 AND score_sito_web <= 100),
    score_seo INTEGER CHECK (score_seo >= 0 AND score_seo <= 100),
    score_gmb INTEGER CHECK (score_gmb >= 0 AND score_gmb <= 100),
    score_social INTEGER CHECK (score_social >= 0 AND score_social <= 100),
    score_competitivo INTEGER CHECK (score_competitivo >= 0 AND score_competitivo <= 100),
    score_totale INTEGER CHECK (score_totale >= 0 AND score_totale <= 100),
    
    -- Tracking
    ip_address TEXT,
    user_agent TEXT,
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    
    -- Timestamp
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    report_sent_at TIMESTAMPTZ,
    premium_sent_at TIMESTAMPTZ,
    
    -- Constraint
    CONSTRAINT email_unique UNIQUE (email)
);

-- Indici per performance
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at);
CREATE INDEX IF NOT EXISTS idx_leads_citta ON leads(citta);
CREATE INDEX IF NOT EXISTS idx_leads_settore ON leads(settore_attivita);

-- Trigger per aggiornare updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- TABELLA: reports
-- ============================================
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    report_type TEXT NOT NULL CHECK (report_type IN ('free', 'premium')),
    
    -- Contenuto
    html_content TEXT,
    pdf_path TEXT,
    
    -- Metadata AI
    ai_model_used TEXT,
    ai_tokens_used INTEGER,
    ai_cost_estimated DECIMAL(10, 4),
    generation_time_seconds INTEGER,
    
    -- Status
    status TEXT NOT NULL DEFAULT 'generating' CHECK (status IN ('generating', 'completed', 'error')),
    error_message TEXT,
    
    -- Timestamp
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indici
CREATE INDEX IF NOT EXISTS idx_reports_lead_id ON reports(lead_id);
CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(report_type);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);

-- ============================================
-- TABELLA: payments
-- ============================================
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    
    -- Stripe
    stripe_session_id TEXT,
    stripe_payment_intent TEXT,
    
    -- Importo
    amount DECIMAL(10, 2) NOT NULL DEFAULT 99.00,
    currency TEXT NOT NULL DEFAULT 'EUR',
    
    -- Status
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    payment_method TEXT DEFAULT 'stripe',
    
    -- Timestamp
    created_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

-- Indici
CREATE INDEX IF NOT EXISTS idx_payments_lead_id ON payments(lead_id);
CREATE INDEX IF NOT EXISTS idx_payments_stripe_session ON payments(stripe_session_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);

-- ============================================
-- TABELLA: analytics_events
-- ============================================
CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    
    -- Evento
    event_type TEXT NOT NULL,
    event_data JSONB DEFAULT '{}'::jsonb,
    
    -- Tracking
    ip_address TEXT,
    
    -- Timestamp
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indici
CREATE INDEX IF NOT EXISTS idx_analytics_lead_id ON analytics_events(lead_id);
CREATE INDEX IF NOT EXISTS idx_analytics_event_type ON analytics_events(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_created_at ON analytics_events(created_at);

-- ============================================
-- VIEW: KPI Summary
-- ============================================
CREATE OR REPLACE VIEW view_kpi_summary AS
SELECT
    COUNT(*) AS total_leads,
    COUNT(*) FILTER (WHERE l.created_at >= date_trunc('month', CURRENT_DATE)) AS leads_this_month,
    COUNT(*) FILTER (WHERE l.status = 'converted') AS total_conversions,
    COALESCE(SUM(p.amount) FILTER (WHERE p.status = 'completed'), 0) AS total_revenue
FROM leads l
LEFT JOIN payments p ON l.id = p.lead_id;

-- ============================================
-- VIEW: Funnel
-- ============================================
CREATE OR REPLACE VIEW view_funnel AS
SELECT
    l.status,
    COUNT(*) AS count
FROM leads l
GROUP BY l.status
ORDER BY 
    CASE l.status
        WHEN 'new' THEN 1
        WHEN 'processing' THEN 2
        WHEN 'analysis_complete' THEN 3
        WHEN 'free_report_generated' THEN 4
        WHEN 'free_report_sent' THEN 5
        WHEN 'payment_pending' THEN 6
        WHEN 'payment_confirmed' THEN 7
        WHEN 'premium_processing' THEN 8
        WHEN 'premium_report_generated' THEN 9
        WHEN 'premium_report_sent' THEN 10
        WHEN 'converted' THEN 11
        WHEN 'error' THEN 12
        ELSE 99
    END;

-- ============================================
-- VIEW: Daily Stats
-- ============================================
CREATE OR REPLACE VIEW view_daily_stats AS
SELECT
    DATE(l.created_at) AS date,
    COUNT(*) AS leads_count,
    COALESCE(SUM(p.amount) FILTER (WHERE p.status = 'completed'), 0) AS revenue
FROM leads l
LEFT JOIN payments p ON l.id = p.lead_id
WHERE l.created_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE(l.created_at)
ORDER BY date DESC;

-- ============================================
-- Row Level Security (RLS)
-- ============================================
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics_events ENABLE ROW LEVEL SECURITY;

-- Policy: accesso solo tramite service_role key
CREATE POLICY "Service role full access on leads" ON leads
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access on reports" ON reports
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access on payments" ON payments
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access on analytics_events" ON analytics_events
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================
-- COMMENTI
-- ============================================
COMMENT ON TABLE leads IS 'Tabella principale dei lead raccolti dal form della Diagnosi Strategica Digitale';
COMMENT ON TABLE reports IS 'Report generati (gratuiti e premium) con metadata AI';
COMMENT ON TABLE payments IS 'Pagamenti Stripe per diagnosi premium (99 euro)';
COMMENT ON TABLE analytics_events IS 'Eventi di tracking per analytics e funnel analysis';

COMMENT ON COLUMN leads.status IS 'Stati possibili: new, processing, analysis_complete, free_report_generated, free_report_sent, payment_pending, payment_confirmed, premium_processing, premium_report_generated, premium_report_sent, converted, error';
