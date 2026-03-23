'use client'

import { useEffect, useState } from 'react'
import { supabase, DashboardKPI } from '@/lib/supabase'
import {
    Users, UserPlus, FileCheck, Crown, AlertTriangle, Loader,
    TrendingUp, Target, DollarSign, RefreshCw
} from 'lucide-react'

export default function DashboardPage() {
    const [kpi, setKpi] = useState<DashboardKPI | null>(null)
    const [recentLeads, setRecentLeads] = useState<any[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => { fetchData() }, [])

    const fetchData = async () => {
        setLoading(true)
        try {
            const { data: kpiData } = await supabase.from('dashboard_kpi').select('*').single()
            if (kpiData) setKpi(kpiData)
            const { data: leads } = await supabase
                .from('leads')
                .select('id, nome_azienda, nome_contatto, email, citta, provincia, status, score_totale, created_at')
                .order('created_at', { ascending: false })
                .limit(10)
            if (leads) setRecentLeads(leads)
        } catch (error) { console.error('Errore:', error) }
        finally { setLoading(false) }
    }

    const statusColor = (s: string) => {
        const m: Record<string, string> = {
            new: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
            processing: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
            free_report_sent: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
            payment_pending: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
            payment_confirmed: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
            converted: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
            error: 'bg-red-500/10 text-red-400 border-red-500/20',
        }
        return m[s] || 'bg-slate-500/10 text-slate-400 border-slate-500/20'
    }

    const statusLabel = (s: string) => {
        const m: Record<string, string> = {
            new: 'Nuovo', processing: 'Elaborazione', free_report_sent: 'Report inviato',
            payment_pending: 'Attesa pag.', payment_confirmed: 'Pag. confermato',
            converted: 'Convertito', error: 'Errore',
        }
        return m[s] || s
    }

    if (loading) return <div className="flex items-center justify-center h-96"><Loader className="w-8 h-8 text-[#F90100] animate-spin" /></div>

    const cards1 = [
        { t: 'Lead Totali', v: kpi?.lead_totali || 0, s: `${kpi?.lead_oggi || 0} oggi`, Icon: Users, c: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20' },
        { t: 'Settimana', v: kpi?.lead_settimana || 0, s: `${kpi?.lead_mese || 0} mese`, Icon: UserPlus, c: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
        { t: 'Free', v: kpi?.diagnosi_free_inviate || 0, s: 'Inviate', Icon: FileCheck, c: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/20' },
        { t: 'Premium', v: kpi?.diagnosi_premium_completate || 0, s: 'Completate', Icon: Crown, c: 'text-purple-400', bg: 'bg-purple-500/10 border-purple-500/20' },
        { t: 'Revenue', v: `€${kpi?.revenue_totale_eur?.toLocaleString('it-IT') || '0'}`, s: 'Totale', Icon: DollarSign, c: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
    ]

    const cards2 = [
        { t: 'Conversione', v: `${kpi?.tasso_conversione_percent || 0}%`, s: 'Free→Premium', Icon: TrendingUp, c: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/20' },
        { t: 'Score Medio', v: `${Math.round(kpi?.score_medio || 0)}/100`, s: 'Media', Icon: Target, c: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20' },
        { t: 'Elaborazione', v: kpi?.lead_in_elaborazione || 0, s: 'In corso', Icon: Loader, c: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/20' },
        { t: 'Errori', v: kpi?.lead_in_errore || 0, s: 'Da verificare', Icon: AlertTriangle, c: 'text-red-400', bg: 'bg-red-500/10 border-red-500/20' },
    ]

    const renderCard = (card: typeof cards1[0], i: number) => (
        <div key={i} className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4">
            <div className="flex items-center gap-2 mb-1">
                <card.Icon className={`w-4 h-4 ${card.c}`} />
                <span className="text-xs text-slate-400">{card.t}</span>
            </div>
            <p className="text-xl sm:text-2xl font-bold text-white">{card.v}</p>
            <p className="text-[10px] text-slate-500">{card.s}</p>
        </div>
    )

    return (
        <div className="max-w-full overflow-x-hidden space-y-4 sm:space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                    <h1 className="text-xl sm:text-3xl font-bold text-white flex items-center gap-3">
                        <TrendingUp className="w-6 h-6 sm:w-8 sm:h-8 text-[#F90100]" /> Dashboard
                    </h1>
                    <p className="text-xs sm:text-sm text-slate-400 mt-1">Panoramica DigIdentity Engine</p>
                </div>
                <button onClick={fetchData} className="flex items-center gap-2 px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-xl text-slate-300 hover:text-white transition-all self-start sm:self-auto">
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Aggiorna
                </button>
            </div>

            <div style={{display:"grid",gridTemplateColumns:"repeat(2,1fr)",gap:"0.75rem"}} className="sm:grid-cols-3 lg:grid-cols-5">
                {cards1.map((c, i) => renderCard(c, i))}
            </div>

            <div style={{display:"grid",gridTemplateColumns:"repeat(2,1fr)",gap:"0.75rem"}} className="sm:grid-cols-4">
                {cards2.map((c, i) => renderCard(c, i))}
            </div>

            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl overflow-hidden">
                <div className="p-4 sm:p-6 border-b border-slate-700/50">
                    <h2 className="text-lg sm:text-xl font-semibold text-white">Ultimi Lead</h2>
                    <p className="text-xs sm:text-sm text-slate-400 mt-1">Ultimi 10 ricevuti</p>
                </div>

                <div className="sm:hidden divide-y divide-slate-700/30">
                    {recentLeads.map((lead) => (
                        <div key={lead.id} className="p-4 space-y-2">
                            <div className="flex items-start justify-between gap-2">
                                <div className="min-w-0 flex-1">
                                    <p className="text-sm font-medium text-white truncate">{lead.nome_azienda}</p>
                                    <p className="text-xs text-slate-500 truncate">{lead.nome_contatto}</p>
                                </div>
                                <span className={`flex-shrink-0 px-2 py-0.5 rounded-lg text-[10px] font-medium border ${statusColor(lead.status)}`}>{statusLabel(lead.status)}</span>
                            </div>
                            <div className="flex items-center justify-between text-xs text-slate-400">
                                <span className="truncate">{lead.citta}{lead.provincia ? ` (${lead.provincia})` : ''}</span>
                                <span className={`font-bold ml-2 ${lead.score_totale >= 70 ? 'text-emerald-400' : lead.score_totale >= 40 ? 'text-yellow-400' : lead.score_totale > 0 ? 'text-red-400' : 'text-slate-500'}`}>{lead.score_totale > 0 ? lead.score_totale : '—'}</span>
                            </div>
                        </div>
                    ))}
                    {recentLeads.length === 0 && <div className="p-8 text-center text-slate-500 text-sm">Nessun lead</div>}
                </div>

                <div className="hidden sm:block overflow-x-auto">
                    <table className="w-full">
                        <thead><tr className="border-b border-slate-700/50">
                            <th className="text-left text-xs font-medium text-slate-400 uppercase px-6 py-4">Azienda</th>
                            <th className="text-left text-xs font-medium text-slate-400 uppercase px-6 py-4">Contatto</th>
                            <th className="text-left text-xs font-medium text-slate-400 uppercase px-6 py-4">Città</th>
                            <th className="text-left text-xs font-medium text-slate-400 uppercase px-6 py-4">Score</th>
                            <th className="text-left text-xs font-medium text-slate-400 uppercase px-6 py-4">Stato</th>
                            <th className="text-left text-xs font-medium text-slate-400 uppercase px-6 py-4">Data</th>
                        </tr></thead>
                        <tbody className="divide-y divide-slate-700/30">
                            {recentLeads.map((lead) => (
                                <tr key={lead.id} className="hover:bg-slate-700/20 transition-colors">
                                    <td className="px-6 py-4"><p className="text-sm font-medium text-white">{lead.nome_azienda}</p><p className="text-xs text-slate-500">{lead.email}</p></td>
                                    <td className="px-6 py-4 text-sm text-slate-300">{lead.nome_contatto}</td>
                                    <td className="px-6 py-4 text-sm text-slate-300">{lead.citta} ({lead.provincia})</td>
                                    <td className="px-6 py-4"><span className={`text-sm font-bold ${lead.score_totale >= 70 ? 'text-emerald-400' : lead.score_totale >= 40 ? 'text-yellow-400' : lead.score_totale > 0 ? 'text-red-400' : 'text-slate-500'}`}>{lead.score_totale > 0 ? `${lead.score_totale}/100` : '—'}</span></td>
                                    <td className="px-6 py-4"><span className={`px-2.5 py-1 rounded-lg text-xs font-medium border ${statusColor(lead.status)}`}>{statusLabel(lead.status)}</span></td>
                                    <td className="px-6 py-4 text-sm text-slate-400">{new Date(lead.created_at).toLocaleDateString('it-IT')}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}
