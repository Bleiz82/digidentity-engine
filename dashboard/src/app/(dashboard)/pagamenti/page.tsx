'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import { CreditCard, RefreshCw, CheckCircle, XCircle, Clock } from 'lucide-react'

export default function PagamentiPage() {
    const [pagamenti, setPagamenti] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [statusFilter, setStatusFilter] = useState('all')

    useEffect(() => { fetchPagamenti() }, [])

    const fetchPagamenti = async () => {
        setLoading(true)
        try {
            const { data, error } = await supabase
                .from('dashboard_pagamenti')
                .select('*')

            if (data) setPagamenti(data)
            if (error) console.error('Errore fetch pagamenti:', error)
        } catch (error) {
            console.error('Errore:', error)
        } finally {
            setLoading(false)
        }
    }

    const filtered = pagamenti.filter(p => statusFilter === 'all' || p.stato_pagamento === statusFilter)

    const totalRevenue = pagamenti.filter(p => p.stato_pagamento === 'completed').reduce((sum, p) => sum + Number(p.amount), 0)
    const completedCount = pagamenti.filter(p => p.stato_pagamento === 'completed').length
    const pendingCount = pagamenti.filter(p => p.stato_pagamento === 'pending').length
    const failedCount = pagamenti.filter(p => p.stato_pagamento === 'failed').length

    const getStatusIcon = (status: string) => {
        if (status === 'completed') return <CheckCircle className="w-4 h-4 text-emerald-400" />
        if (status === 'failed') return <XCircle className="w-4 h-4 text-red-400" />
        return <Clock className="w-4 h-4 text-orange-400" />
    }

    const getStatusColor = (status: string) => {
        const colors: Record<string, string> = {
            'completed': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
            'pending': 'bg-orange-500/10 text-orange-400 border-orange-500/20',
            'failed': 'bg-red-500/10 text-red-400 border-red-500/20',
        }
        return colors[status] || 'bg-slate-500/10 text-slate-400 border-slate-500/20'
    }

    const getStatusLabel = (status: string) => {
        const labels: Record<string, string> = { 'completed': 'Completato', 'pending': 'In attesa', 'failed': 'Fallito' }
        return labels[status] || status
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                        <CreditCard className="w-8 h-8 text-orange-500" />
                        Pagamenti
                    </h1>
                    <p className="text-slate-400 mt-1">{filtered.length} transazioni</p>
                </div>
                <button onClick={fetchPagamenti} className="flex items-center gap-2 px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-xl text-slate-300 hover:text-white transition-all">
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    Aggiorna
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5">
                    <p className="text-sm text-slate-400 mb-1">Revenue Totale</p>
                    <p className="text-3xl font-bold text-emerald-400">€{totalRevenue.toLocaleString('it-IT')}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5">
                    <p className="text-sm text-slate-400 mb-1">Completati</p>
                    <p className="text-3xl font-bold text-white">{completedCount}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5">
                    <p className="text-sm text-slate-400 mb-1">In Attesa</p>
                    <p className="text-3xl font-bold text-orange-400">{pendingCount}</p>
                </div>
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5">
                    <p className="text-sm text-slate-400 mb-1">Falliti</p>
                    <p className="text-3xl font-bold text-red-400">{failedCount}</p>
                </div>
            </div>

            <div className="flex gap-2">
                {['all', 'completed', 'pending', 'failed'].map(s => (
                    <button key={s} onClick={() => setStatusFilter(s)}
                        className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${statusFilter === s ? 'bg-orange-500/10 text-orange-400 border border-orange-500/20' : 'bg-slate-800/50 text-slate-400 border border-slate-700/50 hover:text-white'
                            }`}>
                        {s === 'all' ? 'Tutti' : getStatusLabel(s)}
                    </button>
                ))}
            </div>

            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-slate-700/50">
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Azienda</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Contatto</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Importo</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Stato</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Stripe</th>
                                <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-6 py-4">Data</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700/30">
                            {filtered.map((p) => (
                                <tr key={p.payment_id} className="hover:bg-slate-700/20 transition-colors">
                                    <td className="px-6 py-4">
                                        <p className="text-sm font-medium text-white">{p.nome_azienda}</p>
                                        <p className="text-xs text-slate-500">{p.citta}{p.provincia ? ` (${p.provincia})` : ''}</p>
                                    </td>
                                    <td className="px-6 py-4">
                                        <p className="text-sm text-slate-300">{p.nome_contatto}</p>
                                        <p className="text-xs text-slate-500">{p.email}</p>
                                    </td>
                                    <td className="px-6 py-4"><span className="text-lg font-bold text-white">€{p.amount}</span></td>
                                    <td className="px-6 py-4">
                                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border ${getStatusColor(p.stato_pagamento)}`}>
                                            {getStatusIcon(p.stato_pagamento)}
                                            {getStatusLabel(p.stato_pagamento)}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        {p.stripe_payment_intent ? (
                                            <p className="text-xs text-slate-500 font-mono">{p.stripe_payment_intent.substring(0, 20)}...</p>
                                        ) : <span className="text-xs text-slate-600">—</span>}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-slate-400">
                                        {new Date(p.pagamento_creato_il).toLocaleDateString('it-IT', {
                                            day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit'
                                        })}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                {filtered.length === 0 && !loading && (
                    <div className="p-12 text-center text-slate-500">Nessun pagamento registrato ancora</div>
                )}
            </div>
        </div>
    )
}
