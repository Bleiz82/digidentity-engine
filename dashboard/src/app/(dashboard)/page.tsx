'use client'

import { useEffect, useState } from 'react'
import { supabase, DashboardKPI } from '@/lib/supabase'
import KPICard from '@/components/KPICard'
import {
    Users,
    UserPlus,
    FileCheck,
    Crown,
    AlertTriangle,
    Loader,
    TrendingUp,
    Target,
    DollarSign,
    Cpu
} from 'lucide-react'

export default function DashboardPage() {
    const [kpi, setKpi] = useState<DashboardKPI | null>(null)
    const [recentLeads, setRecentLeads] = useState<any[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchData()
        const interval = setInterval(fetchData, 30000) // refresh ogni 30 secondi
        return () => clearInterval(interval)
    }, [])

    const fetchData = async () => {
        try {
            // KPI
            const { data: kpiData } = await supabase
                .from('dashboard_kpi')
                .select('*')
                .single()

            if (kpiData) setKpi(kpiData)

            // Ultimi 10 lead
            const { data: leads } = await supabase
                .from('leads')
                .select('id, nome_azienda, nome_contatto, email, citta, provincia, status, score_totale, created_at')
                .order('created_at', { ascending: false })
                .limit(10)

            if (leads) setRecentLeads(leads)
        } catch (error) {
            console.error('Errore fetch dashboard:', error)
        } finally {
            setLoading(false)
        }
    }

    const getStatusColor = (status: string) => {
        const colors: Record<string, string> = {
            'new': 'bg-blue-500/10 text-blue-400 border-blue-500/20',
            'processing': 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
            'free_report_sent': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
            'payment_pending': 'bg-orange-500/10 text-orange-400 border-orange-500/20',
            'payment_confirmed': 'bg-purple-500/10 text-purple-400 border-purple-500/20',
            'converted': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
            'error': 'bg-red-500/10 text-red-400 border-red-500/20',
        }
        return colors[status] || 'bg-slate-500/10 text-slate-400 border-slate-500/20'
    }

    const getStatusLabel = (status: string) => {
        const labels: Record<string, string> = {
            'new': 'Nuovo',
            'processing': 'In elaborazione',
            'scraping': 'Scraping',
            'analyzing': 'Analisi',
            'generating': 'Generazione',
            'analysis_complete': 'Analisi completata',
            'free_report_generated': 'Report generato',
            'free_report_sent': 'Report inviato',
            'payment_pending': 'Pagamento in attesa',
            'payment_confirmed': 'Pagamento confermato',
            'premium_processing': 'Premium in corso',
            'converted': 'Convertito',
            'error': 'Errore',
        }
        return labels[status] || status
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <Loader className="w-8 h-8 text-orange-500 animate-spin" />
            </div>
        )
    }

    return (
        <div className="space-y-8">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-white">Dashboard</h1>
                <p className="text-slate-400 mt-1">Panoramica DigIdentity Engine — aggiornamento ogni 30 secondi</p>
            </div>

            {/* KPI Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
                <KPICard
                    title="Lead Totali"
                    value={kpi?.lead_totali || 0}
                    subtitle={`${kpi?.lead_oggi || 0} oggi`}
                    icon={Users}
                    color="blue"
                />
                <KPICard
                    title="Questa Settimana"
                    value={kpi?.lead_settimana || 0}
                    subtitle={`${kpi?.lead_mese || 0} questo mese`}
                    icon={UserPlus}
                    color="green"
                />
                <KPICard
                    title="Diagnosi Free Inviate"
                    value={kpi?.diagnosi_free_inviate || 0}
                    icon={FileCheck}
                    color="orange"
                />
                <KPICard
                    title="Premium Completate"
                    value={kpi?.diagnosi_premium_completate || 0}
                    icon={Crown}
                    color="purple"
                />
                <KPICard
                    title="Revenue Totale"
                    value={`€${kpi?.revenue_totale_eur?.toLocaleString('it-IT') || '0'}`}
                    icon={DollarSign}
                    color="green"
                />
            </div>

            {/* Seconda riga KPI */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <KPICard
                    title="Tasso Conversione"
                    value={`${kpi?.tasso_conversione_percent || 0}%`}
                    subtitle="Free → Premium"
                    icon={TrendingUp}
                    color="orange"
                />
                <KPICard
                    title="Score Medio"
                    value={`${Math.round(kpi?.score_medio || 0)}/100`}
                    icon={Target}
                    color="blue"
                />
                <KPICard
                    title="In Elaborazione"
                    value={kpi?.lead_in_elaborazione || 0}
                    icon={Loader}
                    color="yellow"
                />
                <KPICard
                    title="Errori"
                    value={kpi?.lead_in_errore || 0}
                    icon={AlertTriangle}
                    color="red"
                />
            </div>

            {/* Ultimi Lead */}
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl overflow-hidden">
                <div className="p-6 border-b border-slate-700/50">
                    <h2 className="text-xl font-semibold text-white">Ultimi Lead</h2>
                    <p className="text-sm text-slate-400 mt-1">Gli ultimi 10 lead ricevuti</p>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-slate-700/50">
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Azienda</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Contatto</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Città</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Score</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Stato</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Data</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700/30">
                            {recentLeads.map((lead) => (
                                <tr key={lead.id} className="hover:bg-slate-700/20 transition-colors">
                                    <td className="px-6 py-4">
                                        <p className="text-sm font-medium text-white">{lead.nome_azienda}</p>
                                        <p className="text-xs text-slate-500">{lead.email}</p>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-slate-300">{lead.nome_contatto}</td>
                                    <td className="px-6 py-4 text-sm text-slate-300">{lead.citta} ({lead.provincia})</td>
                                    <td className="px-6 py-4">
                                        <span className={`text-sm font-bold ${lead.score_totale >= 70 ? 'text-emerald-400' :
                                                lead.score_totale >= 40 ? 'text-yellow-400' :
                                                    lead.score_totale > 0 ? 'text-red-400' :
                                                        'text-slate-500'
                                            }`}>
                                            {lead.score_totale > 0 ? `${lead.score_totale}/100` : '—'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium border ${getStatusColor(lead.status)}`}>
                                            {getStatusLabel(lead.status)}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-slate-400">
                                        {new Date(lead.created_at).toLocaleDateString('it-IT', {
                                            day: '2-digit',
                                            month: '2-digit',
                                            year: 'numeric',
                                            hour: '2-digit',
                                            minute: '2-digit'
                                        })}
                                    </td>
                                </tr>
                            ))}
                            {recentLeads.length === 0 && (
                                <tr>
                                    <td colSpan={6} className="px-6 py-12 text-center text-slate-500">
                                        Nessun lead ancora. La prima diagnosi è in arrivo!
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}
