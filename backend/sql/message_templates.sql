
-- Esegui nel SQL Editor di Supabase
CREATE TABLE IF NOT EXISTS message_templates (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    channel TEXT NOT NULL DEFAULT 'whatsapp',
    category TEXT NOT NULL DEFAULT 'utility',
    content TEXT NOT NULL,
    placeholders JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indice per ricerche
CREATE INDEX IF NOT EXISTS idx_templates_channel ON message_templates(channel);
CREATE INDEX IF NOT EXISTS idx_templates_category ON message_templates(category);

-- Template di esempio
INSERT INTO message_templates (name, channel, category, content, placeholders) VALUES
('Conferma Appuntamento', 'whatsapp', 'utility', 
 'Ciao {{nome}}! 👋 Ti confermo l''appuntamento per la Diagnosi Strategica il {{data}} alle {{ora}}. Riceverai il link Google Meet via email. A presto! — Stefano, DigIdentity Agency',
 '["nome", "data", "ora"]'),
('Reminder 24h', 'whatsapp', 'utility',
 'Ciao {{nome}}, ti ricordo che domani alle {{ora}} hai la Diagnosi Strategica con Stefano. Se hai bisogno di spostare, rispondi a questo messaggio. A domani! 🚀',
 '["nome", "ora"]'),
('Follow-up Post Consulenza', 'whatsapp', 'utility',
 'Ciao {{nome}}! Come stai? Volevo sapere se hai avuto modo di riflettere sulla strategia che abbiamo discusso durante la diagnosi. Hai domande? Sono qui! 😊',
 '["nome"]'),
('Benvenuto Nuovo Lead', 'messenger', 'utility',
 'Ciao {{nome}}! Grazie per averci contattato su Messenger. Sono Digy, l''assistente digitale di DigIdentity Agency. Come posso aiutarti oggi?',
 '["nome"]')
ON CONFLICT DO NOTHING;
