'use client'

import { Settings, Globe, Database, CreditCard, Mail, MessageSquare, Brain, Shield, CheckCircle, XCircle, Server, Workflow } from 'lucide-react'

interface ConfigItem {
    label: string
    value: string
    status: 'ok' | 'missing' | 'info'
}

interface ConfigSection {
    title: string
    icon: any
    items: ConfigItem[]
}

export default function ImpostazioniPage() {
    const sections: ConfigSection[] = [
        {
            title: 'Applicazione',
            icon: Globe,
            items: [
                { label: 'Base URL', value: 'https://digidentityagency.it', status: 'ok' },
                { label: 'Ambiente', value: 'DEBUG', status: 'info' },
                { label: 'Versione', value: 'v1.0.0', status: 'ok' },
                { label: 'Framework', value: 'FastAPI + Next.js', status: 'ok' },
            ]
        },
        {
            title: 'Database',
            icon: Database,
            items: [
                { label: 'Provider', value: 'Supabase (PostgreSQL)', status: 'ok' },
                { label: 'Tabelle', value: 'leads, payments, reports', status: 'ok' },
                { label: 'Viste Dashboard', value: '7 viste attive', status: 'ok' },
                { label: 'RLS', value: 'Attivo', status: 'ok' },
            ]
        },
        {
            title: 'AI Engine',
            icon: Brain,
            items: [
                { label: 'Modello Primario', value: 'Claude Sonnet 4 (Anthropic)', status: 'ok' },
                { label: 'Max Tokens', value: '4000 (free) / 8000 (premium)', status: 'ok' },
                { label: 'Prompt Free', value: 'free-report-prompt.md', status: 'ok' },
                { label: 'Prompt Premium', value: 'premium-report-prompt.md', status: 'ok' },
            ]
        },
        {
            title: 'Pagamenti',
            icon: CreditCard,
            items: [
                { label: 'Provider', value: 'Stripe', status: 'ok' },
                { label: 'Prodotto', value: 'Diagnosi Premium — €99', status: 'ok' },
                { label: 'Webhook', value: '/api/payment/webhook', status: 'ok' },
                { label: 'Modalità', value: 'Checkout Session', status: 'ok' },
            ]
        },
        {
            title: 'Email',
            icon: Mail,
            items: [
                { label: 'Provider', value: 'Gmail SMTP', status: 'ok' },
                { label: 'Sender', value: 'DigIdentity Agency', status: 'ok' },
                { label: 'Template Free', value: 'HTML con CTA Premium', status: 'ok' },
                { label: 'Template Premium', value: 'HTML con roadmap', status: 'ok' },
            ]
        },
        {
            title: 'WhatsApp',
            icon: MessageSquare,
            items: [
                { label: 'Provider', value: 'Meta Business API', status: 'ok' },
                { label: 'Notifica Free', value: 'Attiva', status: 'ok' },
                { label: 'Notifica Premium', value: 'Attiva', status: 'ok' },
                { label: 'Webhook Verify Token', value: 'Non necessario (invio via email)', status: 'info' },
            ]
        },
        {
            title: 'Infrastruttura',
            icon: Server,
            items: [
                { label: 'Task Queue', value: 'Celery + Redis', status: 'ok' },
                { label: 'PDF Engine', value: 'WeasyPrint', status: 'ok' },
                { label: 'Scraping', value: 'PageSpeed + SerpAPI + GMB + Social', status: 'ok' },
                { label: 'Container', value: 'Docker + docker-compose', status: 'ok' },
            ]
        },
    ]

    const pipelineSteps = [
        { label: 'Landing Page', color: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
        { label: 'Lead Intake', color: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20' },
        { label: 'Supabase', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' },
        { label: 'Celery Task', color: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' },
        { label: 'Scraping', color: 'bg-[#F90100]/10 text-[#F90100] border-[#F90100]/20' },
        { label: 'Claude AI', color: 'bg-purple-500/10 text-purple-400 border-purple-500/20' },
        { label: 'PDF', color: 'bg-red-500/10 text-red-400 border-red-500/20' },
        { label: 'Email + WhatsApp', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' },
    ]

    const premiumSteps = [
        { label: 'Stripe Checkout', color: 'bg-purple-500/10 text-purple-400 border-purple-500/20' },
        { label: 'Webhook', color: 'bg-purple-500/10 text-purple-400 border-purple-500/20' },
        { label: 'Deep Analysis', color: 'bg-purple-500/10 text-purple-400 border-purple-500/20' },
        { label: 'Premium Report (40-50 pag)', color: 'bg-purple-500/10 text-purple-400 border-purple-500/20' },
    ]

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-white flex items-center gap-3 tracking-tight">
                    <Settings className="w-8 h-8 text-[#F90100]" />
                    Impostazioni
                </h1>
                <p className="text-[#9CA3AF] mt-1">Configurazione sistema DigIdentity Engine</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {sections.map((section, i) => {
                    const Icon = section.icon
                    return (
                        <div key={i} className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-2xl overflow-hidden hover:border-[#333333] transition-all duration-300">
                            <div className="p-5 border-b border-[#1F1F1F] flex items-center gap-3">
                                <div className="w-8 h-8 rounded-lg bg-[#F90100]/10 flex items-center justify-center">
                                    <Icon className="w-4 h-4 text-[#F90100]" />
                                </div>
                                <h2 className="text-lg font-semibold text-white">{section.title}</h2>
                            </div>
                            <div className="p-5 space-y-4">
                                {section.items.map((item, j) => (
                                    <div key={j} className="flex items-center justify-between">
                                        <span className="text-sm text-[#9CA3AF]">{item.label}</span>
                                        <div className="flex items-center gap-2">
                                            <span className={`text-sm font-medium ${item.status === 'ok' ? 'text-white' :
                                                    item.status === 'missing' ? 'text-[#F90100]' :
                                                        'text-[#9CA3AF]'
                                                }`}>
                                                {item.value}
                                            </span>
                                            {item.status === 'ok' && <CheckCircle className="w-4 h-4 text-emerald-400" />}
                                            {item.status === 'missing' && <XCircle className="w-4 h-4 text-[#F90100]" />}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )
                })}
            </div>

            <div className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-2xl p-6">
                <div className="flex items-center gap-3 mb-6">
                    <div className="w-8 h-8 rounded-lg bg-[#F90100]/10 flex items-center justify-center">
                        <Workflow className="w-4 h-4 text-[#F90100]" />
                    </div>
                    <h2 className="text-xl font-semibold text-white">Pipeline Flow</h2>
                </div>
                <div className="mb-4">
                    <p className="text-xs text-[#6B7280] uppercase tracking-wider mb-3">Diagnosi Gratuita</p>
                    <div className="flex flex-wrap items-center gap-2">
                        {pipelineSteps.map((step, i) => (
                            <div key={i} className="flex items-center gap-2">
                                <span className={`px-3 py-1.5 rounded-lg border text-xs font-medium ${step.color}`}>
                                    {step.label}
                                </span>
                                {i < pipelineSteps.length - 1 && <span className="text-[#333333]">→</span>}
                            </div>
                        ))}
                    </div>
                </div>
                <div>
                    <p className="text-xs text-[#6B7280] uppercase tracking-wider mb-3">Premium (€99)</p>
                    <div className="flex flex-wrap items-center gap-2">
                        {premiumSteps.map((step, i) => (
                            <div key={i} className="flex items-center gap-2">
                                <span className={`px-3 py-1.5 rounded-lg border text-xs font-medium ${step.color}`}>
                                    {step.label}
                                </span>
                                {i < premiumSteps.length - 1 && <span className="text-[#333333]">→</span>}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}
