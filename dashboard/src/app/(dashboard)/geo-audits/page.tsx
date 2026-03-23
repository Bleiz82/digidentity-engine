'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import { RefreshCw, Globe, Download, AlertCircle, CheckCircle2, Clock, Loader2, TrendingUp, Mail } from 'lucide-react'

interface GeoAudit {
    id: string; url_sito: string; email_cliente: string; status: 'pending' | 'in_progress' | 'completed' | 'error'
    geo_score: number | null; pdf_path: string | null; email_sent: boolean; error_message: string | null
    created_at: string; completed_at: string | null
}

export default function GeoAuditsPage() {
    const [audits, setAudits] = useState<GeoAudit[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [showForm, setShowForm] = useState(false)
    const [geoUrl, setGeoUrl] = useState('')
    const [geoEmail, setGeoEmail] = useState('digidentityagency@gmail.com')
    const [geoLoading, setGeoLoading] = useState(false)
    const [geoMsg, setGeoMsg] = useState<string | null>(null)

    const triggerGeoAudit = async () => {
        if (!geoUrl) return
        setGeoLoading(true); setGeoMsg(null)
        try {
            const res = await fetch('https://api.digidentityagency.it/api/payment/internal/genera-geo', {
                method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Internal-Key': 'dIgId_int3rn4L_X9kM2pV7nQ4wL6jR8' },
                body: JSON.stringify({ url_sito: geoUrl, email: geoEmail })
            })
            const data = await res.json()
            if (res.ok) { setGeoMsg('GEO Audit avviato!'); setGeoUrl(''); setShowForm(false); fetchAudits() }
            else { setGeoMsg(data.detail || data.error || 'Errore') }
        } catch { setGeoMsg('Errore di connessione') } finally { setGeoLoading(false) }
    }

    useEffect(() => { fetchAudits() }, [])

    const fetchAudits = async () => {
        setLoading(true); setError(null)
        try {
            const { data, error: sbError } = await supabase.from('geo_audits').select('*').order('created_at', { ascending: false })
            if (sbError) throw sbError
            if (data) setAudits(data)
        } catch (err: any) { setError(err.message || 'Errore') } finally { setLoading(false) }
    }

    const cleanDomain = (url: string) => { try { return url.replace(/^https?:\/\//, '').replace(/^www\./, '').replace(/\/$/, '') } catch { return url } }
    const formatDateTime = (dateStr: string | null) => {
        if (!dateStr) return '—'
        return new Date(dateStr).toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }).replace(',', ' alle')
    }

    const getScoreBadge = (score: number | null) => {
        if (score === null) return <span className="text-slate-600">—</span>
        if (score <= 39) return <span className="inline-flex items-center px-2 py-0.5 rounded-lg text-[10px] sm:text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20">Critico ({score})</span>
        if (score <= 69) return <span className="inline-flex items-center px-2 py-0.5 rounded-lg text-[10px] sm:text-xs font-medium bg-yellow-500/10 text-yellow-400 border border-yellow-500/20">Da migliorare ({score})</span>
        if (score <= 84) return <span className="inline-flex items-center px-2 py-0.5 rounded-lg text-[10px] sm:text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">Buono ({score})</span>
        return <span className="inline-flex items-center px-2 py-0.5 rounded-lg text-[10px] sm:text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Ottimo ({score})</span>
    }

    const getStatusBadge = (status: string) => {
        const map: Record<string, { icon: any; label: string; cls: string }> = {
            pending: { icon: Clock, label: 'In attesa', cls: 'bg-slate-500/10 text-slate-400 border-slate-500/20' },
            in_progress: { icon: Loader2, label: 'Elaborazione', cls: 'bg-blue-500/10 text-blue-400 border-blue-500/20 animate-pulse' },
            completed: { icon: CheckCircle2, label: 'Completato', cls: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' },
            error: { icon: AlertCircle, label: 'Errore', cls: 'bg-red-500/10 text-red-400 border-red-500/20' },
        }
        const s = map[status] || map.pending
        const Icon = s.icon
        return <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-[10px] sm:text-xs font-medium border ${s.cls}`}><Icon className="w-3 h-3" />{s.label}</span>
    }

    const totalAudits = audits.length
    const completedAudits = audits.filter(a => a.status === 'completed').length
    const completedWithScore = audits.filter(a => a.status === 'completed' && a.geo_score !== null)
    const avgScore = completedWithScore.length > 0 ? Math.round(completedWithScore.reduce((acc, curr) => acc + (curr.geo_score || 0), 0) / completedWithScore.length) : 0
    const emailsSentCount = audits.filter(a => a.email_sent).length

    return (
        <div className="max-w-full overflow-x-hidden space-y-4 sm:space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                    <h1 className="text-xl sm:text-3xl font-bold text-white flex items-center gap-3">
                        <Globe className="w-6 h-6 sm:w-8 sm:h-8 text-[#F90100]" /> GEO Audits
                    </h1>
                    <p className="text-xs sm:text-sm text-slate-400 mt-1">Audit posizionamento AI/GEO</p>
                </div>
                <div className="flex gap-2 self-start sm:self-auto">
                    <button onClick={() => setShowForm(!showForm)} className="flex items-center gap-2 px-3 sm:px-4 py-2 bg-[#F90100] hover:bg-[#d40100] text-white text-xs sm:text-sm font-medium rounded-xl transition-all">Nuovo Audit</button>
                    <button onClick={fetchAudits} disabled={loading} className="flex items-center gap-2 px-3 sm:px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-xl text-slate-300 hover:text-white transition-all disabled:opacity-50">
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                </div>
            </div>

            {error && <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-4 flex items-center gap-3 text-red-400"><AlertCircle className="w-5 h-5 flex-shrink-0" /><p className="text-sm">{error}</p></div>}

            {showForm && (
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4 sm:p-6">
                    <h3 className="text-base sm:text-lg font-semibold text-white mb-4">Nuovo GEO Audit</h3>
                    {geoMsg && <p className="text-sm text-emerald-400 mb-3">{geoMsg}</p>}
                    <div className="flex flex-col sm:flex-row gap-3 sm:items-end">
                        <div className="flex-1">
                            <label className="block text-xs text-slate-400 mb-1">URL Sito *</label>
                            <input type="text" value={geoUrl} onChange={(e) => setGeoUrl(e.target.value)} placeholder="https://esempio.it"
                                className="w-full px-4 py-2.5 bg-black border border-slate-700 rounded-xl text-white text-sm placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-[#F90100]/50" />
                        </div>
                        <div className="flex-1">
                            <label className="block text-xs text-slate-400 mb-1">Email</label>
                            <input type="email" value={geoEmail} onChange={(e) => setGeoEmail(e.target.value)}
                                className="w-full px-4 py-2.5 bg-black border border-slate-700 rounded-xl text-white text-sm placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-[#F90100]/50" />
                        </div>
                        <button onClick={triggerGeoAudit} disabled={geoLoading || !geoUrl}
                            className="px-6 py-2.5 bg-[#F90100] hover:bg-[#d40100] text-white text-sm font-medium rounded-xl disabled:opacity-50 flex items-center gap-2 justify-center">
                            {geoLoading && <RefreshCw className="w-4 h-4 animate-spin" />} Avvia
                        </button>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4">
                    <div className="flex items-center gap-2 mb-1"><Globe className="w-4 h-4 text-blue-500" /><span className="text-xs text-slate-400">Totale</span></div>
                    <p className="text-xl sm:text-2xl font-bold text-white">{totalAudits}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4">
                    <div className="flex items-center gap-2 mb-1"><CheckCircle2 className="w-4 h-4 text-emerald-500" /><span className="text-xs text-slate-400">Completati</span></div>
                    <p className="text-xl sm:text-2xl font-bold text-white">{completedAudits}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4">
                    <div className="flex items-center gap-2 mb-1"><TrendingUp className="w-4 h-4 text-orange-500" /><span className="text-xs text-slate-400">Score Medio</span></div>
                    <p className="text-xl sm:text-2xl font-bold text-white">{avgScore}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4">
                    <div className="flex items-center gap-2 mb-1"><Mail className="w-4 h-4 text-purple-500" /><span className="text-xs text-slate-400">Email Inviate</span></div>
                    <p className="text-xl sm:text-2xl font-bold text-white">{emailsSentCount}</p>
                </div>
            </div>

            {/* Mobile cards */}
            <div className="sm:hidden space-y-3">
                {audits.map((audit) => (
                    <div key={audit.id} className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4 space-y-2">
                        <div className="flex items-start justify-between">
                            <p className="text-sm font-medium text-white truncate flex-1 min-w-0">{cleanDomain(audit.url_sito)}</p>
                            {getStatusBadge(audit.status)}
                        </div>
                        <p className="text-xs text-slate-500">{audit.email_cliente}</p>
                        <div className="flex items-center justify-between">
                            {getScoreBadge(audit.geo_score)}
                            <div className="flex items-center gap-2">
                                {audit.pdf_path && <a href={`https://api.digidentityagency.it/api/reports/geo/${audit.id}/pdf`} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 px-2 py-1 bg-slate-700/50 hover:bg-slate-600/50 text-slate-200 rounded-lg text-[10px]"><Download className="w-3 h-3" />PDF</a>}
                                <span className="text-[10px] text-slate-500">{formatDateTime(audit.completed_at)}</span>
                            </div>
                        </div>
                    </div>
                ))}
                {audits.length === 0 && !loading && <div className="text-center text-slate-500 py-8 text-sm">Nessun GEO Audit</div>}
            </div>

            {/* Desktop table */}
            <div className="hidden sm:block bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-slate-700/50">
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Sito</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Email</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">GEO Score</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Stato</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">PDF</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Completato</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700/30">
                            {audits.map((audit) => (
                                <tr key={audit.id} className="hover:bg-slate-700/20 transition-colors">
                                    <td className="px-6 py-4"><p className="text-sm font-medium text-white">{cleanDomain(audit.url_sito)}</p></td>
                                    <td className="px-6 py-4 text-sm text-slate-300">{audit.email_cliente}</td>
                                    <td className="px-6 py-4">{getScoreBadge(audit.geo_score)}</td>
                                    <td className="px-6 py-4">{getStatusBadge(audit.status)}</td>
                                    <td className="px-6 py-4">{audit.pdf_path ? <a href={`https://api.digidentityagency.it/api/reports/geo/${audit.id}/pdf`} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 px-3 py-1.5 bg-slate-700/50 hover:bg-slate-600/50 text-slate-200 rounded-lg text-xs"><Download className="w-3.5 h-3.5" />Scarica</a> : <span className="text-slate-600">—</span>}</td>
                                    <td className="px-6 py-4 text-sm text-slate-400">{formatDateTime(audit.completed_at)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                {audits.length === 0 && !loading && <div className="p-12 text-center"><Globe className="w-12 h-12 text-slate-700 mx-auto mb-4 opacity-20" /><p className="text-slate-500">Nessun GEO Audit</p></div>}
            </div>
        </div>
    )
}
