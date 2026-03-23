'use client'

import { useEffect, useState } from 'react'
import { supabase, LeadPerProvincia } from '@/lib/supabase'
import { MapPin, RefreshCw } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function ProvinciePage() {
    const [provincie, setProvincie] = useState<LeadPerProvincia[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => { fetchProvincie() }, [])
    const fetchProvincie = async () => {
        setLoading(true)
        try { const { data } = await supabase.from('dashboard_lead_per_provincia').select('*'); if (data) setProvincie(data) }
        catch (error) { console.error('Errore:', error) } finally { setLoading(false) }
    }

    const totalLead = provincie.reduce((sum, p) => sum + p.totale_lead, 0)
    const totalConversioni = provincie.reduce((sum, p) => sum + p.conversioni, 0)
    const chartData = provincie.slice(0, 15).map(p => ({ provincia: p.provincia, lead: p.totale_lead, conversioni: p.conversioni }))

    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (<div className="bg-slate-800 border border-slate-700 rounded-xl p-3 shadow-xl">
                <p className="text-xs font-medium text-white mb-1">{label}</p>
                {payload.map((entry: any, i: number) => (<p key={i} className="text-xs" style={{ color: entry.color }}>{entry.name === 'lead' ? 'Lead' : 'Conversioni'}: {entry.value}</p>))}
            </div>)
        }
        return null
    }

    return (
        <div className="max-w-full overflow-x-hidden space-y-4 sm:space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                    <h1 className="text-xl sm:text-3xl font-bold text-white flex items-center gap-3">
                        <MapPin className="w-6 h-6 sm:w-8 sm:h-8 text-orange-500" /> Mappa Provincie
                    </h1>
                    <p className="text-xs sm:text-sm text-slate-400 mt-1">Distribuzione geografica dei lead</p>
                </div>
                <button onClick={fetchProvincie} className="flex items-center gap-2 px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-xl text-slate-300 hover:text-white transition-all self-start sm:self-auto">
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Aggiorna
                </button>
            </div>

            <div className="grid grid-cols-3 gap-3">
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4 sm:p-6">
                    <p className="text-xs text-slate-400 mb-1">Provincie</p>
                    <p className="text-xl sm:text-4xl font-bold text-white">{provincie.length}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4 sm:p-6">
                    <p className="text-xs text-slate-400 mb-1">Lead</p>
                    <p className="text-xl sm:text-4xl font-bold text-blue-400">{totalLead}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4 sm:p-6">
                    <p className="text-xs text-slate-400 mb-1">Conversioni</p>
                    <p className="text-xl sm:text-4xl font-bold text-emerald-400">{totalConversioni}</p>
                </div>
            </div>

            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4 sm:p-6">
                <h2 className="text-base sm:text-xl font-semibold text-white mb-4 sm:mb-6">Top 15 Provincie</h2>
                {chartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={Math.max(chartData.length * 35, 250)}>
                        <BarChart data={chartData} layout="vertical">
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis type="number" stroke="#64748b" fontSize={11} />
                            <YAxis dataKey="provincia" type="category" stroke="#64748b" fontSize={11} width={50} />
                            <Tooltip content={<CustomTooltip />} />
                            <Bar dataKey="lead" fill="#3b82f6" radius={[0, 8, 8, 0]} name="lead" />
                            <Bar dataKey="conversioni" fill="#10b981" radius={[0, 8, 8, 0]} name="Conversioni" />
                        </BarChart>
                    </ResponsiveContainer>
                ) : <div className="h-64 flex items-center justify-center text-slate-500">Nessun dato</div>}
            </div>

            {/* Mobile cards */}
            <div className="sm:hidden space-y-2">
                {provincie.map((p, i) => (
                    <div key={i} className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-3 flex items-center justify-between">
                        <span className="text-sm font-medium text-white flex items-center gap-2"><MapPin className="w-3 h-3 text-orange-500" />{p.provincia}</span>
                        <div className="flex items-center gap-3 text-xs">
                            <span className="text-blue-400">{p.totale_lead} lead</span>
                            <span className="text-emerald-400">{p.conversioni} conv</span>
                            <span className={`font-medium ${(p.tasso_conversione_percent || 0) >= 10 ? 'text-emerald-400' : 'text-slate-500'}`}>{p.tasso_conversione_percent || 0}%</span>
                        </div>
                    </div>
                ))}
            </div>

            {/* Desktop table */}
            <div className="hidden sm:block bg-slate-800/50 border border-slate-700/50 rounded-2xl overflow-hidden">
                <div className="p-6 border-b border-slate-700/50"><h2 className="text-xl font-semibold text-white">Dettaglio per Provincia</h2></div>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead><tr className="border-b border-slate-700/50">
                            <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Provincia</th>
                            <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Lead</th>
                            <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Conversioni</th>
                            <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Tasso</th>
                            <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Score</th>
                        </tr></thead>
                        <tbody className="divide-y divide-slate-700/30">
                            {provincie.map((p, i) => (
                                <tr key={i} className="hover:bg-slate-700/20 transition-colors">
                                    <td className="px-6 py-4"><span className="text-sm font-medium text-white flex items-center gap-2"><MapPin className="w-4 h-4 text-orange-500" />{p.provincia}</span></td>
                                    <td className="px-6 py-4 text-sm text-slate-300">{p.totale_lead}</td>
                                    <td className="px-6 py-4 text-sm text-emerald-400 font-medium">{p.conversioni}</td>
                                    <td className="px-6 py-4"><span className={`text-sm font-medium ${(p.tasso_conversione_percent || 0) > 10 ? 'text-emerald-400' : (p.tasso_conversione_percent || 0) > 0 ? 'text-yellow-400' : 'text-slate-500'}`}>{p.tasso_conversione_percent || 0}%</span></td>
                                    <td className="px-6 py-4"><span className={`text-sm font-bold ${(p.score_medio || 0) >= 70 ? 'text-emerald-400' : (p.score_medio || 0) >= 40 ? 'text-yellow-400' : (p.score_medio || 0) > 0 ? 'text-red-400' : 'text-slate-500'}`}>{p.score_medio ? Math.round(p.score_medio) : '—'}</span></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                {provincie.length === 0 && <div className="p-12 text-center text-slate-500">Nessun dato</div>}
            </div>
        </div>
    )
}
