-- ============================================================
-- DigIdentity Engine — Schema Completo Supabase
-- ============================================================

-- TABELLA LEADS
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome_contatto TEXT NOT NULL,
    email TEXT NOT NULL,
    telefono TEXT,
    nome_azienda TEXT NOT NULL,
    settore_attivita TEXT DEFAULT 'Da identificare',
    sito_web TEXT,
    ha_sito_web BOOLEAN DEFAULT false,
    citta TEXT,
    provincia TEXT,
    urgenza INTEGER DEFAULT 3,
    budget_mensile_indicativo TEXT,
    
    -- Consensi
    consenso_privacy BOOLEAN DEFAULT false,
    consenso_marketing BOOLEAN DEFAULT false,
    
    -- Tracking
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    utm_content TEXT,
    ip_address TEXT,
    user_agent TEXT,
    
    -- Status pipeline
    status TEXT DEFAULT 'new' CHECK (status IN (
        'new', 'processing', 'scraping', 'analyzing', 'generating',
        'analysis_complete', 'free_report_generated', 'free_report_sent',
        'payment_pending', 'payment_confirmed', 'premium_processing',
        'converted', 'error'
    )),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Dati scraping
    analysis_pagespeed JSONB,
    analysis_serp JSONB,
    analysis_gmb JSONB,
    analysis_social JSONB,
    analysis_competitors JSONB,
    analysis_deep_site JSONB,
    analysis_ai_opportunities JSONB,
    
    -- Score
    score_sito_web INTEGER DEFAULT 0,
    score_seo INTEGER DEFAULT 0,
    score_gmb INTEGER DEFAULT 0,
    score_social INTEGER DEFAULT 0,
    score_competitivo INTEGER DEFAULT 0,
    score_totale INTEGER DEFAULT 0,
    
    -- Report AI
    free_report_sections JSONB,
    free_report_metadata JSONB,
    premium_report_sections JSONB,
    premium_report_metadata JSONB,
    
    -- PDF
    pdf_free_path TEXT,
    pdf_free_filename TEXT,
    pdf_free_size INTEGER,
    pdf_premium_path TEXT,
    pdf_premium_filename TEXT,
    pdf_premium_size INTEGER,
    
    -- Delivery
    email_free_sent BOOLEAN DEFAULT false,
    email_free_sent_at TIMESTAMPTZ,
    email_premium_sent BOOLEAN DEFAULT false,
    email_premium_sent_at TIMESTAMPTZ,
    whatsapp_free_sent BOOLEAN DEFAULT false,
    whatsapp_free_sent_at TIMESTAMPTZ,
    whatsapp_free_message_id TEXT,
    whatsapp_premium_sent BOOLEAN DEFAULT false,
    whatsapp_premium_sent_at TIMESTAMPTZ,
    whatsapp_premium_message_id TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

-- Indici per performance
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_provincia ON leads(provincia);
CREATE INDEX IF NOT EXISTS idx_leads_score_totale ON leads(score_totale);

-- TABELLA PAYMENTS
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    stripe_session_id TEXT,
    stripe_payment_intent TEXT,
    stripe_customer_id TEXT,
    amount DECIMAL(10,2) DEFAULT 99.00,
    currency TEXT DEFAULT 'EUR',
    status TEXT DEFAULT 'pending' CHECK (status IN (
        'pending', 'completed', 'failed', 'refunded'
    )),
    product TEXT DEFAULT 'diagnosi_premium',
    invoice_number TEXT,
    invoice_sent BOOLEAN DEFAULT false,
    invoice_sent_at TIMESTAMPTZ,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_payments_lead_id ON payments(lead_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_stripe_session ON payments(stripe_session_id);

-- TABELLA REPORTS (log di ogni report generato)
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('free', 'premium')),
    ai_model TEXT,
    ai_tokens_input INTEGER,
    ai_tokens_output INTEGER,
    ai_total_tokens INTEGER,
    ai_cost_usd DECIMAL(10,4),
    pdf_path TEXT,
    pdf_filename TEXT,
    pdf_size_bytes INTEGER,
    sections JSONB,
    generation_time_seconds DECIMAL(10,2),
    status TEXT DEFAULT 'generated' CHECK (status IN (
        'generating', 'generated', 'sent', 'error'
    )),
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_reports_lead_id ON reports(lead_id);
CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(type);

-- ============================================================
-- VISTE DASHBOARD
-- ============================================================

