'use client'

import { useEffect, useState } from 'react'
import { supabase, Appointment, AgentContact } from '@/lib/supabase'
import {
    CalendarDays,
    ChevronLeft,
    ChevronRight,
    Clock,
    Phone,
    User,
    Video,
    ExternalLink,
    Loader,
    X,
    CheckCircle,
    XCircle,
    AlertCircle
} from 'lucide-react'

const DAYS = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
const MONTHS = ['Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno', 'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']

const statusConfig: Record<string, { icon: any; color: string; bg: string }> = {
    confermato: { icon: CheckCircle, color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
    cancellato: { icon: XCircle, color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/20' },
    completato: { icon: CheckCircle, color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20' },
    no_show: { icon: AlertCircle, color: 'text-orange-400', bg: 'bg-orange-500/10 border-orange-500/20' },
}

export default function CalendarioPage() {
    const [appointments, setAppointments] = useState<(Appointment & { contact?: AgentContact })[]>([])
    const [loading, setLoading] = useState(true)
    const [currentDate, setCurrentDate] = useState(new Date())
    const [viewMode, setViewMode] = useState<'month' | 'list'>('month')
    const [selectedAppointment, setSelectedAppointment] = useState<(Appointment & { contact?: AgentContact }) | null>(null)
    const [filterStatus, setFilterStatus] = useState('all')

    const currentYear = currentDate.getFullYear()
    const currentMonth = currentDate.getMonth()

    useEffect(() => {
        fetchAppointments()
        const interval = setInterval(fetchAppointments, 30000)
        return () => clearInterval(interval)
    }, [currentMonth, currentYear])

    const fetchAppointments = async () => {
        try {
            const startOfMonth = new Date(currentYear, currentMonth, 1).toISOString()
            const endOfMonth = new Date(currentYear, currentMonth + 1, 0, 23, 59, 59).toISOString()
            const { data, error } = await supabase
                .from('appointments')
                .select('*, contact:contacts(*)')
                .is('deleted_at', null)
                .gte('data_ora', startOfMonth)
                .lte('data_ora', endOfMonth)
                .order('data_ora', { ascending: true })
            if (data && !error) setAppointments(data as any)
        } catch (err) {
            console.error('Errore fetch appuntamenti:', err)
        } finally {
            setLoading(false)
        }
    }

    const prevMonth = () => setCurrentDate(new Date(currentYear, currentMonth - 1, 1))
    const nextMonth = () => setCurrentDate(new Date(currentYear, currentMonth + 1, 1))
    const goToday = () => setCurrentDate(new Date())

    const getDaysInMonth = () => {
        const firstDay = new Date(currentYear, currentMonth, 1)
        const lastDay = new Date(currentYear, currentMonth + 1, 0)
        const startDay = (firstDay.getDay() + 6) % 7
        const totalDays = lastDay.getDate()
        const days: { date: number; isCurrentMonth: boolean; dateObj: Date }[] = []
        const prevMonthLastDay = new Date(currentYear, currentMonth, 0).getDate()
        for (let i = startDay - 1; i >= 0; i--) {
            days.push({ date: prevMonthLastDay - i, isCurrentMonth: false, dateObj: new Date(currentYear, currentMonth - 1, prevMonthLastDay - i) })
        }
        for (let i = 1; i <= totalDays; i++) {
            days.push({ date: i, isCurrentMonth: true, dateObj: new Date(currentYear, currentMonth, i) })
        }
        const remaining = 42 - days.length
        for (let i = 1; i <= remaining; i++) {
            days.push({ date: i, isCurrentMonth: false, dateObj: new Date(currentYear, currentMonth + 1, i) })
        }
        return days
    }

    const getAppointmentsForDay = (date: Date) => {
        return appointments.filter(appt => {
            const d = new Date(appt.data_ora)
            return d.getDate() === date.getDate() && d.getMonth() === date.getMonth() && d.getFullYear() === date.getFullYear()
        })
    }

    const isToday = (date: Date) => {
        const t = new Date()
        return date.getDate() === t.getDate() && date.getMonth() === t.getMonth() && date.getFullYear() === t.getFullYear()
    }

    const getContactName = (contact?: AgentContact) => {
        if (!contact) return 'Sconosciuto'
        return contact.nome || contact.nome_attivita || contact.telefono || 'Sconosciuto'
    }

    const filteredAppointments = filterStatus === 'all' ? appointments : appointments.filter(a => a.stato === filterStatus)
    const totalMonth = appointments.length
    const confermati = appointments.filter(a => a.stato === 'confermato').length
    const completati = appointments.filter(a => a.stato === 'completato').length
    const cancellati = appointments.filter(a => a.stato === 'cancellato').length
    const oggi = appointments.filter(a => { const d = new Date(a.data_ora); const n = new Date(); return d.getDate() === n.getDate() && d.getMonth() === n.getMonth() && d.getFullYear() === n.getFullYear() }).length

    if (loading) {
        return <div className="flex items-center justify-center h-[80vh]"><Loader className="w-8 h-8 text-[#F90100] animate-spin" /></div>
    }

    return (
        <div>
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-white">Calendario</h1>
                    <p className="text-sm text-[#6B7280] mt-1">Appuntamenti gestiti da Digy</p>
                </div>
                <div className="flex items-center gap-2">
                    <button onClick={() => setViewMode('month')} className={`px-4 py-2 rounded-lg text-xs font-medium transition-all ${viewMode === 'month' ? 'bg-[#F90100]/10 text-[#F90100] border border-[#F90100]/30' : 'text-[#9CA3AF] hover:text-white bg-[#1F1F1F]'}`}>Calendario</button>
                    <button onClick={() => setViewMode('list')} className={`px-4 py-2 rounded-lg text-xs font-medium transition-all ${viewMode === 'list' ? 'bg-[#F90100]/10 text-[#F90100] border border-[#F90100]/30' : 'text-[#9CA3AF] hover:text-white bg-[#1F1F1F]'}`}>Lista</button>
                </div>
            </div>

            <div className="grid grid-cols-5 gap-4 mb-6">
                {[
                    { label: 'Questo mese', value: totalMonth, color: 'text-white' },
                    { label: 'Oggi', value: oggi, color: 'text-[#F90100]' },
                    { label: 'Confermati', value: confermati, color: 'text-emerald-400' },
                    { label: 'Completati', value: completati, color: 'text-blue-400' },
                    { label: 'Cancellati', value: cancellati, color: 'text-red-400' },
                ].map(kpi => (
                    <div key={kpi.label} className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl p-4">
                        <p className="text-xs text-[#6B7280] uppercase tracking-wider">{kpi.label}</p>
                        <p className={`text-2xl font-bold mt-1 ${kpi.color}`}>{kpi.value}</p>
                    </div>
                ))}
            </div>

            {viewMode === 'month' ? (
                <div className="rounded-2xl border border-[#1F1F1F] overflow-hidden bg-[#0A0A0A]">
                    <div className="flex items-center justify-between px-6 py-4 border-b border-[#1F1F1F]">
                        <button onClick={prevMonth} className="text-[#9CA3AF] hover:text-white p-2 rounded-lg hover:bg-[#1F1F1F]"><ChevronLeft className="w-5 h-5" /></button>
                        <div className="flex items-center gap-3">
                            <h2 className="text-lg font-bold text-white">{MONTHS[currentMonth]} {currentYear}</h2>
                            <button onClick={goToday} className="text-xs text-[#F90100] hover:underline">Oggi</button>
                        </div>
                        <button onClick={nextMonth} className="text-[#9CA3AF] hover:text-white p-2 rounded-lg hover:bg-[#1F1F1F]"><ChevronRight className="w-5 h-5" /></button>
                    </div>
                    <div className="grid grid-cols-7 border-b border-[#1F1F1F]">
                        {DAYS.map(day => (<div key={day} className="px-2 py-3 text-center text-xs font-semibold text-[#6B7280] uppercase">{day}</div>))}
                    </div>
                    <div className="grid grid-cols-7">
                        {getDaysInMonth().map((day, idx) => {
                            const dayAppts = getAppointmentsForDay(day.dateObj)
                            const today = isToday(day.dateObj)
                            return (
                                <div key={idx} className={`min-h-[100px] p-2 border-b border-r border-[#1F1F1F] ${!day.isCurrentMonth ? 'opacity-30' : ''} ${today ? 'bg-[#F90100]/5' : ''}`}>
                                    <span className={`text-xs font-medium ${today ? 'w-6 h-6 bg-[#F90100] text-white rounded-full flex items-center justify-center' : 'text-[#9CA3AF]'}`}>{day.date}</span>
                                    <div className="mt-1 space-y-1">
                                        {dayAppts.slice(0, 3).map(appt => {
                                            const time = new Date(appt.data_ora).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
                                            const st = statusConfig[appt.stato] || statusConfig.confermato
                                            return (<button key={appt.id} onClick={() => setSelectedAppointment(appt)} className={`w-full text-left px-1.5 py-1 rounded-md border text-[10px] truncate ${st.bg} ${st.color} hover:opacity-80 transition-opacity`}><span className="font-medium">{time}</span> {appt.titolo.split(' - ')[0]}</button>)
                                        })}
                                        {dayAppts.length > 3 && <p className="text-[10px] text-[#6B7280] text-center">+{dayAppts.length - 3} altri</p>}
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                </div>
            ) : (
                <div className="space-y-4">
                    <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-[#F90100]/50 mb-4">
                        <option value="all">Tutti gli stati</option>
                        <option value="confermato">Confermati</option>
                        <option value="completato">Completati</option>
                        <option value="cancellato">Cancellati</option>
                        <option value="no_show">No Show</option>
                    </select>
                    {filteredAppointments.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-16 text-[#6B7280] bg-[#0A0A0A] rounded-2xl border border-[#1F1F1F]"><CalendarDays className="w-10 h-10 mb-3" /><p className="text-sm">Nessun appuntamento questo mese</p></div>
                    ) : (
                        filteredAppointments.map(appt => {
                            const st = statusConfig[appt.stato] || statusConfig.confermato
                            const StatusIcon = st.icon
                            const apptDate = new Date(appt.data_ora)
                            return (
                                <div key={appt.id} onClick={() => setSelectedAppointment(appt)} className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl p-5 hover:border-[#F90100]/30 transition-all cursor-pointer">
                                    <div className="flex items-start justify-between">
                                        <div className="flex items-start gap-4">
                                            <div className="w-14 h-14 rounded-xl bg-[#1F1F1F] flex flex-col items-center justify-center flex-shrink-0">
                                                <span className="text-lg font-bold text-white">{apptDate.getDate()}</span>
                                                <span className="text-[10px] text-[#6B7280] uppercase">{apptDate.toLocaleDateString('it-IT', { month: 'short' })}</span>
                                            </div>
                                            <div>
                                                <h3 className="text-sm font-medium text-white">{appt.titolo}</h3>
                                                <div className="flex items-center gap-3 mt-1.5 text-xs text-[#6B7280]">
                                                    <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{apptDate.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })} · {appt.durata_minuti} min</span>
                                                    <span className="flex items-center gap-1 capitalize"><Video className="w-3 h-3" />{appt.modalita}</span>
                                                    <span className="flex items-center gap-1"><User className="w-3 h-3" />{getContactName(appt.contact)}</span>
                                                </div>
                                                {appt.note && <p className="text-xs text-[#6B7280] mt-1.5 line-clamp-1">{appt.note}</p>}
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-3">
                                            {appt.meet_link && <a href={appt.meet_link} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()} className="text-xs text-[#F90100] hover:underline flex items-center gap-1"><Video className="w-3.5 h-3.5" />Meet</a>}
                                            <span className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border ${st.bg} ${st.color}`}><StatusIcon className="w-3.5 h-3.5" />{appt.stato}</span>
                                        </div>
                                    </div>
                                </div>
                            )
                        })
                    )}
                </div>
            )}

            {selectedAppointment && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setSelectedAppointment(null)}>
                    <div className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-2xl w-full max-w-lg" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-between p-6 border-b border-[#1F1F1F]">
                            <h2 className="text-lg font-bold text-white">Dettaglio Appuntamento</h2>
                            <button onClick={() => setSelectedAppointment(null)} className="text-[#6B7280] hover:text-white"><X className="w-5 h-5" /></button>
                        </div>
                        <div className="p-6 space-y-5">
                            <div>
                                <h3 className="text-base font-semibold text-white">{selectedAppointment.titolo}</h3>
                                <div className="flex items-center gap-2 mt-2">
                                    {(() => { const st = statusConfig[selectedAppointment.stato] || statusConfig.confermato; const SI = st.icon; return <span className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border ${st.bg} ${st.color}`}><SI className="w-3.5 h-3.5" />{selectedAppointment.stato}</span> })()}
                                    <span className="text-xs text-[#6B7280]">Creato da: {selectedAppointment.creato_da}</span>
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                                <div className="bg-[#1F1F1F] rounded-xl p-3 flex items-center gap-3"><CalendarDays className="w-4 h-4 text-[#F90100]" /><div><p className="text-[10px] text-[#6B7280] uppercase">Data</p><p className="text-sm text-white">{new Date(selectedAppointment.data_ora).toLocaleDateString('it-IT', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' })}</p></div></div>
                                <div className="bg-[#1F1F1F] rounded-xl p-3 flex items-center gap-3"><Clock className="w-4 h-4 text-[#F90100]" /><div><p className="text-[10px] text-[#6B7280] uppercase">Orario</p><p className="text-sm text-white">{new Date(selectedAppointment.data_ora).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })} · {selectedAppointment.durata_minuti} min</p></div></div>
                                <div className="bg-[#1F1F1F] rounded-xl p-3 flex items-center gap-3"><Video className="w-4 h-4 text-[#F90100]" /><div><p className="text-[10px] text-[#6B7280] uppercase">Modalità</p><p className="text-sm text-white capitalize">{selectedAppointment.modalita}</p></div></div>
                                <div className="bg-[#1F1F1F] rounded-xl p-3 flex items-center gap-3"><User className="w-4 h-4 text-[#F90100]" /><div><p className="text-[10px] text-[#6B7280] uppercase">Cliente</p><p className="text-sm text-white">{getContactName(selectedAppointment.contact)}</p></div></div>
                            </div>
                            {selectedAppointment.cliente_telefono && <div className="bg-[#1F1F1F] rounded-xl p-3 flex items-center gap-3"><Phone className="w-4 h-4 text-[#F90100]" /><div><p className="text-[10px] text-[#6B7280] uppercase">Telefono</p><p className="text-sm text-white">{selectedAppointment.cliente_telefono}</p></div></div>}
                            {selectedAppointment.note && <div><p className="text-xs font-semibold text-[#6B7280] uppercase tracking-wider mb-2">Note</p><p className="text-sm text-[#9CA3AF] bg-[#1F1F1F] rounded-xl p-3">{selectedAppointment.note}</p></div>}
                            {selectedAppointment.meet_link && <a href={selectedAppointment.meet_link} target="_blank" rel="noopener noreferrer" className="flex items-center justify-center gap-2 w-full bg-[#F90100] hover:bg-[#F90100]/80 text-white font-medium text-sm py-3 rounded-xl transition-all"><Video className="w-4 h-4" />Apri Google Meet</a>}
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
