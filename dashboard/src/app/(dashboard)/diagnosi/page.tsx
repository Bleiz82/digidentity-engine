'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import { FileText, RefreshCw, Cpu, Clock, Globe } from 'lucide-react'

interface DiagnosiRow {
    report_id: string; lead_id: string; nome_azienda: string; nome_contatto: string; email: string
    tipo_report: string; ai_model: string | null; ai_total_tokens: number | null; ai_cost_usd: number | null
    generation_time_seconds: number | null; html_url: string | null; report_status: string; report_generato_il: string
}

export default function DiagnosiPage() {
    const [diagnosi, setDiagnosi] = useState<DiagnosiRow[]>([])
    const [loading, setLoading] = useState(true)
    const [typeFilter, setTypeFilter] = useState('all')

    useEffect(() => { fetchDiagnosi() }, [])

    const fetchDiagnosi = async () => {
        setLoading(true)
        try { const { data } = await supabase.from('dashboard_diagnosi').select('*'); if (data) setDiagnosi(data) }
        catch (error) { console.error('Errore:', error) } finally { setLoading(false) }
    }

    const filtered = diagnosi.filter(d => typeFilter === 'all' || d.tipo_report === typeFilter)
    const totalCost = diagnosi.reduce((sum, d) => sum + (d.ai_cost_usd || 0), 0)
    const totalTokens = diagnosi.reduce((sum, d) => sum + (d.ai_total_tokens || 0), 0)
    const avgTime = diagnosi.length > 0 ? diagnosi.reduce((sum, d) => sum + (d.generation_time_seconds || 0), 0) / diagnosi.length : 0

    return (
        <div className="max-w-full overflow-x-hidden space-y-4 sm:space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                    <h1 className="text-xl sm:text-3xl font-bold text-white flex items-center gap-3">
                        <FileText className="w-6 h-6 sm:w-8 sm:h-8 text-orange-500" /> Diagnosi Generate
                    </h1>
                    <p className="text-xs sm:text-sm text-slate-400 mt-1">{filtered.length} report generati</p>
                </div>
                <button onClick={fetchDiagnosi} className="flex items-center gap-2 px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-xl text-slate-300 hover:text-white transition-all self-start sm:self-auto">
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Aggiorna
                </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4">
                    <div className="flex items-center gap-2 mb-1"><FileText className="w-4 h-4 text-orange-500" /><span className="text-xs text-slate-400">Report</span></div>
                    <p className="text-xl sm:text-2xl font-bold text-white">{diagnosi.length}</p>
                    <p className="text-[10px] text-slate-500">{diagnosi.filter(d => d.tipo_report === 'free').length} free · {diagnosi.filter(d => d.tipo_report === 'premium').length} premium</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4">
                    <div className="flex items-center gap-2 mb-1"><Cpu className="w-4 h-4 text-blue-500" /><span className="text-xs text-slate-400">Token</span></div>
                    <p className="text-xl sm:text-2xl font-bold text-white">{totalTokens.toLocaleString('it-IT')}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4">
                    <div className="flex items-center gap-2 mb-1"><span className="text-sm">$</span><span className="text-xs text-slate-400">Costo AI</span></div>
                    <p className="text-xl sm:text-2xl font-bold text-white">${totalCost.toFixed(4)}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4">
                    <div className="flex items-center gap-2 mb-1"><Clock className="w-4 h-4 text-emerald-500" /><span className="text-xs text-slate-400">Tempo Medio</span></div>
                    <p className="text-xl sm:text-2xl font-bold text-white">{avgTime.toFixed(1)}s</p>
                </div>
            </div>

            <div className="flex gap-2">
                {['all', 'free', 'premium'].map(t => (
                    <button key={t} onClick={() => setTypeFilter(t)} className={`px-3 sm:px-4 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all ${typeFilter === t ? 'bg-orange-500/10 text-orange-400 border border-orange-500/20' : 'bg-slate-800/50 text-slate-400 border border-slate-700/50 hover:text-white'}`}>
                        {t === 'all' ? 'Tutti' : t === 'free' ? 'Free' : 'Premium'}
                    </button>
                ))}
            </div>

            {/* Mobile cards */}
            <div className="sm:hidden space-y-3">
                {filtered.map((d) => (
                    <div key={d.report_id} className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4 space-y-2">
                        <div className="flex items-start justify-between">
                            <div className="min-w-0 flex-1">
                                <p className="text-sm font-medium text-white truncate">{d.nome_azienda}</p>
                                <p className="text-xs text-slate-500">{d.email}</p>
                            </div>
                            <span className={`ml-2 flex-shrink-0 inline-flex items-center px-2 py-0.5 rounded-lg text-[10px] font-medium border ${d.tipo_report === 'premium' ? 'bg-purple-500/10 text-purple-400 border-purple-500/20' : 'bg-blue-500/10 text-blue-400 border-blue-500/20'}`}>{d.tipo_report === 'premium' ? 'Premium' : 'Free'}</span>
                        </div>
                        <div className="flex items-center justify-between text-xs text-slate-400">
                            <span>{d.ai_model || '—'} · {d.ai_total_tokens?.toLocaleString('it-IT') || '—'} tok</span>
                            <span className="text-emerald-400">${d.ai_cost_usd?.toFixed(4) || '—'}</span>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded-lg border ${d.report_status === 'sent' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'}`}>{d.report_status}</span>
                            {d.html_url && <a href={d.html_url} target="_blank" rel="noopener noreferrer" className="text-red-400 flex items-center gap-1"><Globe className="w-3 h-3" />Apri</a>}
                        </div>
                    </div>
                ))}
                {filtered.length === 0 && !loading && <div className="text-center text-slate-500 py-8 text-sm">Nessuna diagnosi generata</div>}
            </div>

            {/* Desktop table */}
            <div className="hidden sm:block bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl overflow-hidden">
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
                                    <td className="px-6 py-4"><p className="text-sm font-medium text-white">{d.nome_azienda}</p><p className="text-xs text-slate-500">{d.email}</p></td>
                                    <td className="px-6 py-4"><span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium border ${d.tipo_report === 'premium' ? 'bg-purple-500/10 text-purple-400 border-purple-500/20' : 'bg-blue-500/10 text-blue-400 border-blue-500/20'}`}>{d.tipo_report === 'premium' ? 'Premium' : 'Free'}</span></td>
                                    <td className="px-6 py-4 text-sm text-slate-400">{d.ai_model || '—'}</td>
                                    <td className="px-6 py-4 text-sm text-slate-300">{d.ai_total_tokens?.toLocaleString('it-IT') || '—'}</td>
                                    <td className="px-6 py-4 text-sm text-emerald-400">${d.ai_cost_usd?.toFixed(4) || '—'}</td>
                                    <td className="px-6 py-4 text-sm">{d.html_url ? <a href={d.html_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 text-red-400 hover:text-red-300 underline"><Globe className="w-3.5 h-3.5" />Apri</a> : <span className="text-slate-600">—</span>}</td>
                                    <td className="px-6 py-4 text-sm text-slate-300">{d.generation_time_seconds ? `${d.generation_time_seconds.toFixed(1)}s` : '—'}</td>
                                    <td className="px-6 py-4"><span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium border ${d.report_status === 'sent' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : d.report_status === 'generated' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' : d.report_status === 'error' ? 'bg-red-500/10 text-red-400 border-red-500/20' : 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'}`}>{d.report_status || 'pending'}</span></td>
cd /opt/digidentity/digidentity-engine/dashboard
                                    <td className="px-6 py-4"><span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium border ${d.report_status === 'sent' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : d.report_status === 'generated' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' : d.report_status === 'error' ? 'bg-red-500/10 text-red-400 border-red-500/20' : 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'}`}>{d.report_status || 'pending'}</span></td>
                                    <td className="px-6 py-4 text-sm text-slate-400">{d.report_generato_il ? new Date(d.report_generato_il).toLocaleDateString('it-IT') : '—'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                {filtered.length === 0 && !loading && <div className="text-center text-slate-500 py-8 text-sm">Nessuna diagnosi trovata</div>}
            </div>
        </div>
    )
}
