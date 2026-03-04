'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import { RefreshCw, Globe, Download, AlertCircle, CheckCircle2, Clock, Loader2, TrendingUp, Mail } from 'lucide-react'

interface GeoAudit {
    id: string
    url_sito: string
    email_cliente: string
    status: 'pending' | 'in_progress' | 'completed' | 'error'
    geo_score: number | null
    pdf_path: string | null
    email_sent: boolean
    error_message: string | null
    created_at: string
    completed_at: string | null
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
        setGeoLoading(true)
        setGeoMsg(null)
        try {
            const res = await fetch('https://api.digidentityagency.it/api/payment/internal/genera-geo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-Internal-Key': 'dIgId_int3rn4L_X9kM2pV7nQ4wL6jR8' },
                body: JSON.stringify({ url_sito: geoUrl, email: geoEmail })
            })
            const data = await res.json()
            if (res.ok) {
                setGeoMsg('GEO Audit avviato!')
                setGeoUrl('')
                setShowForm(false)
                fetchAudits()
            } else {
                setGeoMsg(data.detail || data.error || 'Errore')
            }
        } catch { setGeoMsg('Errore di connessione') }
        finally { setGeoLoading(false) }
    }

    useEffect(() => {
        fetchAudits()
    }, [])

    const fetchAudits = async () => {
        setLoading(true)
        setError(null)
        try {
            const { data, error: sbError } = await supabase
                .from('geo_audits')
                .select('*')
                .order('created_at', { ascending: false })

            if (sbError) throw sbError
            if (data) setAudits(data)
        } catch (err: any) {
            console.error('Errore fetch audits:', err)
            setError(err.message || 'Errore durante il caricamento degli audit')
        } finally {
            setLoading(false)
        }
    }

    const cleanDomain = (url: string) => {
        try {
            return url.replace(/^https?:\/\//, '').replace(/^www\./, '').replace(/\/$/, '')
        } catch {
            return url
        }
    }

    const formatDateTime = (dateStr: string | null) => {
        if (!dateStr) return '—'
        const date = new Date(dateStr)
        return date.toLocaleDateString('it-IT', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).replace(',', ' alle')
    }

    const getScoreBadge = (score: number | null) => {
        if (score === null) return <span className="text-slate-600">—</span>

        if (score <= 39) return (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20">
                Critico ({score})
            </span>
        )
        if (score <= 69) return (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-yellow-500/10 text-yellow-400 border border-yellow-500/20">
                Da migliorare ({score})
            </span>
        )
        if (score <= 84) return (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
                Buono ({score})
            </span>
        )
        return (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Ottimo ({score})
            </span>
        )
    }

    const getStatusBadge = (status: string, errorMsg: string | null) => {
        switch (status) {
            case 'pending':
                return (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-500/10 text-slate-400 border border-slate-500/20">
                        <Clock className="w-3 h-3" />
                        In attesa
                    </span>
                )
            case 'in_progress':
                return (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20 animate-pulse">
                        <Loader2 className="w-3 h-3 animate-spin" />
                        In elaborazione
                    </span>
                )
            case 'completed':
                return (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        <CheckCircle2 className="w-3 h-3" />
                        Completato
                    </span>
                )
            case 'error':
                return (
                    <span 
                        title={errorMsg || 'Errore sconosciuto'} 
                        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20 cursor-help"
                    >
                        <AlertCircle className="w-3 h-3" />
                        Errore
                    </span>
                )
            default:
                return (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-500/10 text-slate-400 border border-slate-500/20">
                        {status}
                    </span>
                )
        }
    }

    // KPIs
    const totalAudits = audits.length
    const completedAudits = audits.filter(a => a.status === 'completed').length
    const completedWithScore = audits.filter(a => a.status === 'completed' && a.geo_score !== null)
    const avgScore = completedWithScore.length > 0 
        ? Math.round(completedWithScore.reduce((acc, curr) => acc + (curr.geo_score || 0), 0) / completedWithScore.length)
        : 0
    const emailsSentCount = audits.filter(a => a.email_sent).length

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                        <Globe className="w-8 h-8 text-[#F90100]" />
                        GEO Audits
                    </h1>
                    <p className="text-slate-400 mt-1">Audit sul posizionamento AI/GEO dei siti analizzati</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={() => setShowForm(!showForm)}
                        className="flex items-center gap-2 px-4 py-2 bg-[#F90100] hover:bg-[#d40100] text-white font-medium rounded-xl transition-all"
                    >
                        Nuovo GEO Audit
                    </button>
                    <button 
                        onClick={fetchAudits}
                        disabled={loading}
                        className="flex items-center gap-2 px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-xl text-slate-300 hover:text-white transition-all disabled:opacity-50"
                    >
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                        Aggiorna
                    </button>
                </div>
            </div>

            {/* ERROR BANNER */}
            {error && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-4 flex items-center gap-3 text-red-400">
                    <AlertCircle className="w-5 h-5 flex-shrink-0" />
                    <p className="text-sm font-medium">{error}</p>
                </div>
            )}

            {/* Form Nuovo GEO Audit */}
            {showForm && (
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Nuovo GEO Audit (interno)</h3>
                    {geoMsg && <p className="text-sm text-emerald-400 mb-3">{geoMsg}</p>}
                    <div className="flex flex-wrap gap-4 items-end">
                        <div className="flex-1 min-w-[250px]">
                            <label className="block text-xs text-slate-400 mb-1">URL Sito *</label>
                            <input type="text" value={geoUrl} onChange={(e) => setGeoUrl(e.target.value)} placeholder="https://esempio.it"
                                className="w-full px-4 py-2.5 bg-black border border-slate-700 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-[#F90100]/50" />
                        </div>
                        <div className="flex-1 min-w-[250px]">
                            <label className="block text-xs text-slate-400 mb-1">Email</label>
                            <input type="email" value={geoEmail} onChange={(e) => setGeoEmail(e.target.value)}
                                className="w-full px-4 py-2.5 bg-black border border-slate-700 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-[#F90100]/50" />
                        </div>
                        <button onClick={triggerGeoAudit} disabled={geoLoading || !geoUrl}
                            className="px-6 py-2.5 bg-[#F90100] hover:bg-[#d40100] text-white font-medium rounded-xl transition-all disabled:opacity-50 flex items-center gap-2">
                            {geoLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : null}
                            Avvia Audit
                        </button>
                    </div>
                </div>
            )}

            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5">
                    <div className="flex items-center gap-3 mb-2">
                        <Globe className="w-5 h-5 text-blue-500" />
                        <span className="text-sm text-slate-400">Totale Audit</span>
                    </div>
                    <p className="text-2xl font-bold text-white tracking-tight">{totalAudits}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5">
                    <div className="flex items-center gap-3 mb-2">
                        <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                        <span className="text-sm text-slate-400">Completati</span>
                    </div>
                    <p className="text-2xl font-bold text-white tracking-tight">{completedAudits}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5">
                    <div className="flex items-center gap-3 mb-2">
                        <TrendingUp className="w-5 h-5 text-orange-500" />
                        <span className="text-sm text-slate-400">GEO Score Medio</span>
                    </div>
                    <p className="text-2xl font-bold text-white tracking-tight">{avgScore}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5">
                    <div className="flex items-center gap-3 mb-2">
                        <Mail className="w-5 h-5 text-purple-500" />
                        <span className="text-sm text-slate-400">Email Inviate</span>
                    </div>
                    <p className="text-2xl font-bold text-white tracking-tight">{emailsSentCount}</p>
                </div>
            </div>

            {/* Tabella */}
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-slate-700/50">
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Sito Analizzato</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Email Cliente</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">GEO Score</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Stato</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">PDF</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Completato il</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700/30">
                            {audits.map((audit) => (
                                <tr key={audit.id} className="hover:bg-slate-700/20 transition-colors">
                                    <td className="px-6 py-4">
                                        <div className="group relative inline-block">
                                            <p className="text-sm font-medium text-white cursor-pointer underline decoration-dotted decoration-slate-600 underline-offset-4">
                                                {cleanDomain(audit.url_sito)}
                                            </p>
                                            <div className="absolute left-0 bottom-full mb-2 hidden group-hover:block z-20 bg-slate-900 border border-slate-700 p-2 rounded-lg text-xs text-white whitespace-nowrap shadow-xl">
                                                {audit.url_sito}
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-slate-300">{audit.email_cliente}</td>
                                    <td className="px-6 py-4">{getScoreBadge(audit.geo_score)}</td>
                                    <td className="px-6 py-4">{getStatusBadge(audit.status, audit.error_message)}</td>
                                    <td className="px-6 py-4">
                                        {audit.pdf_path ? (
                                            <a
                                                href={`https://api.digidentityagency.it/api/reports/geo/${audit.id}/pdf`}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="inline-flex items-center gap-2 px-3 py-1.5 bg-slate-700/50 hover:bg-slate-600/50 text-slate-200 hover:text-white rounded-lg text-xs font-medium transition-all"
                                            >
                                                <Download className="w-3.5 h-3.5" />
                                                Scarica
                                            </a>
                                        ) : (
                                            <span className="text-slate-600">—</span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-slate-400">
                                        {formatDateTime(audit.completed_at)}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {audits.length === 0 && !loading && (
                    <div className="p-12 text-center">
                        <Globe className="w-12 h-12 text-slate-700 mx-auto mb-4 opacity-20" />
                        <p className="text-slate-500">Nessun GEO Audit trovato. Gli audit appariranno qui dopo il pagamento.</p>
                    </div>
                )}
            </div>
        </div>
    )
}
