'use client'

import { useEffect, useState } from 'react'
import { supabase, LeadPerProvincia } from '@/lib/supabase'
import { MapPin, RefreshCw } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function ProvinciePage() {
    const [provincie, setProvincie] = useState<LeadPerProvincia[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchProvincie()
    }, [])

    const fetchProvincie = async () => {
        setLoading(true)
        try {
            const { data, error } = await supabase
                .from('dashboard_lead_per_provincia')
                .select('*')

            if (data) setProvincie(data)
            if (error) console.error('Errore fetch provincie:', error)
        } catch (error) {
            console.error('Errore:', error)
        } finally {
            setLoading(false)
        }
    }

    const totalLead = provincie.reduce((sum, p) => sum + p.totale_lead, 0)
    const totalConversioni = provincie.reduce((sum, p) => sum + p.conversioni, 0)

    const chartData = provincie.slice(0, 15).map(p => ({
        provincia: p.provincia,
        lead: p.totale_lead,
        conversioni: p.conversioni
    }))

    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-slate-800 border border-slate-700 rounded-xl p-4 shadow-xl">
                    <p className="text-sm font-medium text-white mb-2">{label}</p>
                    {payload.map((entry: any, index: number) => (
                        <p key={index} className="text-sm" style={{ color: entry.color }}>
                            {entry.name === 'lead' ? 'Lead' : 'Conversioni'}: {entry.value}
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
                        <MapPin className="w-8 h-8 text-orange-500" />
                        Mappa Provincie
                    </h1>
                    <p className="text-slate-400 mt-1">Distribuzione geografica dei lead</p>
                </div>
                <button onClick={fetchProvincie} className="flex items-center gap-2 px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-xl text-slate-300 hover:text-white transition-all">
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    Aggiorna
                </button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
                    <p className="text-sm text-slate-400 mb-1">Provincie Attive</p>
                    <p className="text-4xl font-bold text-white">{provincie.length}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
                    <p className="text-sm text-slate-400 mb-1">Lead Totali</p>
                    <p className="text-4xl font-bold text-blue-400">{totalLead}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
                    <p className="text-sm text-slate-400 mb-1">Conversioni Totali</p>
                    <p className="text-4xl font-bold text-emerald-400">{totalConversioni}</p>
                </div>
            </div>

            {/* Grafico */}
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
                <h2 className="text-xl font-semibold text-white mb-6">Lead per Provincia (Top 15)</h2>
                {chartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={400}>
                        <BarChart data={chartData} layout="vertical">
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis type="number" stroke="#64748b" fontSize={12} />
                            <YAxis dataKey="provincia" type="category" stroke="#64748b" fontSize={12} width={60} />
                            <Tooltip content={<CustomTooltip />} />
                            <Bar dataKey="lead" fill="#3b82f6" radius={[0, 8, 8, 0]} name="lead" />
                            <Bar dataKey="conversioni" fill="#10b981" radius={[0, 8, 8, 0]} name="Conversioni" />
                        </BarChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="h-96 flex items-center justify-center text-slate-500">
                        Nessun dato disponibile
                    </div>
                )}
            </div>

            {/* Tabella */}
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl overflow-hidden">
                <div className="p-6 border-b border-slate-700/50">
                    <h2 className="text-xl font-semibold text-white">Dettaglio per Provincia</h2>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-slate-700/50">
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Provincia</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Lead</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Conversioni</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Tasso Conv.</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Score Medio</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700/30">
                            {provincie.map((p, i) => (
                                <tr key={i} className="hover:bg-slate-700/20 transition-colors">
                                    <td className="px-6 py-4">
                                        <span className="text-sm font-medium text-white flex items-center gap-2">
                                            <MapPin className="w-4 h-4 text-orange-500" />
                                            {p.provincia}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-slate-300">{p.totale_lead}</td>
                                    <td className="px-6 py-4 text-sm text-emerald-400 font-medium">{p.conversioni}</td>
                                    <td className="px-6 py-4">
                                        <span className={`text-sm font-medium ${(p.tasso_conversione_percent || 0) >= 10 ? 'text-emerald-400' :
                                                (p.tasso_conversione_percent || 0) > 0 ? 'text-yellow-400' :
                                                    'text-slate-500'
                                            }`}>
                                            {p.tasso_conversione_percent || 0}%
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`text-sm font-bold ${(p.score_medio || 0) >= 70 ? 'text-emerald-400' :
                                                (p.score_medio || 0) >= 40 ? 'text-yellow-400' :
                                                    (p.score_medio || 0) > 0 ? 'text-red-400' :
                                                        'text-slate-500'
                                            }`}>
                                            {p.score_medio ? Math.round(p.score_medio) : '—'}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                {provincie.length === 0 && (
                    <div className="p-12 text-center text-slate-500">Nessun dato disponibile</div>
                )}
            </div>
        </div>
    )
}