-- VISTA 1: KPI Overview
CREATE OR REPLACE VIEW dashboard_kpi AS
SELECT
    COUNT(*) AS lead_totali,
    COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE) AS lead_oggi,
    COUNT(*) FILTER (WHERE created_at >= date_trunc('week', CURRENT_DATE)) AS lead_settimana,
    COUNT(*) FILTER (WHERE created_at >= date_trunc('month', CURRENT_DATE)) AS lead_mese,
    COUNT(*) FILTER (WHERE status = 'free_report_sent') AS diagnosi_free_inviate,
    COUNT(*) FILTER (WHERE status = 'converted') AS diagnosi_premium_completate,
    COUNT(*) FILTER (WHERE status = 'error') AS lead_in_errore,
    COUNT(*) FILTER (WHERE status = 'processing') AS lead_in_elaborazione,
    ROUND(
        COUNT(*) FILTER (WHERE status = 'converted')::DECIMAL /
        NULLIF(COUNT(*) FILTER (WHERE status IN ('free_report_sent', 'payment_pending', 'payment_confirmed', 'converted')), 0) * 100, 1
    ) AS tasso_conversione_percent,
    AVG(score_totale) FILTER (WHERE score_totale > 0) AS score_medio,
    SUM(CASE WHEN status = 'converted' THEN 99.00 ELSE 0 END) AS revenue_totale_eur
FROM leads;

-- VISTA 2: Pipeline Lead (lista completa)
CREATE OR REPLACE VIEW dashboard_lead_pipeline AS
SELECT
    id,
    nome_azienda,
    nome_contatto,
    email,
    telefono,
    citta,
    provincia,
    settore_attivita,
    status,
    score_totale,
    score_sito_web,
    score_seo,
    score_gmb,
    score_social,
    score_competitivo,
    ha_sito_web,
    email_free_sent,
    email_premium_sent,
    whatsapp_free_sent,
    error_message,
    created_at,
    updated_at,
    completed_at
FROM leads
ORDER BY created_at DESC;

-- VISTA 3: Diagnosi generate (report log)
CREATE OR REPLACE VIEW dashboard_diagnosi AS
SELECT
    r.id AS report_id,
    r.lead_id,
    l.nome_azienda,
    l.nome_contatto,
    l.email,
    r.type AS tipo_report,
    r.ai_model,
    r.ai_total_tokens,
    r.ai_cost_usd,
    r.pdf_filename,
    r.pdf_size_bytes,
    r.generation_time_seconds,
    r.status AS report_status,
    r.created_at AS report_generato_il
FROM reports r
JOIN leads l ON r.lead_id = l.id
ORDER BY r.created_at DESC;

-- VISTA 4: Pagamenti e Fatturazione
CREATE OR REPLACE VIEW dashboard_pagamenti AS
SELECT
    p.id AS payment_id,
    p.lead_id,
    l.nome_azienda,
    l.nome_contatto,
    l.email,
    l.telefono,
    l.citta,
    l.provincia,
    p.amount,
    p.currency,
    p.status AS stato_pagamento,
    p.stripe_session_id,
    p.stripe_payment_intent,
    p.invoice_number,
    p.invoice_sent,
    p.invoice_sent_at,
    p.product,
    p.completed_at AS pagamento_completato_il,
    p.created_at AS pagamento_creato_il
FROM payments p
JOIN leads l ON p.lead_id = l.id
ORDER BY p.created_at DESC;

-- VISTA 5: Revenue mensile
CREATE OR REPLACE VIEW dashboard_revenue_mensile AS
SELECT
    date_trunc('month', completed_at) AS mese,
    COUNT(*) AS transazioni,
    SUM(amount) AS revenue_eur,
    AVG(amount) AS ticket_medio
FROM payments
WHERE status = 'completed'
GROUP BY date_trunc('month', completed_at)
ORDER BY mese DESC;

-- VISTA 6: Lead per provincia (mappa)
CREATE OR REPLACE VIEW dashboard_lead_per_provincia AS
SELECT
    provincia,
    COUNT(*) AS totale_lead,
    COUNT(*) FILTER (WHERE status = 'converted') AS conversioni,
    AVG(score_totale) FILTER (WHERE score_totale > 0) AS score_medio,
    ROUND(
        COUNT(*) FILTER (WHERE status = 'converted')::DECIMAL /
        NULLIF(COUNT(*), 0) * 100, 1
    ) AS tasso_conversione_percent
FROM leads
WHERE provincia IS NOT NULL
GROUP BY provincia
ORDER BY totale_lead DESC;

-- VISTA 7: Costi AI
CREATE OR REPLACE VIEW dashboard_costi_ai AS
SELECT
    date_trunc('month', created_at) AS mese,
    type AS tipo_report,
    COUNT(*) AS report_generati,
    SUM(ai_total_tokens) AS tokens_totali,
    SUM(ai_cost_usd) AS costo_totale_usd,
    AVG(ai_cost_usd) AS costo_medio_per_report,
    AVG(generation_time_seconds) AS tempo_medio_generazione_sec
FROM reports
GROUP BY date_trunc('month', created_at), type
ORDER BY mese DESC, type;

-- Row Level Security (opzionale, per sicurezza)
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;

-- Policy: service_role può fare tutto
CREATE POLICY "Service role full access leads" ON leads
    FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access payments" ON payments
    FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access reports" ON reports
    FOR ALL USING (true) WITH CHECK (true);
