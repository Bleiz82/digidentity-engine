'use client'

import { useEffect, useState } from 'react'
import { supabase, CostiAI } from '@/lib/supabase'
import { Cpu, RefreshCw, Zap, DollarSign, Clock } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

export default function CostiAIPage() {
    const [costi, setCosti] = useState<CostiAI[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => { fetchCosti() }, [])
    const fetchCosti = async () => {
        setLoading(true)
        try { const { data } = await supabase.from('dashboard_costi_ai').select('*'); if (data) setCosti(data) }
        catch (error) { console.error('Errore:', error) } finally { setLoading(false) }
    }

    const totalCost = costi.reduce((sum, c) => sum + Number(c.costo_totale_usd), 0)
    const totalTokens = costi.reduce((sum, c) => sum + c.tokens_totali, 0)
    const totalReports = costi.reduce((sum, c) => sum + c.report_generati, 0)
    const avgCostPerReport = totalReports > 0 ? totalCost / totalReports : 0

    const monthMap = new Map<string, { mese: string; free: number; premium: number }>()
    costi.forEach(c => {
        const meseLabel = new Date(c.mese).toLocaleDateString('it-IT', { month: 'short', year: '2-digit' })
        const existing = monthMap.get(meseLabel) || { mese: meseLabel, free: 0, premium: 0 }
        if (c.tipo_report === 'free') existing.free = Number(c.costo_totale_usd)
        if (c.tipo_report === 'premium') existing.premium = Number(c.costo_totale_usd)
        monthMap.set(meseLabel, existing)
    })
    const chartData = Array.from(monthMap.values())

    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (<div className="bg-slate-800 border border-slate-700 rounded-xl p-3 shadow-xl">
                <p className="text-xs font-medium text-white mb-1">{label}</p>
                {payload.map((entry: any, i: number) => (<p key={i} className="text-xs" style={{ color: entry.color }}>{entry.name === 'free' ? 'Free' : 'Premium'}: ${entry.value.toFixed(4)}</p>))}
            </div>)
        }
        return null
    }

    return (
        <div className="max-w-full overflow-x-hidden space-y-4 sm:space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                    <h1 className="text-xl sm:text-3xl font-bold text-white flex items-center gap-3">
                        <Cpu className="w-6 h-6 sm:w-8 sm:h-8 text-orange-500" /> Costi AI
                    </h1>
                    <p className="text-xs sm:text-sm text-slate-400 mt-1">Monitoraggio utilizzo Claude AI</p>
                </div>
                <button onClick={fetchCosti} className="flex items-center gap-2 px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-xl text-slate-300 hover:text-white transition-all self-start sm:self-auto">
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Aggiorna
                </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4 sm:p-6">
                    <div className="flex items-center gap-2 mb-2"><DollarSign className="w-4 h-4 sm:w-6 sm:h-6 text-emerald-500" /><span className="text-xs text-slate-400">Costo</span></div>
                    <p className="text-xl sm:text-3xl font-bold text-white">${totalCost.toFixed(4)}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4 sm:p-6">
                    <div className="flex items-center gap-2 mb-2"><Zap className="w-4 h-4 sm:w-6 sm:h-6 text-yellow-500" /><span className="text-xs text-slate-400">Token</span></div>
                    <p className="text-xl sm:text-3xl font-bold text-white">{totalTokens.toLocaleString('it-IT')}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4 sm:p-6">
                    <div className="flex items-center gap-2 mb-2"><Cpu className="w-4 h-4 sm:w-6 sm:h-6 text-blue-500" /><span className="text-xs text-slate-400">Report</span></div>
                    <p className="text-xl sm:text-3xl font-bold text-white">{totalReports}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4 sm:p-6">
                    <div className="flex items-center gap-2 mb-2"><Clock className="w-4 h-4 sm:w-6 sm:h-6 text-orange-500" /><span className="text-xs text-slate-400">$/Report</span></div>
                    <p className="text-xl sm:text-3xl font-bold text-white">${avgCostPerReport.toFixed(4)}</p>
                </div>
            </div>

            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4 sm:p-6">
                <h2 className="text-base sm:text-xl font-semibold text-white mb-4 sm:mb-6">Costi Mensili</h2>
                {chartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={window?.innerWidth < 640 ? 220 : 350}>
                        <BarChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis dataKey="mese" stroke="#64748b" fontSize={11} />
                            <YAxis stroke="#64748b" fontSize={11} tickFormatter={(v) => `$${v}`} />
                            <Tooltip content={<CustomTooltip />} />
                            <Legend wrapperStyle={{ fontSize: '12px' }} />
                            <Bar dataKey="free" fill="#3b82f6" radius={[8, 8, 0, 0]} name="free" />
                            <Bar dataKey="premium" fill="#a855f7" radius={[8, 8, 0, 0]} name="premium" />
                        </BarChart>
                    </ResponsiveContainer>
                ) : <div className="h-52 flex items-center justify-center text-slate-500">Nessun dato</div>}
            </div>

            {/* Mobile cards */}
            <div className="sm:hidden space-y-2">
                {costi.map((c, i) => (
                    <div key={i} className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-3 flex items-center justify-between">
                        <div>
                            <p className="text-sm text-white">{new Date(c.mese).toLocaleDateString('it-IT', { month: 'short', year: '2-digit' })}</p>
                            <p className="text-[10px] text-slate-500">{c.tipo_report} · {c.report_generati} report · {c.tokens_totali.toLocaleString('it-IT')} tok</p>
                        </div>
                        <p className="text-sm font-bold text-white">${Number(c.costo_totale_usd).toFixed(4)}</p>
                    </div>
                ))}
            </div>

            {/* Desktop table */}
            <div className="hidden sm:block bg-slate-800/50 border border-slate-700/50 rounded-2xl overflow-hidden">
                <div className="p-6 border-b border-slate-700/50"><h2 className="text-xl font-semibold text-white">Dettaglio</h2></div>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead><tr className="border-b border-slate-700/50">
                            <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Mese</th>
                            <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Tipo</th>
                            <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Report</th>
                            <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Token</th>
                            <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Costo</th>
                            <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">$/Report</th>
                            <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Tempo</th>
                        </tr></thead>
                        <tbody className="divide-y divide-slate-700/30">
                            {costi.map((c, i) => (
                                <tr key={i} className="hover:bg-slate-700/20 transition-colors">
                                    <td className="px-6 py-4 text-sm font-medium text-white">{new Date(c.mese).toLocaleDateString('it-IT', { month: 'long', year: 'numeric' })}</td>
                                    <td className="px-6 py-4"><span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium border ${c.tipo_report === 'premium' ? 'bg-purple-500/10 text-purple-400 border-purple-500/20' : 'bg-blue-500/10 text-blue-400 border-blue-500/20'}`}>{c.tipo_report === 'premium' ? 'Premium' : 'Free'}</span></td>
                                    <td className="px-6 py-4 text-sm text-slate-300">{c.report_generati}</td>
                                    <td className="px-6 py-4 text-sm text-slate-300">{c.tokens_totali.toLocaleString('it-IT')}</td>
                                    <td className="px-6 py-4 text-sm font-medium text-white">${Number(c.costo_totale_usd).toFixed(4)}</td>
                                    <td className="px-6 py-4 text-sm text-slate-400">${Number(c.costo_medio_per_report).toFixed(4)}</td>
                                    <td className="px-6 py-4 text-sm text-slate-400">{Number(c.tempo_medio_generazione_sec).toFixed(1)}s</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                {costi.length === 0 && <div className="p-12 text-center text-slate-500">Nessun dato</div>}
            </div>
        </div>
    )
}
