'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import { FileText, RefreshCw, Cpu, Clock, Globe } from 'lucide-react'

interface DiagnosiRow {
    report_id: string
    lead_id: string
    nome_azienda: string
    nome_contatto: string
    email: string
    tipo_report: string
    ai_model: string | null
    ai_total_tokens: number | null
    ai_cost_usd: number | null
    generation_time_seconds: number | null
    html_url: string | null
    report_status: string
    report_generato_il: string
}

export default function DiagnosiPage() {
    const [diagnosi, setDiagnosi] = useState<DiagnosiRow[]>([])
    const [loading, setLoading] = useState(true)
    const [typeFilter, setTypeFilter] = useState('all')

    useEffect(() => {
        fetchDiagnosi()
    }, [])

    const fetchDiagnosi = async () => {
        setLoading(true)
        try {
            const { data, error } = await supabase
                .from('dashboard_diagnosi')
                .select('*')

            if (data) setDiagnosi(data)
            if (error) console.error('Errore fetch diagnosi:', error)
        } catch (error) {
            console.error('Errore:', error)
        } finally {
            setLoading(false)
        }
    }

    const filtered = diagnosi.filter(d => typeFilter === 'all' || d.tipo_report === typeFilter)

    const totalCost = diagnosi.reduce((sum, d) => sum + (d.ai_cost_usd || 0), 0)
    const totalTokens = diagnosi.reduce((sum, d) => sum + (d.ai_total_tokens || 0), 0)
    const avgTime = diagnosi.length > 0
        ? diagnosi.reduce((sum, d) => sum + (d.generation_time_seconds || 0), 0) / diagnosi.length
        : 0



    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                        <FileText className="w-8 h-8 text-orange-500" />
                        Diagnosi Generate
                    </h1>
                    <p className="text-slate-400 mt-1">{filtered.length} report generati</p>
                </div>
                <button onClick={fetchDiagnosi} className="flex items-center gap-2 px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-xl text-slate-300 hover:text-white transition-all">
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    Aggiorna
                </button>
            </div>

            {/* Stats cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5">
                    <div className="flex items-center gap-3 mb-2">
                        <FileText className="w-5 h-5 text-orange-500" />
                        <span className="text-sm text-slate-400">Report Totali</span>
                    </div>
                    <p className="text-2xl font-bold text-white">{diagnosi.length}</p>
                    <p className="text-xs text-slate-500 mt-1">
                        {diagnosi.filter(d => d.tipo_report === 'free').length} free · {diagnosi.filter(d => d.tipo_report === 'premium').length} premium
                    </p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5">
                    <div className="flex items-center gap-3 mb-2">
                        <Cpu className="w-5 h-5 text-blue-500" />
                        <span className="text-sm text-slate-400">Token Totali</span>
                    </div>
                    <p className="text-2xl font-bold text-white">{totalTokens.toLocaleString('it-IT')}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5">
                    <div className="flex items-center gap-3 mb-2">
                        <span className="text-lg">$</span>
                        <span className="text-sm text-slate-400">Costo AI Totale</span>
                    </div>
                    <p className="text-2xl font-bold text-white">${totalCost.toFixed(4)}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5">
                    <div className="flex items-center gap-3 mb-2">
                        <Clock className="w-5 h-5 text-emerald-500" />
                        <span className="text-sm text-slate-400">Tempo Medio</span>
                    </div>
                    <p className="text-2xl font-bold text-white">{avgTime.toFixed(1)}s</p>
                </div>
            </div>

            {/* Filtro tipo */}
            <div className="flex gap-2">
                {['all', 'free', 'premium'].map(t => (
                    <button
                        key={t}
                        onClick={() => setTypeFilter(t)}
                        className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${typeFilter === t
                                ? 'bg-orange-500/10 text-orange-400 border border-orange-500/20'
                                : 'bg-slate-800/50 text-slate-400 border border-slate-700/50 hover:text-white'
                            }`}
                    >
                        {t === 'all' ? 'Tutti' : t === 'free' ? 'Free' : 'Premium'}
                    </button>
                ))}
            </div>

            {/* Tabella */}
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-slate-700/50">
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Azienda</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Tipo</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Modello AI</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Token</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Costo</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Report</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Tempo</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Stato</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Data</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700/30">
                            {filtered.map((d) => (
                                <tr key={d.report_id} className="hover:bg-slate-700/20 transition-colors">
                                    <td className="px-6 py-4">
                                        <p className="text-sm font-medium text-white">{d.nome_azienda}</p>
                                        <p className="text-xs text-slate-500">{d.email}</p>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium border ${d.tipo_report === 'premium'
                                                ? 'bg-purple-500/10 text-purple-400 border-purple-500/20'
                                                : 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                                            }`}>
                                            {d.tipo_report === 'premium' ? 'Premium' : 'Free'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-slate-400">{d.ai_model || '—'}</td>
                                    <td className="px-6 py-4 text-sm text-slate-300">{d.ai_total_tokens?.toLocaleString('it-IT') || '—'}</td>
                                    <td className="px-6 py-4 text-sm text-emerald-400">${d.ai_cost_usd?.toFixed(4) || '—'}</td>
                                    <td className="px-6 py-4 text-sm">
                                        {d.html_url ? (
                                            <a
                                                href={d.html_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="inline-flex items-center gap-1.5 text-red-400 hover:text-red-300 underline"
                                            >
                                                <Globe className="w-3.5 h-3.5" />
                                                Apri Report
                                            </a>
                                        ) : (
                                            <span className="text-slate-600">—</span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-slate-300">{d.generation_time_seconds ? `${d.generation_time_seconds.toFixed(1)}s` : '—'}</td>
                                    <td className="px-6 py-4">
                                        <span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium border ${d.report_status === 'sent' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                                                d.report_status === 'generated' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                                                    d.report_status === 'error' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                                                        'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
                                            }`}>
                                            {d.report_status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-slate-400">
                                        {new Date(d.report_generato_il).toLocaleDateString('it-IT', {
                                            day: '2-digit', month: '2-digit', year: 'numeric',
                                            hour: '2-digit', minute: '2-digit'
                                        })}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                {filtered.length === 0 && !loading && (
                    <div className="p-12 text-center text-slate-500">
                        Nessuna diagnosi generata ancora
                    </div>
                )}
            </div>
        </div>
    )
}
