'use client'

import { useEffect, useState, useMemo } from 'react'
import { supabase } from '@/lib/supabase'
import type { Appointment, AgentContact } from '@/lib/supabase'
import {
    Calendar, ChevronLeft, ChevronRight, Clock, User, MapPin,
    Video, Phone, FileText, X, CheckCircle, XCircle, AlertCircle,
    Loader, Filter, Eye, LayoutGrid, List, Columns, CalendarDays
} from 'lucide-react'

const DAYS = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
const DAYS_FULL = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
const MONTHS = ['Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno', 'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']

const statusConfig: Record<string, { icon: typeof CheckCircle; color: string; bg: string }> = {
    confermato: { icon: CheckCircle, color: 'text-emerald-400', bg: 'bg-emerald-400/10 border-emerald-400/30' },
    cancellato: { icon: XCircle, color: 'text-red-400', bg: 'bg-red-400/10 border-red-400/30' },
    completato: { icon: CheckCircle, color: 'text-blue-400', bg: 'bg-blue-400/10 border-blue-400/30' },
    no_show: { icon: AlertCircle, color: 'text-amber-400', bg: 'bg-amber-400/10 border-amber-400/30' },
}

const HOURS = Array.from({ length: 13 }, (_, i) => i + 8) // 8:00 - 20:00

type ViewMode = 'month' | 'week' | 'day' | 'list'

