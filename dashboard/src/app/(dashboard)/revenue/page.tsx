'use client'

import { useEffect, useState } from 'react'
import { supabase, RevenueMensile } from '@/lib/supabase'
import { TrendingUp, RefreshCw, Euro, Calendar, BarChart3 } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'

export default function RevenuePage() {
    const [revenue, setRevenue] = useState<RevenueMensile[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => { fetchRevenue() }, [])
    const fetchRevenue = async () => {
        setLoading(true)
        try { const { data } = await supabase.from('dashboard_revenue_mensile').select('*'); if (data) setRevenue(data) }
        catch (error) { console.error('Errore:', error) } finally { setLoading(false) }
    }

    const totalRevenue = revenue.reduce((sum, r) => sum + Number(r.revenue_eur), 0)
    const totalTransazioni = revenue.reduce((sum, r) => sum + r.transazioni, 0)
    const avgTicket = totalTransazioni > 0 ? totalRevenue / totalTransazioni : 0

    const chartData = [...revenue].reverse().map(r => ({
        mese: new Date(r.mese).toLocaleDateString('it-IT', { month: 'short', year: '2-digit' }),
        revenue: Number(r.revenue_eur), transazioni: r.transazioni
    }))

    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-slate-800 border border-slate-700 rounded-xl p-3 shadow-xl">
                    <p className="text-xs font-medium text-white mb-1">{label}</p>
                    {payload.map((entry: any, i: number) => (
                        <p key={i} className="text-xs" style={{ color: entry.color }}>
                            {entry.name === 'revenue' ? 'Revenue' : 'Transazioni'}: {entry.name === 'revenue' ? `€${entry.value.toLocaleString('it-IT')}` : entry.value}
                        </p>
                    ))}
                </div>
            )
        }
        return null
    }

    return (
        <div className="max-w-full overflow-x-hidden space-y-4 sm:space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                    <h1 className="text-xl sm:text-3xl font-bold text-white flex items-center gap-3">
                        <TrendingUp className="w-6 h-6 sm:w-8 sm:h-8 text-orange-500" /> Revenue
                    </h1>
                    <p className="text-xs sm:text-sm text-slate-400 mt-1">Andamento ricavi mensili</p>
                </div>
                <button onClick={fetchRevenue} className="flex items-center gap-2 px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-xl text-slate-300 hover:text-white transition-all self-start sm:self-auto">
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Aggiorna
                </button>
            </div>

            <div className="grid grid-cols-3 gap-3">
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4 sm:p-6">
                    <div className="flex items-center gap-2 mb-2"><Euro className="w-4 h-4 sm:w-6 sm:h-6 text-emerald-500" /><span className="text-xs text-slate-400">Revenue</span></div>
                    <p className="text-xl sm:text-4xl font-bold text-emerald-400">€{totalRevenue.toLocaleString('it-IT')}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4 sm:p-6">
                    <div className="flex items-center gap-2 mb-2"><BarChart3 className="w-4 h-4 sm:w-6 sm:h-6 text-blue-500" /><span className="text-xs text-slate-400">Transazioni</span></div>
                    <p className="text-xl sm:text-4xl font-bold text-white">{totalTransazioni}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4 sm:p-6">
                    <div className="flex items-center gap-2 mb-2"><Calendar className="w-4 h-4 sm:w-6 sm:h-6 text-orange-500" /><span className="text-xs text-slate-400">Ticket Medio</span></div>
                    <p className="text-xl sm:text-4xl font-bold text-orange-400">€{avgTicket.toFixed(0)}</p>
                </div>
            </div>

            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4 sm:p-6">
                <h2 className="text-base sm:text-xl font-semibold text-white mb-4 sm:mb-6">Revenue Mensile</h2>
                {chartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={window?.innerWidth < 640 ? 250 : 400}>
                        <AreaChart data={chartData}>
                            <defs><linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#f97316" stopOpacity={0.3} /><stop offset="95%" stopColor="#f97316" stopOpacity={0} /></linearGradient></defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis dataKey="mese" stroke="#64748b" fontSize={11} />
                            <YAxis stroke="#64748b" fontSize={11} tickFormatter={(v) => `€${v}`} />
                            <Tooltip content={<CustomTooltip />} />
                            <Area type="monotone" dataKey="revenue" stroke="#f97316" fill="url(#colorRevenue)" strokeWidth={2} name="revenue" />
                        </AreaChart>
                    </ResponsiveContainer>
                ) : <div className="h-64 flex items-center justify-center text-slate-500">Nessun dato</div>}
            </div>

            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4 sm:p-6">
                <h2 className="text-base sm:text-xl font-semibold text-white mb-4 sm:mb-6">Transazioni Mensili</h2>
                {chartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={window?.innerWidth < 640 ? 200 : 300}>
                        <BarChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis dataKey="mese" stroke="#64748b" fontSize={11} />
                            <YAxis stroke="#64748b" fontSize={11} />
                            <Tooltip content={<CustomTooltip />} />
                            <Bar dataKey="transazioni" fill="#3b82f6" radius={[8, 8, 0, 0]} name="Transazioni" />
                        </BarChart>
                    </ResponsiveContainer>
                ) : <div className="h-48 flex items-center justify-center text-slate-500">Nessun dato</div>}
            </div>

            {/* Mobile cards per dettaglio */}
            <div className="sm:hidden space-y-3">
                {revenue.map((r, i) => (
                    <div key={i} className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4 flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-white">{new Date(r.mese).toLocaleDateString('it-IT', { month: 'long', year: 'numeric' })}</p>
                            <p className="text-xs text-slate-500">{r.transazioni} transazioni · Ticket €{Number(r.ticket_medio).toFixed(0)}</p>
                        </div>
                        <p className="text-sm font-bold text-emerald-400">€{Number(r.revenue_eur).toLocaleString('it-IT')}</p>
                    </div>
                ))}
            </div>

            {/* Desktop table */}
            <div className="hidden sm:block bg-slate-800/50 border border-slate-700/50 rounded-2xl overflow-hidden">
                <div className="p-6 border-b border-slate-700/50"><h2 className="text-xl font-semibold text-white">Dettaglio Mensile</h2></div>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead><tr className="border-b border-slate-700/50">
                            <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Mese</th>
                            <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Transazioni</th>
                            <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Revenue</th>
                            <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Ticket Medio</th>
                        </tr></thead>
                        <tbody className="divide-y divide-slate-700/30">
                            {revenue.map((r, i) => (
                                <tr key={i} className="hover:bg-slate-700/20 transition-colors">
                                    <td className="px-6 py-4 text-sm font-medium text-white">{new Date(r.mese).toLocaleDateString('it-IT', { month: 'long', year: 'numeric' })}</td>
                                    <td className="px-6 py-4 text-sm text-slate-300">{r.transazioni}</td>
                                    <td className="px-6 py-4 text-sm font-bold text-emerald-400">€{Number(r.revenue_eur).toLocaleString('it-IT')}</td>
                                    <td className="px-6 py-4 text-sm text-slate-300">€{Number(r.ticket_medio).toFixed(0)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                {revenue.length === 0 && <div className="p-12 text-center text-slate-500">Nessun dato</div>}
            </div>
        </div>
    )
}
