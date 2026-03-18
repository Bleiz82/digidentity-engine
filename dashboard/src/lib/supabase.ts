import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseKey)

// Tipi database
export interface Lead {
    id: string
    nome_contatto: string
    email: string
    telefono: string | null
    nome_azienda: string
    settore_attivita: string
    sito_web: string | null
    ha_sito_web: boolean
    citta: string | null
    provincia: string | null
    urgenza: number
    status: string
    error_message: string | null
    score_sito_web: number
    score_seo: number
    score_gmb: number
    score_social: number
    score_competitivo: number
    score_totale: number
    email_free_sent: boolean
    email_premium_sent: boolean
    whatsapp_free_sent: boolean
    whatsapp_premium_sent: boolean
    pdf_free_path: string | null
    pdf_free_filename: string | null
    pdf_premium_path: string | null
    pdf_premium_filename: string | null
    created_at: string
    updated_at: string
    completed_at: string | null
}

export interface Payment {
    id: string
    lead_id: string
    stripe_session_id: string | null
    stripe_payment_intent: string | null
    amount: number
    currency: string
    status: string
    product: string
    invoice_number: string | null
    invoice_sent: boolean
    invoice_sent_at: string | null
    completed_at: string | null
    created_at: string
}

export interface Report {
    id: string
    lead_id: string
    report_type: string
    ai_model: string | null
    ai_tokens_input: number | null
    ai_tokens_output: number | null
    ai_total_tokens: number | null
    ai_cost_usd: number | null
    pdf_path: string | null
    pdf_filename: string | null
    pdf_size_bytes: number | null
    generation_time_seconds: number | null
    status: string
    created_at: string
}

export interface DashboardKPI {
    lead_totali: number
    lead_oggi: number
    lead_settimana: number
    lead_mese: number
    diagnosi_free_inviate: number
    diagnosi_premium_completate: number
    lead_in_errore: number
    lead_in_elaborazione: number
    tasso_conversione_percent: number | null
    score_medio: number | null
    revenue_totale_eur: number
}

export interface RevenueMensile {
    mese: string
    transazioni: number
    revenue_eur: number
    ticket_medio: number
}

export interface LeadPerProvincia {
    provincia: string
    totale_lead: number
    conversioni: number
    score_medio: number | null
    tasso_conversione_percent: number | null
}

export interface CostiAI {
    mese: string
    tipo_report: string
    report_generati: number
    tokens_totali: number
    costo_totale_usd: number
    costo_medio_per_report: number
    tempo_medio_generazione_sec: number
}

// ============================================
// AGENT TYPES — Digy Agent tables
// ============================================

export interface AgentContact {
    id: string
    engine_lead_id: string | null
    nome: string | null
    email: string | null
    telefono: string | null
    tipo_attivita: string | null
    nome_attivita: string | null
    indirizzo: string | null
    note: string | null
    whatsapp_id: string | null
    telegram_id: string | null
    messenger_id: string | null
    instagram_id: string | null
    chatbot_session: string | null
    vapi_call_id: string | null
    email_channel_id: string | null
    sms_phone: string | null
    canale_primo_contatto: string
    ultimo_canale: string
    lead_score: number
    lead_status: string
    source: string
    has_diagnosi: boolean
    has_geo_audit: boolean
    diagnosi_score: number | null
    geo_score: number | null
    tags: string[]
    metadata: Record<string, any>
    created_at: string
    updated_at: string
}

export interface Conversation {
    id: string
    contact_id: string
    channel_type: string
    status: string
    assigned_to: string | null
    ai_enabled: boolean
    last_message_at: string
    last_message_preview: string | null
    unread_count: number
    total_messages: number
    metadata: Record<string, any>
    created_at: string
    updated_at: string
    closed_at: string | null
    // joined
    contact?: AgentContact
}

export interface Message {
    id: string
    conversation_id: string
    contact_id: string
    direction: 'inbound' | 'outbound'
    sender_type: 'contact' | 'ai' | 'agent'
    sender_name: string | null
    content: string
    content_type: string
    media_url: string | null
    media_mime_type: string | null
    media_transcription: string | null
    channel_type: string
    channel_message_id: string | null
    ai_model: string | null
    ai_tokens_used: number | null
    ai_tools_called: string | null
    ai_confidence: number | null
    delivered: boolean
    read: boolean
    error: string | null
    metadata: Record<string, any>
    created_at: string
}

export interface Appointment {
    id: string
    contact_id: string
    google_event_id: string | null
    hangout_link: string | null
    cliente_telefono: string | null
    titolo: string
    data_ora: string
    durata_minuti: number
    modalita: string
    location: string | null
    stato: string
    note: string | null
    esito: string | null
    creato_da: string
    modified_by: string | null
    modification_reason: string | null
    reminder_24h_sent: boolean
    reminder_1h_sent: boolean
    created_at: string
    updated_at: string
    deleted_at: string | null
    meet_link: string | null
    // joined
    contact?: AgentContact
}
