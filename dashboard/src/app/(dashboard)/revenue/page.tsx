'use client'

import { useEffect, useState } from 'react'
import { supabase, RevenueMensile } from '@/lib/supabase'
import { TrendingUp, RefreshCw, Euro, Calendar, BarChart3 } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, Area, AreaChart } from 'recharts'

export default function RevenuePage() {
    const [revenue, setRevenue] = useState<RevenueMensile[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchRevenue()
    }, [])

    const fetchRevenue = async () => {
        setLoading(true)
        try {
            const { data, error } = await supabase
                .from('dashboard_revenue_mensile')
                .select('*')

            if (data) setRevenue(data)
            if (error) console.error('Errore fetch revenue:', error)
        } catch (error) {
            console.error('Errore:', error)
        } finally {
            setLoading(false)
        }
    }

    const totalRevenue = revenue.reduce((sum, r) => sum + Number(r.revenue_eur), 0)
    const totalTransazioni = revenue.reduce((sum, r) => sum + r.transazioni, 0)
    const avgTicket = totalTransazioni > 0 ? totalRevenue / totalTransazioni : 0

    const chartData = [...revenue].reverse().map(r => ({
        mese: new Date(r.mese).toLocaleDateString('it-IT', { month: 'short', year: '2-digit' }),
        revenue: Number(r.revenue_eur),
        transazioni: r.transazioni,
        ticket_medio: Number(r.ticket_medio)
    }))

    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-slate-800 border border-slate-700 rounded-xl p-4 shadow-xl">
                    <p className="text-sm font-medium text-white mb-2">{label}</p>
                    {payload.map((entry: any, index: number) => (
                        <p key={index} className="text-sm" style={{ color: entry.color }}>
                            {entry.name === 'revenue' ? 'Revenue' : 'Transazioni'}: {entry.name === 'revenue' ? `€${entry.value.toLocaleString('it-IT')}` : entry.value}
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
                        <TrendingUp className="w-8 h-8 text-orange-500" />
                        Revenue
                    </h1>
                    <p className="text-slate-400 mt-1">Andamento ricavi mensili</p>
                </div>
                <button onClick={fetchRevenue} className="flex items-center gap-2 px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-xl text-slate-300 hover:text-white transition-all">
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    Aggiorna
                </button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
                    <div className="flex items-center gap-3 mb-3">
                        <Euro className="w-6 h-6 text-emerald-500" />
                        <span className="text-sm text-slate-400">Revenue Totale</span>
                    </div>
                    <p className="text-4xl font-bold text-emerald-400">€{totalRevenue.toLocaleString('it-IT')}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
                    <div className="flex items-center gap-3 mb-3">
                        <BarChart3 className="w-6 h-6 text-blue-500" />
                        <span className="text-sm text-slate-400">Transazioni Totali</span>
                    </div>
                    <p className="text-4xl font-bold text-white">{totalTransazioni}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
                    <div className="flex items-center gap-3 mb-3">
                        <Calendar className="w-6 h-6 text-orange-500" />
                        <span className="text-sm text-slate-400">Ticket Medio</span>
                    </div>
                    <p className="text-4xl font-bold text-orange-400">€{avgTicket.toFixed(0)}</p>
                </div>
            </div>

            {/* Grafico Revenue */}
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
                <h2 className="text-xl font-semibold text-white mb-6">Revenue Mensile</h2>
                {chartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={400}>
                        <AreaChart data={chartData}>
                            <defs>
                                <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis dataKey="mese" stroke="#64748b" fontSize={12} />
                            <YAxis stroke="#64748b" fontSize={12} tickFormatter={(v) => `€${v}`} />
                            <Tooltip content={<CustomTooltip />} />
                            <Area type="monotone" dataKey="revenue" stroke="#f97316" fill="url(#colorRevenue)" strokeWidth={2} name="revenue" />
                        </AreaChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="h-96 flex items-center justify-center text-slate-500">
                        Nessun dato di revenue disponibile
                    </div>
                )}
            </div>

            {/* Grafico Transazioni */}
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
                <h2 className="text-xl font-semibold text-white mb-6">Transazioni Mensili</h2>
                {chartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis dataKey="mese" stroke="#64748b" fontSize={12} />
                            <YAxis stroke="#64748b" fontSize={12} />
                            <Tooltip content={<CustomTooltip />} />
                            <Bar dataKey="transazioni" fill="#3b82f6" radius={[8, 8, 0, 0]} name="Transazioni" />
                        </BarChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="h-72 flex items-center justify-center text-slate-500">
                        Nessun dato disponibile
                    </div>
                )}
            </div>

            {/* Tabella dettaglio */}
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl overflow-hidden">
                <div className="p-6 border-b border-slate-700/50">
                    <h2 className="text-xl font-semibold text-white">Dettaglio Mensile</h2>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-slate-700/50">
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Mese</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Transazioni</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Revenue</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Ticket Medio</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700/30">
                            {revenue.map((r, i) => (
                                <tr key={i} className="hover:bg-slate-700/20 transition-colors">
                                    <td className="px-6 py-4 text-sm font-medium text-white">
                                        {new Date(r.mese).toLocaleDateString('it-IT', { month: 'long', year: 'numeric' })}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-slate-300">{r.transazioni}</td>
                                    <td className="px-6 py-4 text-sm font-bold text-emerald-400">€{Number(r.revenue_eur).toLocaleString('it-IT')}</td>
                                    <td className="px-6 py-4 text-sm text-slate-300">€{Number(r.ticket_medio).toFixed(0)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                {revenue.length === 0 && (
                    <div className="p-12 text-center text-slate-500">Nessun dato di revenue disponibile</div>
                )}
            </div>
        </div>
    )
}
