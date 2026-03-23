'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import { Users, Search, Filter, ChevronDown, ChevronUp, ExternalLink, RefreshCw } from 'lucide-react'

export default function LeadsPage() {
    const [leads, setLeads] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [searchTerm, setSearchTerm] = useState('')
    const [statusFilter, setStatusFilter] = useState('all')
    const [provinciaFilter, setProvinciaFilter] = useState('all')
    const [sortField, setSortField] = useState<string>('created_at')
    const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc')
    const [expandedLead, setExpandedLead] = useState<string | null>(null)
    const [provincie, setProvincie] = useState<string[]>([])
    const [adminLoading, setAdminLoading] = useState<string | null>(null)
    const [adminMsg, setAdminMsg] = useState<string | null>(null)

    const triggerPremium = async (leadId: string) => {
        setAdminLoading(leadId); setAdminMsg(null)
        try {
            const res = await fetch('https://api.digidentityagency.it/api/payment/internal/genera-premium', {
                method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Internal-Key': process.env.NEXT_PUBLIC_INTERNAL_API_KEY || '' },
                body: JSON.stringify({ lead_id: leadId })
            })
            const data = await res.json()
            if (res.ok) { setAdminMsg('Report Premium avviato!'); fetchLeads() } else { setAdminMsg(data.detail || data.error || 'Errore') }
        } catch { setAdminMsg('Errore di connessione') } finally { setAdminLoading(null) }
    }

    const triggerFreeReport = async (leadId: string) => {
        setAdminLoading(leadId + '_free'); setAdminMsg(null)
        try {
            const res = await fetch('https://api.digidentityagency.it/api/payment/internal/genera-free', {
                method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Internal-Key': process.env.NEXT_PUBLIC_INTERNAL_API_KEY || '' },
                body: JSON.stringify({ lead_id: leadId })
            })
            const data = await res.json()
            if (res.ok) { setAdminMsg('Report Free ri-avviato!'); fetchLeads() } else { setAdminMsg(data.detail || data.error || 'Errore') }
        } catch { setAdminMsg('Errore di connessione') } finally { setAdminLoading(null) }
    }

    useEffect(() => { fetchLeads() }, [])

    const fetchLeads = async () => {
        setLoading(true)
        try {
            const { data, error } = await supabase.from('leads')
                .select('id, nome_azienda, nome_contatto, email, telefono, citta, provincia, settore_attivita, sito_web, ha_sito_web, status, score_sito_web, score_seo, score_gmb, score_social, score_competitivo, score_totale, report_sent_at, premium_sent_at, created_at, updated_at')
                .order('created_at', { ascending: false })
            if (data) {
                setLeads(data)
                const uniqueProvincie = [...new Set(data.map((l: any) => l.provincia).filter(Boolean))] as string[]
                setProvincie(uniqueProvincie.sort())
            }
        } catch (error) { console.error('Errore:', error) } finally { setLoading(false) }
    }

    const filteredLeads = leads.filter(lead => {
        const matchesSearch = searchTerm === '' || lead.nome_azienda.toLowerCase().includes(searchTerm.toLowerCase()) || lead.nome_contatto.toLowerCase().includes(searchTerm.toLowerCase()) || lead.email.toLowerCase().includes(searchTerm.toLowerCase()) || (lead.citta && lead.citta.toLowerCase().includes(searchTerm.toLowerCase()))
        return matchesSearch && (statusFilter === 'all' || lead.status === statusFilter) && (provinciaFilter === 'all' || lead.provincia === provinciaFilter)
    }).sort((a, b) => {
        const aVal = a[sortField]; const bVal = b[sortField]
        if (aVal == null) return 1; if (bVal == null) return -1
        return sortDirection === 'asc' ? (aVal > bVal ? 1 : -1) : (aVal < bVal ? 1 : -1)
    })

    const handleSort = (field: string) => {
        if (sortField === field) setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
        else { setSortField(field); setSortDirection('desc') }
    }

    const SortIcon = ({ field }: { field: string }) => {
        if (sortField !== field) return null
        return sortDirection === 'asc' ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />
    }

    const getStatusColor = (status: string) => {
        const colors: Record<string, string> = { 'new': 'bg-blue-500/10 text-blue-400 border-blue-500/20', 'processing': 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20', 'free_report_sent': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20', 'payment_pending': 'bg-orange-500/10 text-orange-400 border-orange-500/20', 'payment_confirmed': 'bg-purple-500/10 text-purple-400 border-purple-500/20', 'converted': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20', 'error': 'bg-red-500/10 text-red-400 border-red-500/20' }
        return colors[status] || 'bg-slate-500/10 text-slate-400 border-slate-500/20'
    }

    const getStatusLabel = (status: string) => {
        const labels: Record<string, string> = { 'new': 'Nuovo', 'processing': 'In elaborazione', 'scraping': 'Scraping', 'analyzing': 'Analisi', 'generating': 'Generazione', 'analysis_complete': 'Analisi completata', 'free_report_generated': 'Report generato', 'free_report_sent': 'Report inviato', 'payment_pending': 'Pagamento attesa', 'payment_confirmed': 'Pagamento OK', 'premium_processing': 'Premium in corso', 'converted': 'Convertito Premium', 'error': 'Errore' }
        return labels[status] || status
    }

    const getScoreColor = (score: number) => score >= 70 ? 'text-emerald-400' : score >= 40 ? 'text-yellow-400' : score > 0 ? 'text-red-400' : 'text-slate-500'

    const statuses = ['new', 'processing', 'scraping', 'analyzing', 'generating', 'analysis_complete', 'free_report_generated', 'free_report_sent', 'payment_pending', 'payment_confirmed', 'premium_processing', 'converted', 'error']

    return (
        <div className="max-w-full overflow-x-hidden space-y-4 sm:space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                    <h1 className="text-xl sm:text-3xl font-bold text-white flex items-center gap-3">
                        <Users className="w-6 h-6 sm:w-8 sm:h-8 text-orange-500" />
                        Lead Pipeline
                    </h1>
                    <p className="text-xs sm:text-sm text-slate-400 mt-1">{filteredLeads.length} lead {statusFilter !== 'all' ? `(filtro: ${getStatusLabel(statusFilter)})` : 'totali'}</p>
                </div>
                <button onClick={fetchLeads} className="flex items-center gap-2 px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-xl text-slate-300 hover:text-white transition-all self-start sm:self-auto">
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Aggiorna
                </button>
            </div>

            {/* Filtri responsive */}
            <div className="flex flex-col sm:flex-row gap-3">
                <div className="flex-1 min-w-0 relative">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                    <input type="text" placeholder="Cerca azienda, contatto, email..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-11 pr-4 py-3 bg-slate-800/50 border border-slate-700/50 rounded-xl text-white text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-orange-500/50" />
                </div>
                <div className="flex gap-2">
                    <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}
                        className="flex-1 sm:flex-none px-3 py-3 bg-slate-800/50 border border-slate-700/50 rounded-xl text-white text-sm appearance-none focus:outline-none focus:ring-2 focus:ring-orange-500/50">
                        <option value="all">Tutti gli stati</option>
                        {statuses.map(s => (<option key={s} value={s}>{getStatusLabel(s)}</option>))}
                    </select>
                    <select value={provinciaFilter} onChange={(e) => setProvinciaFilter(e.target.value)}
                        className="flex-1 sm:flex-none px-3 py-3 bg-slate-800/50 border border-slate-700/50 rounded-xl text-white text-sm appearance-none focus:outline-none focus:ring-2 focus:ring-orange-500/50">
                        <option value="all">Tutte le prov.</option>
                        {provincie.map(p => (<option key={p} value={p}>{p}</option>))}
                    </select>
                </div>
            </div>

            {/* Mobile cards */}
            <div className="sm:hidden space-y-3">
                {filteredLeads.map((lead) => (
                    <div key={lead.id} className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4 space-y-3" onClick={() => setExpandedLead(expandedLead === lead.id ? null : lead.id)}>
                        <div className="flex items-start justify-between">
                            <div className="min-w-0 flex-1">
                                <p className="text-sm font-medium text-white truncate">{lead.nome_azienda}</p>
                                <p className="text-xs text-slate-500">{lead.nome_contatto} · {lead.email}</p>
                            </div>
                            <span className={`ml-2 flex-shrink-0 inline-flex items-center px-2 py-0.5 rounded-lg text-[10px] font-medium border ${getStatusColor(lead.status)}`}>
                                {getStatusLabel(lead.status)}
                            </span>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                            <span className="text-slate-400">{lead.citta}{lead.provincia ? ` (${lead.provincia})` : ''}</span>
                            <div className="flex items-center gap-3">
                                <span className={`font-bold ${getScoreColor(lead.score_totale || 0)}`}>{lead.score_totale > 0 ? lead.score_totale : '—'}</span>
                                <div className="flex items-center gap-1">
                                    <span className={`w-2 h-2 rounded-full ${lead.report_sent_at ? 'bg-emerald-400' : 'bg-slate-600'}`} />
                                    <span className={`w-2 h-2 rounded-full ${lead.premium_sent_at ? 'bg-purple-400' : 'bg-slate-600'}`} />
                                </div>
                            </div>
                        </div>
                        {expandedLead === lead.id && (
                            <div className="pt-3 border-t border-slate-700/50 space-y-3">
                                <div className="grid grid-cols-2 gap-2 text-xs">
                                    <div><span className="text-slate-500">Sito Web</span><span className={` ml-1 font-bold ${getScoreColor(lead.score_sito_web || 0)}`}>{lead.score_sito_web || 0}</span></div>
                                    <div><span className="text-slate-500">SEO</span><span className={` ml-1 font-bold ${getScoreColor(lead.score_seo || 0)}`}>{lead.score_seo || 0}</span></div>
                                    <div><span className="text-slate-500">GMB</span><span className={` ml-1 font-bold ${getScoreColor(lead.score_gmb || 0)}`}>{lead.score_gmb || 0}</span></div>
                                    <div><span className="text-slate-500">Social</span><span className={` ml-1 font-bold ${getScoreColor(lead.score_social || 0)}`}>{lead.score_social || 0}</span></div>
                                </div>
                                {lead.sito_web && <a href={lead.sito_web} target="_blank" rel="noopener noreferrer" className="text-xs text-orange-400 flex items-center gap-1"><ExternalLink className="w-3 h-3" />{lead.sito_web}</a>}
                                {adminMsg && <p className="text-xs text-emerald-400">{adminMsg}</p>}
                                <div className="flex gap-2">
                                    <button onClick={(e) => { e.stopPropagation(); triggerFreeReport(lead.id) }} disabled={adminLoading === lead.id + '_free'}
                                        className="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded-xl disabled:opacity-50 flex items-center justify-center gap-1">
                                        {adminLoading === lead.id + '_free' && <RefreshCw className="w-3 h-3 animate-spin" />} Free
                                    </button>
                                    <button onClick={(e) => { e.stopPropagation(); triggerPremium(lead.id) }} disabled={adminLoading === lead.id}
                                        className="flex-1 px-3 py-2 bg-purple-600 hover:bg-purple-700 text-white text-xs font-medium rounded-xl disabled:opacity-50 flex items-center justify-center gap-1">
                                        {adminLoading === lead.id && <RefreshCw className="w-3 h-3 animate-spin" />} Premium
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                ))}
                {filteredLeads.length === 0 && !loading && <div className="text-center text-slate-500 py-8 text-sm">Nessun lead trovato</div>}
            </div>

            {/* Desktop table */}
            <div className="hidden sm:block bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-slate-700/50">
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4 cursor-pointer hover:text-white" onClick={() => handleSort('nome_azienda')}><span className="flex items-center gap-1">Azienda <SortIcon field="nome_azienda" /></span></th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Contatto</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4 cursor-pointer hover:text-white" onClick={() => handleSort('citta')}><span className="flex items-center gap-1">Località <SortIcon field="citta" /></span></th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4 cursor-pointer hover:text-white" onClick={() => handleSort('score_totale')}><span className="flex items-center gap-1">Score <SortIcon field="score_totale" /></span></th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4 cursor-pointer hover:text-white" onClick={() => handleSort('status')}><span className="flex items-center gap-1">Stato <SortIcon field="status" /></span></th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Delivery</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4 cursor-pointer hover:text-white" onClick={() => handleSort('created_at')}><span className="flex items-center gap-1">Data <SortIcon field="created_at" /></span></th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700/30">
                            {filteredLeads.map((lead) => (
                                <tr key={lead.id} className="hover:bg-slate-700/20 transition-colors cursor-pointer" onClick={() => setExpandedLead(expandedLead === lead.id ? null : lead.id)}>
                                    <td className="px-6 py-4"><p className="text-sm font-medium text-white">{lead.nome_azienda}</p><p className="text-xs text-slate-500">{lead.settore_attivita}</p></td>
                                    <td className="px-6 py-4"><p className="text-sm text-slate-300">{lead.nome_contatto}</p><p className="text-xs text-slate-500">{lead.email}</p></td>
                                    <td className="px-6 py-4 text-sm text-slate-300">{lead.citta}{lead.provincia ? ` (${lead.provincia})` : ''}</td>
                                    <td className="px-6 py-4"><span className={`text-lg font-bold ${getScoreColor(lead.score_totale || 0)}`}>{lead.score_totale > 0 ? lead.score_totale : '—'}</span></td>
                                    <td className="px-6 py-4"><span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium border ${getStatusColor(lead.status)}`}>{getStatusLabel(lead.status)}</span></td>
                                    <td className="px-6 py-4"><div className="flex items-center gap-2"><span className={`w-2 h-2 rounded-full ${lead.report_sent_at ? 'bg-emerald-400' : 'bg-slate-600'}`} /><span className={`w-2 h-2 rounded-full ${lead.premium_sent_at ? 'bg-purple-400' : 'bg-slate-600'}`} /></div></td>
                                    <td className="px-6 py-4 text-sm text-slate-400">{new Date(lead.created_at).toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })}</td>
                                </tr>
                            ))}
                            {filteredLeads.length === 0 && !loading && <tr><td colSpan={7} className="px-6 py-12 text-center text-slate-500">Nessun lead trovato</td></tr>}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Dettaglio espanso desktop */}
            {expandedLead && (() => {
                const lead = leads.find(l => l.id === expandedLead)
                if (!lead) return null
                return (
                    <div className="hidden sm:block bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6">
                        <h3 className="text-lg font-semibold text-white mb-4">{lead.nome_azienda} — Dettaglio</h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                            <div>
                                <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Contatto</p>
                                <p className="text-sm text-white">{lead.telefono || 'N/A'}</p>
                                <p className="text-sm text-slate-400">{lead.email}</p>
                                {lead.sito_web && <a href={lead.sito_web} target="_blank" rel="noopener noreferrer" className="text-sm text-orange-400 hover:underline flex items-center gap-1 mt-1">{lead.sito_web} <ExternalLink className="w-3 h-3" /></a>}
                            </div>
                            <div>
                                <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Score Dettaglio</p>
                                <div className="space-y-1">
                                    {['sito_web', 'seo', 'gmb', 'social', 'competitivo'].map(k => (
                                        <div key={k} className="flex justify-between text-sm"><span className="text-slate-400 capitalize">{k.replace('_', ' ')}</span><span className={getScoreColor(lead[`score_${k}`] || 0)}>{lead[`score_${k}`] || 0}/100</span></div>
                                    ))}
                                </div>
                            </div>
                            <div>
                                <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Delivery</p>
                                <p className="text-sm">{lead.report_sent_at ? <span className="text-emerald-400">Free: {new Date(lead.report_sent_at).toLocaleDateString('it-IT')}</span> : <span className="text-slate-500">Free non inviato</span>}</p>
                                <p className="text-sm mt-1">{lead.premium_sent_at ? <span className="text-purple-400">Premium: {new Date(lead.premium_sent_at).toLocaleDateString('it-IT')}</span> : <span className="text-slate-500">Premium non inviato</span>}</p>
                            </div>
                            <div>
                                <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Info</p>
                                <p className="text-sm text-slate-400">Sito: {lead.ha_sito_web ? 'Sì' : 'No'}</p>
                                <p className="text-sm text-slate-400">Settore: {lead.settore_attivita}</p>
                            </div>
                        </div>
                        <div className="mt-6 pt-4 border-t border-slate-700/50 flex flex-wrap gap-3">
                            {adminMsg && <p className="w-full text-sm text-emerald-400 mb-2">{adminMsg}</p>}
                            <button onClick={(e) => { e.stopPropagation(); triggerFreeReport(lead.id) }} disabled={adminLoading === lead.id + '_free'} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-xl disabled:opacity-50 flex items-center gap-2">
                                {adminLoading === lead.id + '_free' && <RefreshCw className="w-4 h-4 animate-spin" />} Ri-genera Free Report
                            </button>
                            <button onClick={(e) => { e.stopPropagation(); triggerPremium(lead.id) }} disabled={adminLoading === lead.id} className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium rounded-xl disabled:opacity-50 flex items-center gap-2">
                                {adminLoading === lead.id && <RefreshCw className="w-4 h-4 animate-spin" />} Genera Premium
                            </button>
                        </div>
                    </div>
                )
            })()}
        </div>
    )
}