export default function CalendarioPage() {
    const [appointments, setAppointments] = useState<(Appointment & { contacts?: AgentContact })[]>([])
    const [loading, setLoading] = useState(true)
    const [currentDate, setCurrentDate] = useState(new Date())
    const [viewMode, setViewMode] = useState<ViewMode>('month')
    const [selectedAppointment, setSelectedAppointment] = useState<(Appointment & { contacts?: AgentContact }) | null>(null)
    const [filterStatus, setFilterStatus] = useState<string>('all')

    useEffect(() => {
        fetchAppointments()
        const interval = setInterval(fetchAppointments, 30000)
        return () => clearInterval(interval)
    }, [currentDate.getMonth(), currentDate.getFullYear()])

    async function fetchAppointments() {
        const year = currentDate.getFullYear()
        const month = currentDate.getMonth()
        // Fetch a wider range for week view that may span two months
        const start = new Date(year, month - 1, 1).toISOString()
        const end = new Date(year, month + 2, 0, 23, 59, 59).toISOString()

        const { data, error } = await supabase
            .from('appointments')
            .select('*, contacts(*)')
            .gte('data_ora', start)
            .lte('data_ora', end)
            .is('deleted_at', null)
            .order('data_ora', { ascending: true })

        if (!error && data) setAppointments(data)
        setLoading(false)
    }

    // Navigation
    function navigate(direction: number) {
        const d = new Date(currentDate)
        if (viewMode === 'month') d.setMonth(d.getMonth() + direction)
        else if (viewMode === 'week') d.setDate(d.getDate() + direction * 7)
        else if (viewMode === 'day') d.setDate(d.getDate() + direction)
        setCurrentDate(d)
    }

    function goToday() {
        setCurrentDate(new Date())
    }

    // Helpers
    function getDaysInMonth(date: Date) {
        return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate()
    }

    function getFirstDayOfMonth(date: Date) {
        const day = new Date(date.getFullYear(), date.getMonth(), 1).getDay()
        return day === 0 ? 6 : day - 1
    }

    function isToday(date: Date) {
        const today = new Date()
        return date.getDate() === today.getDate() && date.getMonth() === today.getMonth() && date.getFullYear() === today.getFullYear()
    }

    function isSameDay(d1: Date, d2: Date) {
        return d1.getDate() === d2.getDate() && d1.getMonth() === d2.getMonth() && d1.getFullYear() === d2.getFullYear()
    }

    function getAppointmentsForDay(date: Date) {
        return appointments.filter(a => {
            const ad = new Date(a.data_ora)
            return isSameDay(ad, date)
        })
    }

    function getAppointmentsForHour(date: Date, hour: number) {
        return appointments.filter(a => {
            const ad = new Date(a.data_ora)
            return isSameDay(ad, date) && ad.getHours() === hour
        })
    }

    function getContactName(a: Appointment & { contacts?: AgentContact }) {
        if (a.contacts) return a.contacts.nome || a.contacts.email || 'Sconosciuto'
        return 'Sconosciuto'
    }

    function getWeekDates(date: Date): Date[] {
        const d = new Date(date)
        const day = d.getDay()
        const diff = d.getDate() - (day === 0 ? 6 : day - 1)
        const monday = new Date(d.setDate(diff))
        return Array.from({ length: 7 }, (_, i) => {
            const wd = new Date(monday)
            wd.setDate(monday.getDate() + i)
            return wd
        })
    }

    function formatTime(dateStr: string) {
        return new Date(dateStr).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
    }

    // KPIs
    const today = new Date()
    const thisMonthAppts = appointments.filter(a => {
        const d = new Date(a.data_ora)
        return d.getMonth() === today.getMonth() && d.getFullYear() === today.getFullYear()
    })
    const todayAppts = appointments.filter(a => isSameDay(new Date(a.data_ora), today))
    const confirmed = thisMonthAppts.filter(a => a.stato === 'confermato').length
    const completed = thisMonthAppts.filter(a => a.stato === 'completato').length
    const cancelled = thisMonthAppts.filter(a => a.stato === 'cancellato').length

    // Navigation title
    function getNavTitle() {
        if (viewMode === 'month') return `${MONTHS[currentDate.getMonth()]} ${currentDate.getFullYear()}`
        if (viewMode === 'week') {
            const week = getWeekDates(currentDate)
            const s = week[0]
            const e = week[6]
            if (s.getMonth() === e.getMonth()) return `${s.getDate()} - ${e.getDate()} ${MONTHS[s.getMonth()]} ${s.getFullYear()}`
            return `${s.getDate()} ${MONTHS[s.getMonth()].substring(0, 3)} - ${e.getDate()} ${MONTHS[e.getMonth()].substring(0, 3)} ${s.getFullYear()}`
        }
        if (viewMode === 'day') {
            const dayIdx = currentDate.getDay() === 0 ? 6 : currentDate.getDay() - 1
            return `${DAYS_FULL[dayIdx]} ${currentDate.getDate()} ${MONTHS[currentDate.getMonth()]} ${currentDate.getFullYear()}`
        }
        return `${MONTHS[currentDate.getMonth()]} ${currentDate.getFullYear()}`
    }

    // Filtered for list
    const filteredAppointments = filterStatus === 'all' ? thisMonthAppts : thisMonthAppts.filter(a => a.stato === filterStatus)

    // View mode buttons config
    const viewModes: { mode: ViewMode; icon: typeof LayoutGrid; label: string }[] = [
        { mode: 'month', icon: LayoutGrid, label: 'Mese' },
        { mode: 'week', icon: Columns, label: 'Settimana' },
        { mode: 'day', icon: CalendarDays, label: 'Giorno' },
        { mode: 'list', icon: List, label: 'Lista' },
    ]

    // ============ RENDER ============

    const renderAppointmentPill = (a: Appointment & { contacts?: AgentContact }, compact = false) => {
        const sc = statusConfig[a.stato] || statusConfig.confermato
        return (
            <button
                key={a.id}
                onClick={(e) => { e.stopPropagation(); setSelectedAppointment(a) }}
                className={`w-full text-left rounded-lg border px-2 py-1 truncate text-xs transition-all hover:scale-[1.02] ${sc.bg}`}
                title={`${formatTime(a.data_ora)} - ${getContactName(a)}`}
            >
                {compact ? (
                    <span className="truncate">{formatTime(a.data_ora)} {a.titolo || getContactName(a)}</span>
                ) : (
                    <>
                        <span className="font-medium">{formatTime(a.data_ora)}</span>
                        <span className="ml-1 truncate">{a.titolo || getContactName(a)}</span>
                    </>
                )}
            </button>
        )
    }

    // MONTH VIEW
    const renderMonthView = () => {
        const daysInMonth = getDaysInMonth(currentDate)
        const firstDay = getFirstDayOfMonth(currentDate)
        const cells = []

        for (let i = 0; i < firstDay; i++) cells.push(<div key={`empty-${i}`} className="bg-[#0A0A0A] rounded-xl min-h-[100px]" />)

        for (let day = 1; day <= daysInMonth; day++) {
            const date = new Date(currentDate.getFullYear(), currentDate.getMonth(), day)
            const dayAppts = getAppointmentsForDay(date)
            const todayClass = isToday(date) ? 'ring-2 ring-[#F90100]' : ''

            cells.push(
                <div
                    key={day}
                    className={`bg-[#0A0A0A] rounded-xl p-2 min-h-[100px] hover:bg-[#111] transition-colors cursor-pointer ${todayClass}`}
                    onClick={() => { setCurrentDate(date); setViewMode('day') }}
                >
                    <p className={`text-xs font-bold mb-1 ${isToday(date) ? 'text-[#F90100]' : 'text-[#6B7280]'}`}>{day}</p>
                    <div className="space-y-1">
                        {dayAppts.slice(0, 3).map(a => renderAppointmentPill(a, true))}
                        {dayAppts.length > 3 && <p className="text-[10px] text-[#6B7280]">+{dayAppts.length - 3} altri</p>}
                    </div>
                </div>
            )
        }

        return (
            <div>
                <div className="grid grid-cols-7 gap-1 mb-1">
                    {DAYS.map(d => <div key={d} className="text-center text-xs font-semibold text-[#6B7280] py-2">{d}</div>)}
                </div>
                <div className="grid grid-cols-7 gap-1">{cells}</div>
            </div>
        )
    }

    // WEEK VIEW
    const renderWeekView = () => {
        const weekDates = getWeekDates(currentDate)

        return (
            <div className="overflow-auto">
                {/* Header row */}
                <div className="grid grid-cols-[60px_repeat(7,1fr)] sticky top-0 z-10 bg-[#0D0D0D]">
                    <div className="p-2" />
                    {weekDates.map((d, i) => (
                        <div
                            key={i}
                            className={`text-center py-2 cursor-pointer hover:bg-[#111] rounded-t-lg transition-colors ${isToday(d) ? 'bg-[#F90100]/10' : ''}`}
                            onClick={() => { setCurrentDate(d); setViewMode('day') }}
                        >
                            <p className="text-xs text-[#6B7280]">{DAYS[i]}</p>
                            <p className={`text-lg font-bold ${isToday(d) ? 'text-[#F90100]' : 'text-white'}`}>{d.getDate()}</p>
                        </div>
                    ))}
                </div>

                {/* Time grid */}
                <div className="grid grid-cols-[60px_repeat(7,1fr)]">
                    {HOURS.map(hour => (
                        <div key={hour} className="contents">
                            <div className="text-right pr-2 py-3 text-xs text-[#6B7280] border-t border-[#1F1F1F]">
                                {hour.toString().padStart(2, '0')}:00
                            </div>
                            {weekDates.map((d, di) => {
                                const hourAppts = getAppointmentsForHour(d, hour)
                                return (
                                    <div
                                        key={`${hour}-${di}`}
                                        className={`border-t border-l border-[#1F1F1F] p-1 min-h-[60px] hover:bg-[#111] transition-colors ${isToday(d) ? 'bg-[#F90100]/5' : ''}`}
                                    >
                                        <div className="space-y-1">
                                            {hourAppts.map(a => renderAppointmentPill(a, true))}
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    ))}
                </div>
            </div>
        )
    }

    // DAY VIEW
    const renderDayView = () => {
        const dayAppts = getAppointmentsForDay(currentDate)

        return (
            <div className="overflow-auto">
                {/* Summary */}
                <div className="flex items-center gap-4 mb-4 px-2">
                    <div className="flex items-center gap-2 text-sm text-[#9CA3AF]">
                        <Calendar className="w-4 h-4" />
                        <span>{dayAppts.length} appuntament{dayAppts.length === 1 ? 'o' : 'i'}</span>
                    </div>
                </div>

                {/* Time grid */}
                <div className="grid grid-cols-[70px_1fr]">
                    {HOURS.map(hour => {
                        const hourAppts = getAppointmentsForHour(currentDate, hour)
                        const now = new Date()
                        const isCurrentHour = isToday(currentDate) && now.getHours() === hour

                        return (
                            <div key={hour} className="contents">
                                <div className={`text-right pr-3 py-4 text-sm font-mono border-t border-[#1F1F1F] ${isCurrentHour ? 'text-[#F90100] font-bold' : 'text-[#6B7280]'}`}>
                                    {hour.toString().padStart(2, '0')}:00
                                </div>
                                <div className={`border-t border-[#1F1F1F] p-2 min-h-[70px] hover:bg-[#111] transition-colors ${isCurrentHour ? 'bg-[#F90100]/5 border-l-2 border-l-[#F90100]' : ''}`}>
                                    <div className="space-y-2">
                                        {hourAppts.map(a => {
                                            const sc = statusConfig[a.stato] || statusConfig.confermato
                                            const StatusIcon = sc.icon
                                            return (
                                                <button
                                                    key={a.id}
                                                    onClick={() => setSelectedAppointment(a)}
                                                    className={`w-full text-left rounded-xl border p-3 transition-all hover:scale-[1.01] ${sc.bg}`}
                                                >
                                                    <div className="flex items-center justify-between mb-1">
                                                        <span className="text-sm font-semibold text-white">{a.titolo || getContactName(a)}</span>
                                                        <StatusIcon className={`w-4 h-4 ${sc.color}`} />
                                                    </div>
                                                    <div className="flex items-center gap-3 text-xs text-[#9CA3AF]">
                                                        <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{formatTime(a.data_ora)}</span>
                                                        {a.durata_minuti && <span>{a.durata_minuti} min</span>}
                                                        <span className="flex items-center gap-1"><User className="w-3 h-3" />{getContactName(a)}</span>
                                                        {a.modalita && <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{a.modalita}</span>}
                                                    </div>
                                                    {a.note && <p className="text-xs text-[#6B7280] mt-1 truncate">{a.note}</p>}
                                                </button>
                                            )
                                        })}
                                    </div>
                                </div>
                            </div>
                        )
                    })}
                </div>
            </div>
        )
    }

    // LIST VIEW
    const renderListView = () => (
        <div>
            <div className="flex items-center gap-3 mb-4">
                <Filter className="w-4 h-4 text-[#6B7280]" />
                <select
                    className="bg-[#1F1F1F] border border-[#2D2D2D] rounded-lg px-3 py-1.5 text-sm text-white"
                    value={filterStatus}
                    onChange={e => setFilterStatus(e.target.value)}
                >
                    <option value="all">Tutti</option>
                    <option value="confermato">Confermati</option>
                    <option value="completato">Completati</option>
                    <option value="cancellato">Cancellati</option>
                    <option value="no_show">No Show</option>
                </select>
                <span className="text-xs text-[#6B7280]">{filteredAppointments.length} risultat{filteredAppointments.length === 1 ? 'o' : 'i'}</span>
            </div>
            <div className="space-y-3">
                {filteredAppointments.map(a => {
                    const sc = statusConfig[a.stato] || statusConfig.confermato
                    const StatusIcon = sc.icon
                    return (
                        <button
                            key={a.id}
                            onClick={() => setSelectedAppointment(a)}
                            className={`w-full text-left rounded-xl border p-4 transition-all hover:scale-[1.01] ${sc.bg}`}
                        >
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-semibold text-white">{a.titolo || getContactName(a)}</span>
                                <div className="flex items-center gap-2">
                                    <span className={`text-xs capitalize ${sc.color}`}>{a.stato}</span>
                                    <StatusIcon className={`w-4 h-4 ${sc.color}`} />
                                </div>
                            </div>
                            <div className="flex flex-wrap items-center gap-3 text-xs text-[#9CA3AF]">
                                <span className="flex items-center gap-1"><Calendar className="w-3 h-3" />{new Date(a.data_ora).toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit' })}</span>
                                <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{formatTime(a.data_ora)}</span>
                                {a.durata_minuti && <span>{a.durata_minuti} min</span>}
                                {a.modalita && <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{a.modalita}</span>}
                                <span className="flex items-center gap-1"><User className="w-3 h-3" />{getContactName(a)}</span>
                            </div>
                            {a.meet_link || a.hangout_link && (
                                <p className="text-xs text-blue-400 mt-2 flex items-center gap-1">
                                    <Video className="w-3 h-3" />
                                    <a href={a.meet_link || a.hangout_link} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()} className="hover:underline">
                                        Google Meet
                                    </a>
                                </p>
                            )}
                        </button>
                    )
                })}
                {filteredAppointments.length === 0 && <p className="text-center text-[#6B7280] py-8">Nessun appuntamento</p>}
            </div>
        </div>
    )

    return (
        <div className="space-y-6">
            {/* KPI */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {[
                    { label: 'Questo mese', value: thisMonthAppts.length, color: 'text-white' },
                    { label: 'Oggi', value: todayAppts.length, color: 'text-[#F90100]' },
                    { label: 'Confermati', value: confirmed, color: 'text-emerald-400' },
                    { label: 'Completati', value: completed, color: 'text-blue-400' },
                    { label: 'Cancellati', value: cancelled, color: 'text-red-400' },
                ].map(kpi => (
                    <div key={kpi.label} className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-2xl p-4 text-center">
                        <p className={`text-2xl font-bold ${kpi.color}`}>{kpi.value}</p>
                        <p className="text-xs text-[#6B7280] mt-1">{kpi.label}</p>
                    </div>
                ))}
            </div>

            {/* Toolbar */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                    <button onClick={() => navigate(-1)} className="p-2 hover:bg-[#1F1F1F] rounded-xl transition-colors">
                        <ChevronLeft className="w-5 h-5 text-white" />
                    </button>
                    <h2 className="text-lg font-bold text-white min-w-[220px] text-center">{getNavTitle()}</h2>
                    <button onClick={() => navigate(1)} className="p-2 hover:bg-[#1F1F1F] rounded-xl transition-colors">
                        <ChevronRight className="w-5 h-5 text-white" />
                    </button>
                    <button onClick={goToday} className="ml-2 px-3 py-1.5 text-xs font-semibold text-[#F90100] border border-[#F90100]/30 rounded-lg hover:bg-[#F90100]/10 transition-colors">
                        Oggi
                    </button>
                </div>
                <div className="flex items-center bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl overflow-hidden">
                    {viewModes.map(v => {
                        const Icon = v.icon
                        return (
                            <button
                                key={v.mode}
                                onClick={() => setViewMode(v.mode)}
                                className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium transition-colors ${viewMode === v.mode ? 'bg-[#F90100] text-white' : 'text-[#6B7280] hover:text-white hover:bg-[#1F1F1F]'}`}
                            >
                                <Icon className="w-3.5 h-3.5" />
                                {v.label}
                            </button>
                        )
                    })}
                </div>
            </div>

            {/* Content */}
            <div className="bg-[#0D0D0D] border border-[#1F1F1F] rounded-2xl p-4 overflow-auto max-h-[calc(100vh-320px)]">
                {loading ? (
                    <div className="flex items-center justify-center py-16">
                        <Loader className="w-8 h-8 text-[#F90100] animate-spin" />
                    </div>
                ) : (
                    <>
                        {viewMode === 'month' && renderMonthView()}
                        {viewMode === 'week' && renderWeekView()}
                        {viewMode === 'day' && renderDayView()}
                        {viewMode === 'list' && renderListView()}
                    </>
                )}
            </div>

            {/* Detail modal */}
            {selectedAppointment && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setSelectedAppointment(null)}>
                    <div className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-2xl w-full max-w-md max-h-[85vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
                        <div className="p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-bold text-white">{selectedAppointment.titolo || 'Appuntamento'}</h3>
                                <button onClick={() => setSelectedAppointment(null)} className="text-[#6B7280] hover:text-white"><X className="w-5 h-5" /></button>
                            </div>
                            {(() => {
                                const sc = statusConfig[selectedAppointment.stato] || statusConfig.confermato
                                const StatusIcon = sc.icon
                                return <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border mb-4 ${sc.bg} ${sc.color}`}><StatusIcon className="w-3 h-3" />{selectedAppointment.stato}</div>
                            })()}
                            <div className="space-y-3 text-sm">
                                {selectedAppointment.creato_da && (
                                    <div className="flex items-center gap-2 text-[#9CA3AF]"><User className="w-4 h-4" /><span>Creato da: {selectedAppointment.creato_da}</span></div>
                                )}
                                <div className="flex items-center gap-2 text-[#9CA3AF]">
                                    <Calendar className="w-4 h-4" />
                                    <span>{new Date(selectedAppointment.data_ora).toLocaleDateString('it-IT', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}</span>
                                </div>
                                <div className="flex items-center gap-2 text-[#9CA3AF]">
                                    <Clock className="w-4 h-4" />
                                    <span>{formatTime(selectedAppointment.data_ora)}{selectedAppointment.durata_minuti ? ` (${selectedAppointment.durata_minuti} min)` : ''}</span>
                                </div>
                                {selectedAppointment.modalita && (
                                    <div className="flex items-center gap-2 text-[#9CA3AF]"><MapPin className="w-4 h-4" /><span>{selectedAppointment.modalita}</span></div>
                                )}
                                {selectedAppointment.contacts && (
                                    <div className="bg-[#1F1F1F] rounded-xl p-3 space-y-1">
                                        <p className="text-white font-medium">{getContactName(selectedAppointment)}</p>
                                        {selectedAppointment.contacts.telefono && <p className="text-[#9CA3AF] flex items-center gap-1"><Phone className="w-3 h-3" />{selectedAppointment.contacts.telefono}</p>}
                                        {selectedAppointment.contacts.email && <p className="text-[#9CA3AF] text-xs">{selectedAppointment.contacts.email}</p>}
                                    </div>
                                )}
                                {selectedAppointment.note && (
                                    <div className="flex items-start gap-2 text-[#9CA3AF]"><FileText className="w-4 h-4 mt-0.5" /><span>{selectedAppointment.note}</span></div>
                                )}
                                {(selectedAppointment.meet_link || selectedAppointment.hangout_link) && (
                                    <a href={(selectedAppointment.meet_link || selectedAppointment.hangout_link) ?? undefined} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-blue-400 hover:underline">
                                        <Video className="w-4 h-4" />Google Meet
                                    </a>
                                )}

                            {/* Azioni */}
                            <div className="flex gap-2 mt-6 pt-4 border-t border-[#1F1F1F]">
                                {selectedAppointment.stato !== 'cancellato' && (
                                    <button
                                        onClick={async () => {
                                            await supabase.from('appointments').update({ stato: 'cancellato' }).eq('id', selectedAppointment.id)
                                            setSelectedAppointment(null)
                                            fetchAppointments()
                                        }}
                                        className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-red-400 border border-red-400/30 rounded-xl hover:bg-red-400/10 transition-colors"
                                    >
                                        <XCircle className="w-4 h-4" />Cancella
                                    </button>
                                )}
                                <button
                                    onClick={async () => {
                                        await supabase.from('appointments').update({ deleted_at: new Date().toISOString() }).eq('id', selectedAppointment.id)
                                        setSelectedAppointment(null)
                                        fetchAppointments()
                                    }}
                                    className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-[#6B7280] border border-[#2D2D2D] rounded-xl hover:bg-[#1F1F1F] transition-colors"
                                >
                                    <X className="w-4 h-4" />Elimina
                                </button>
                            </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
