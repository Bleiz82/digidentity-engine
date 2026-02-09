'use client'

import { useEffect, useState } from 'react'
import { supabase, CostiAI } from '@/lib/supabase'
import { Cpu, RefreshCw, Zap, DollarSign, Clock } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

export default function CostiAIPage() {
    const [costi, setCosti] = useState<CostiAI[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchCosti()
    }, [])

    const fetchCosti = async () => {
        setLoading(true)
        try {
            const { data, error } = await supabase
                .from('dashboard_costi_ai')
                .select('*')

            if (data) setCosti(data)
            if (error) console.error('Errore fetch costi AI:', error)
        } catch (error) {
            console.error('Errore:', error)
        } finally {
            setLoading(false)
        }
    }

    const totalCost = costi.reduce((sum, c) => sum + Number(c.costo_totale_usd), 0)
    const totalTokens = costi.reduce((sum, c) => sum + c.tokens_totali, 0)
    const totalReports = costi.reduce((sum, c) => sum + c.report_generati, 0)
    const avgCostPerReport = totalReports > 0 ? totalCost / totalReports : 0

    // Raggruppa per mese per il grafico
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
            return (
                <div className="bg-slate-800 border border-slate-700 rounded-xl p-4 shadow-xl">
                    <p className="text-sm font-medium text-white mb-2">{label}</p>
                    {payload.map((entry: any, index: number) => (
                        <p key={index} className="text-sm" style={{ color: entry.color }}>
                            {entry.name === 'free' ? 'Free' : 'Premium'}: ${entry.value.toFixed(4)}
                        </p>
                    ))}
                </div>
            )
        }
        return null
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                        <Cpu className="w-8 h-8 text-orange-500" />
                        Costi AI
                    </h1>
                    <p className="text-slate-400 mt-1">Monitoraggio utilizzo e costi Claude AI</p>
                </div>
                <button onClick={fetchCosti} className="flex items-center gap-2 px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-xl text-slate-300 hover:text-white transition-all">
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    Aggiorna
                </button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
                    <div className="flex items-center gap-3 mb-3">
                        <DollarSign className="w-6 h-6 text-emerald-500" />
                        <span className="text-sm text-slate-400">Costo Totale</span>
                    </div>
                    <p className="text-3xl font-bold text-white">${totalCost.toFixed(4)}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
                    <div className="flex items-center gap-3 mb-3">
                        <Zap className="w-6 h-6 text-yellow-500" />
                        <span className="text-sm text-slate-400">Token Totali</span>
                    </div>
                    <p className="text-3xl font-bold text-white">{totalTokens.toLocaleString('it-IT')}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
                    <div className="flex items-center gap-3 mb-3">
                        <Cpu className="w-6 h-6 text-blue-500" />
                        <span className="text-sm text-slate-400">Report Generati</span>
                    </div>
                    <p className="text-3xl font-bold text-white">{totalReports}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
                    <div className="flex items-center gap-3 mb-3">
                        <Clock className="w-6 h-6 text-orange-500" />
                        <span className="text-sm text-slate-400">Costo Medio/Report</span>
                    </div>
                    <p className="text-3xl font-bold text-white">${avgCostPerReport.toFixed(4)}</p>
                </div>
            </div>

            {/* Grafico */}
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
                <h2 className="text-xl font-semibold text-white mb-6">Costi Mensili per Tipo</h2>
                {chartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={350}>
                        <BarChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis dataKey="mese" stroke="#64748b" fontSize={12} />
                            <YAxis stroke="#64748b" fontSize={12} tickFormatter={(v) => `$${v}`} />
                            <Tooltip content={<CustomTooltip />} />
                            <Legend />
                            <Bar dataKey="free" fill="#3b82f6" radius={[8, 8, 0, 0]} name="free" />
                            <Bar dataKey="premium" fill="#a855f7" radius={[8, 8, 0, 0]} name="premium" />
                        </BarChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="h-80 flex items-center justify-center text-slate-500">
                        Nessun dato disponibile
                    </div>
                )}
            </div>

            {/* Tabella */}
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl overflow-hidden">
                <div className="p-6 border-b border-slate-700/50">
                    <h2 className="text-xl font-semibold text-white">Dettaglio Costi</h2>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-slate-700/50">
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Mese</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Tipo</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Report</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Token</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Costo Totale</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Costo Medio</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Tempo Medio</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700/30">
                            {costi.map((c, i) => (
                                <tr key={i} className="hover:bg-slate-700/20 transition-colors">
                                    <td className="px-6 py-4 text-sm font-medium text-white">
                                        {new Date(c.mese).toLocaleDateString('it-IT', { month: 'long', year: 'numeric' })}
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium border ${c.tipo_report === 'premium'
                                                ? 'bg-purple-500/10 text-purple-400 border-purple-500/20'
                                                : 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                                            }`}>
                                            {c.tipo_report === 'premium' ? 'Premium' : 'Free'}
                                        </span>
                                    </td>
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
                {costi.length === 0 && (
                    <div className="p-12 text-center text-slate-500">Nessun dato disponibile</div>
                )}
            </div>
        </div>
    )
}
