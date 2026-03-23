'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import type { Appointment, AgentContact } from '@/lib/supabase'
import {
    Calendar, ChevronLeft, ChevronRight, Clock, User, MapPin,
    Video, Phone, FileText, X, CheckCircle, XCircle, AlertCircle,
    Loader, Filter, LayoutGrid, List, Columns, CalendarDays
} from 'lucide-react'

const DAYS = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
const DAYS_FULL = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
const MONTHS = ['Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno', 'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']
const HOURS = Array.from({ length: 13 }, (_, i) => i + 8)

const statusConfig: Record<string, { icon: typeof CheckCircle; color: string; bg: string }> = {
    confermato: { icon: CheckCircle, color: 'text-emerald-400', bg: 'bg-emerald-400/10 border-emerald-400/30' },
    cancellato: { icon: XCircle, color: 'text-red-400', bg: 'bg-red-400/10 border-red-400/30' },
    completato: { icon: CheckCircle, color: 'text-blue-400', bg: 'bg-blue-400/10 border-blue-400/30' },
    no_show: { icon: AlertCircle, color: 'text-amber-400', bg: 'bg-amber-400/10 border-amber-400/30' },
}

type ViewMode = 'month' | 'week' | 'day' | 'list'

export default function CalendarioPage() {
    const [appointments, setAppointments] = useState<(Appointment & { contacts?: AgentContact })[]>([])
    const [loading, setLoading] = useState(true)
    const [currentDate, setCurrentDate] = useState(new Date())
    const [viewMode, setViewMode] = useState<ViewMode>('list')
    const [selectedAppointment, setSelectedAppointment] = useState<(Appointment & { contacts?: AgentContact }) | null>(null)
    const [filterStatus, setFilterStatus] = useState<string>('all')
    const [isMobile, setIsMobile] = useState(false)

    useEffect(() => {
        const check = () => setIsMobile(window.innerWidth < 640)
        check(); window.addEventListener('resize', check); return () => window.removeEventListener('resize', check)
    }, [])

    useEffect(() => { fetchAppointments(); const i = setInterval(fetchAppointments, 30000); return () => clearInterval(i) }, [currentDate.getMonth(), currentDate.getFullYear()])

    async function fetchAppointments() {
        const year = currentDate.getFullYear(); const month = currentDate.getMonth()
        const start = new Date(year, month - 1, 1).toISOString(); const end = new Date(year, month + 2, 0, 23, 59, 59).toISOString()
        const { data, error } = await supabase.from('appointments').select('*, contacts(*)').gte('data_ora', start).lte('data_ora', end).is('deleted_at', null).order('data_ora', { ascending: true })
        if (!error && data) setAppointments(data); setLoading(false)
    }

    function navigate(dir: number) {
        const d = new Date(currentDate)
        if (viewMode === 'month') d.setMonth(d.getMonth() + dir)
        else if (viewMode === 'week') d.setDate(d.getDate() + dir * 7)
        else if (viewMode === 'day') d.setDate(d.getDate() + dir)
        else d.setMonth(d.getMonth() + dir)
        setCurrentDate(d)
    }

    const goToday = () => setCurrentDate(new Date())
    const getDaysInMonth = (date: Date) => new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate()
    const getFirstDayOfMonth = (date: Date) => { const d = new Date(date.getFullYear(), date.getMonth(), 1).getDay(); return d === 0 ? 6 : d - 1 }
    const isToday = (date: Date) => { const t = new Date(); return date.getDate() === t.getDate() && date.getMonth() === t.getMonth() && date.getFullYear() === t.getFullYear() }
    const isSameDay = (d1: Date, d2: Date) => d1.getDate() === d2.getDate() && d1.getMonth() === d2.getMonth() && d1.getFullYear() === d2.getFullYear()
    const getAppointmentsForDay = (date: Date) => appointments.filter(a => isSameDay(new Date(a.data_ora), date))
    const getAppointmentsForHour = (date: Date, hour: number) => appointments.filter(a => { const ad = new Date(a.data_ora); return isSameDay(ad, date) && ad.getHours() === hour })
    const getContactName = (a: Appointment & { contacts?: AgentContact }) => a.contacts?.nome || a.contacts?.email || 'Sconosciuto'
    const getWeekDates = (date: Date): Date[] => { const d = new Date(date); const day = d.getDay(); const diff = d.getDate() - (day === 0 ? 6 : day - 1); const mon = new Date(d.setDate(diff)); return Array.from({ length: 7 }, (_, i) => { const wd = new Date(mon); wd.setDate(mon.getDate() + i); return wd }) }
    const formatTime = (dateStr: string) => new Date(dateStr).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })

    const today = new Date()
    const thisMonthAppts = appointments.filter(a => { const d = new Date(a.data_ora); return d.getMonth() === today.getMonth() && d.getFullYear() === today.getFullYear() })
    const todayAppts = appointments.filter(a => isSameDay(new Date(a.data_ora), today))
    const confirmed = thisMonthAppts.filter(a => a.stato === 'confermato').length
    const completed = thisMonthAppts.filter(a => a.stato === 'completato').length
    const cancelled = thisMonthAppts.filter(a => a.stato === 'cancellato').length
    const filteredAppointments = filterStatus === 'all' ? thisMonthAppts : thisMonthAppts.filter(a => a.stato === filterStatus)

    function getNavTitle() {
        if (viewMode === 'month') return `${MONTHS[currentDate.getMonth()]} ${currentDate.getFullYear()}`
        if (viewMode === 'week') { const w = getWeekDates(currentDate); return `${w[0].getDate()} - ${w[6].getDate()} ${MONTHS[w[0].getMonth()].substring(0, 3)}` }
        if (viewMode === 'day') { const di = currentDate.getDay() === 0 ? 6 : currentDate.getDay() - 1; return `${DAYS_FULL[di]} ${currentDate.getDate()} ${MONTHS[currentDate.getMonth()].substring(0, 3)}` }
        return `${MONTHS[currentDate.getMonth()]} ${currentDate.getFullYear()}`
    }

    const viewModes: { mode: ViewMode; icon: typeof LayoutGrid; label: string; mobileLabel: string }[] = [
        { mode: 'month', icon: LayoutGrid, label: 'Mese', mobileLabel: 'M' },
        { mode: 'week', icon: Columns, label: 'Sett.', mobileLabel: 'S' },
        { mode: 'day', icon: CalendarDays, label: 'Giorno', mobileLabel: 'G' },
        { mode: 'list', icon: List, label: 'Lista', mobileLabel: 'L' },
    ]

    const renderPill = (a: Appointment & { contacts?: AgentContact }) => {
        const sc = statusConfig[a.stato] || statusConfig.confermato
        return <button key={a.id} onClick={(e) => { e.stopPropagation(); setSelectedAppointment(a) }} className={`w-full text-left rounded-lg border px-2 py-1 truncate text-[10px] sm:text-xs transition-all hover:scale-[1.02] ${sc.bg}`}>
            <span className="font-medium">{formatTime(a.data_ora)}</span> <span className="truncate">{a.titolo || getContactName(a)}</span>
        </button>
    }

    const renderMonthView = () => {
        const daysInMonth = getDaysInMonth(currentDate); const firstDay = getFirstDayOfMonth(currentDate); const cells = []
        for (let i = 0; i < firstDay; i++) cells.push(<div key={`e-${i}`} className="bg-[#0A0A0A] rounded-lg sm:rounded-xl min-h-[60px] sm:min-h-[100px]" />)
        for (let day = 1; day <= daysInMonth; day++) {
            const date = new Date(currentDate.getFullYear(), currentDate.getMonth(), day)
            const dayAppts = getAppointmentsForDay(date)
            cells.push(
                <div key={day}
                    className={`bg-[#0A0A0A] rounded-lg sm:rounded-xl p-1 sm:p-2 min-h-[60px] sm:min-h-[100px] hover:bg-[#111] cursor-pointer ${isToday(date) ? 'ring-2 ring-[#F90100]' : ''}`}
                    onClick={() => { setCurrentDate(date); setViewMode('day') }}
                >
                    <p className={`text-[10px] sm:text-xs font-bold mb-0.5 sm:mb-1 ${isToday(date) ? 'text-[#F90100]' : 'text-[#6B7280]'}`}>{day}</p>
                    <div className="space-y-0.5 sm:space-y-1">
                        {dayAppts.slice(0, isMobile ? 1 : 3).map(a => renderPill(a))}
                        {dayAppts.length > (isMobile ? 1 : 3) && (
                            <p className="text-[8px] sm:text-[10px] text-[#6B7280]">+{dayAppts.length - (isMobile ? 1 : 3)}</p>
                        )}
                    </div>
                </div>
            )
        }
        return <div><div className="grid grid-cols-7 gap-0.5 sm:gap-1 mb-0.5 sm:mb-1">{DAYS.map(d => <div key={d} className="text-center text-[10px] sm:text-xs font-semibold text-[#6B7280] py-1 sm:py-2">{isMobile ? d[0] : d}</div>)}</div><div className="grid grid-cols-7 gap-0.5 sm:gap-1">{cells}</div></div>
    }

    const renderWeekView = () => {
        const weekDates = getWeekDates(currentDate)
        return <div className="overflow-x-auto"><div className="min-w-[600px]">
            <div className="grid grid-cols-[50px_repeat(7,1fr)] sticky top-0 z-10 bg-[#0D0D0D]">
                <div className="p-1" />
                {weekDates.map((d, i) => <div key={i} className={`text-center py-1 sm:py-2 cursor-pointer hover:bg-[#111] rounded-t-lg ${isToday(d) ? 'bg-[#F90100]/10' : ''}`} onClick={() => { setCurrentDate(d); setViewMode('day') }}><p className="text-[10px] text-[#6B7280]">{DAYS[i]}</p><p className={`text-sm sm:text-lg font-bold ${isToday(d) ? 'text-[#F90100]' : 'text-white'}`}>{d.getDate()}</p></div>)}
            </div>
            <div className="grid grid-cols-[50px_repeat(7,1fr)]">
                {HOURS.map(hour => <div key={hour} className="contents">
                    <div className="text-right pr-1 sm:pr-2 py-2 sm:py-3 text-[10px] sm:text-xs text-[#6B7280] border-t border-[#1F1F1F]">{hour.toString().padStart(2, '0')}:00</div>
                    {weekDates.map((d, di) => <div key={`${hour}-${di}`} className={`border-t border-l border-[#1F1F1F] p-0.5 sm:p-1 min-h-[45px] sm:min-h-[60px] hover:bg-[#111] ${isToday(d) ? 'bg-[#F90100]/5' : ''}`}>
                        <div className="space-y-0.5">{getAppointmentsForHour(d, hour).map(a => renderPill(a))}</div>
                    </div>)}
                </div>)}
            </div>
        </div></div>
    }

    const renderDayView = () => {
        const dayAppts = getAppointmentsForDay(currentDate)
        return <div className="overflow-auto">
            <div className="flex items-center gap-3 mb-3 px-1"><Calendar className="w-4 h-4 text-[#9CA3AF]" /><span className="text-xs sm:text-sm text-[#9CA3AF]">{dayAppts.length} appuntament{dayAppts.length === 1 ? 'o' : 'i'}</span></div>
            <div className="grid grid-cols-[50px_1fr] sm:grid-cols-[70px_1fr]">
                {HOURS.map(hour => {
                    const hourAppts = getAppointmentsForHour(currentDate, hour); const now = new Date(); const isCurrent = isToday(currentDate) && now.getHours() === hour
                    return <div key={hour} className="contents">
                        <div className={`text-right pr-2 sm:pr-3 py-3 sm:py-4 text-xs sm:text-sm font-mono border-t border-[#1F1F1F] ${isCurrent ? 'text-[#F90100] font-bold' : 'text-[#6B7280]'}`}>{hour.toString().padStart(2, '0')}:00</div>
                        <div className={`border-t border-[#1F1F1F] p-1 sm:p-2 min-h-[55px] sm:min-h-[70px] hover:bg-[#111] ${isCurrent ? 'bg-[#F90100]/5 border-l-2 border-l-[#F90100]' : ''}`}>
                            <div className="space-y-1 sm:space-y-2">{hourAppts.map(a => {
                                const sc = statusConfig[a.stato] || statusConfig.confermato; const SI = sc.icon
                                return <button key={a.id} onClick={() => setSelectedAppointment(a)} className={`w-full text-left rounded-xl border p-2 sm:p-3 transition-all hover:scale-[1.01] ${sc.bg}`}>
                                    <div className="flex items-center justify-between mb-1"><span className="text-xs sm:text-sm font-semibold text-white truncate">{a.titolo || getContactName(a)}</span><SI className={`w-3 h-3 sm:w-4 sm:h-4 ${sc.color} flex-shrink-0`} /></div>
                                    <div className="flex flex-wrap items-center gap-2 text-[10px] sm:text-xs text-[#9CA3AF]">
                                        <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{formatTime(a.data_ora)}</span>
                                        {a.durata_minuti && <span>{a.durata_minuti}m</span>}
                                        <span className="flex items-center gap-1"><User className="w-3 h-3" />{getContactName(a)}</span>
                                    </div>
                                </button>
                            })}</div>
                        </div>
                    </div>
                })}
            </div>
        </div>
    }

    const renderListView = () => <div>
        <div className="flex items-center gap-2 sm:gap-3 mb-3 sm:mb-4">
            <Filter className="w-4 h-4 text-[#6B7280]" />
            <select className="bg-[#1F1F1F] border border-[#2D2D2D] rounded-lg px-2 sm:px-3 py-1.5 text-xs sm:text-sm text-white" value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
                <option value="all">Tutti</option><option value="confermato">Confermati</option><option value="completato">Completati</option><option value="cancellato">Cancellati</option><option value="no_show">No Show</option>
            </select>
            <span className="text-[10px] sm:text-xs text-[#6B7280]">{filteredAppointments.length} risultat{filteredAppointments.length === 1 ? 'o' : 'i'}</span>
        </div>
        <div className="space-y-2 sm:space-y-3">{filteredAppointments.map(a => {
            const sc = statusConfig[a.stato] || statusConfig.confermato; const SI = sc.icon
            return <button key={a.id} onClick={() => setSelectedAppointment(a)} className={`w-full text-left rounded-xl border p-3 sm:p-4 transition-all hover:scale-[1.01] ${sc.bg}`}>
                <div className="flex items-center justify-between mb-1.5 sm:mb-2"><span className="text-xs sm:text-sm font-semibold text-white truncate">{a.titolo || getContactName(a)}</span><div className="flex items-center gap-1.5 sm:gap-2 flex-shrink-0"><span className={`text-[10px] sm:text-xs capitalize ${sc.color}`}>{a.stato}</span><SI className={`w-3 h-3 sm:w-4 sm:h-4 ${sc.color}`} /></div></div>
                <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-[10px] sm:text-xs text-[#9CA3AF]">
                    <span className="flex items-center gap-1"><Calendar className="w-3 h-3" />{new Date(a.data_ora).toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit' })}</span>
                    <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{formatTime(a.data_ora)}</span>
                    {a.durata_minuti && <span>{a.durata_minuti}m</span>}
                    <span className="flex items-center gap-1"><User className="w-3 h-3" />{getContactName(a)}</span>
                </div>
                {(a.meet_link || a.hangout_link) && <p className="text-[10px] sm:text-xs text-blue-400 mt-1.5 flex items-center gap-1"><Video className="w-3 h-3" /><a href={(a.meet_link || a.hangout_link) ?? undefined} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()} className="hover:underline">Google Meet</a></p>}
            </button>
        })}{filteredAppointments.length === 0 && <p className="text-center text-[#6B7280] py-8 text-sm">Nessun appuntamento</p>}</div>
    </div>

    return (
        <div className="max-w-full overflow-x-hidden space-y-4 sm:space-y-6">
            <div className="grid grid-cols-3 sm:grid-cols-5 gap-2 sm:gap-3">
                {[
                    { label: 'Mese', value: thisMonthAppts.length, color: 'text-white' },
                    { label: 'Oggi', value: todayAppts.length, color: 'text-[#F90100]' },
                    { label: 'Confermati', value: confirmed, color: 'text-emerald-400' },
                    { label: 'Completati', value: completed, color: 'text-blue-400' },
                    { label: 'Cancellati', value: cancelled, color: 'text-red-400' },
                ].map(kpi => <div key={kpi.label} className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl sm:rounded-2xl p-3 sm:p-4 text-center">
                    <p className={`text-lg sm:text-2xl font-bold ${kpi.color}`}>{kpi.value}</p>
                    <p className="text-[10px] sm:text-xs text-[#6B7280] mt-0.5">{kpi.label}</p>
                </div>)}
            </div>

            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 sm:gap-3">
                <div className="flex items-center gap-1 sm:gap-2">
                    <button onClick={() => navigate(-1)} className="p-1.5 sm:p-2 hover:bg-[#1F1F1F] rounded-xl"><ChevronLeft className="w-4 h-4 sm:w-5 sm:h-5 text-white" /></button>
                    <h2 className="text-sm sm:text-lg font-bold text-white min-w-0 text-center">{getNavTitle()}</h2>
                    <button onClick={() => navigate(1)} className="p-1.5 sm:p-2 hover:bg-[#1F1F1F] rounded-xl"><ChevronRight className="w-4 h-4 sm:w-5 sm:h-5 text-white" /></button>
                    <button onClick={goToday} className="ml-1 sm:ml-2 px-2 sm:px-3 py-1 sm:py-1.5 text-[10px] sm:text-xs font-semibold text-[#F90100] border border-[#F90100]/30 rounded-lg hover:bg-[#F90100]/10">Oggi</button>
                </div>
                <div className="flex items-center bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl overflow-hidden">
                    {viewModes.map(v => {
                        const Icon = v.icon
                        return <button key={v.mode} onClick={() => setViewMode(v.mode)}
                            className={`flex items-center gap-1 px-2 sm:px-3 py-1.5 sm:py-2 text-[10px] sm:text-xs font-medium transition-colors ${viewMode === v.mode ? 'bg-[#F90100] text-white' : 'text-[#6B7280] hover:text-white hover:bg-[#1F1F1F]'}`}>
                            <Icon className="w-3 h-3 sm:w-3.5 sm:h-3.5" /><span className="hidden sm:inline">{v.label}</span><span className="sm:hidden">{v.mobileLabel}</span>
                        </button>
                    })}
                </div>
            </div>

            <div className="bg-[#0D0D0D] border border-[#1F1F1F] rounded-2xl p-2 sm:p-4 overflow-auto max-h-[calc(100vh-320px)]">
                {loading ? <div className="flex items-center justify-center py-16"><Loader className="w-8 h-8 text-[#F90100] animate-spin" /></div> : <>
                    {viewMode === 'month' && renderMonthView()}
                    {viewMode === 'week' && renderWeekView()}
                    {viewMode === 'day' && renderDayView()}
                    {viewMode === 'list' && renderListView()}
                </>}
            </div>

            {selectedAppointment && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-end sm:items-center justify-center" onClick={() => setSelectedAppointment(null)}>
                    <div className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-t-2xl sm:rounded-2xl w-full sm:max-w-md max-h-[85vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
                        <div className="p-4 sm:p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-base sm:text-lg font-bold text-white truncate">{selectedAppointment.titolo || 'Appuntamento'}</h3>
                                <button onClick={() => setSelectedAppointment(null)} className="text-[#6B7280] hover:text-white p-1"><X className="w-5 h-5" /></button>
                            </div>
                            {(() => { const sc = statusConfig[selectedAppointment.stato] || statusConfig.confermato; const SI = sc.icon; return <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border mb-4 ${sc.bg} ${sc.color}`}><SI className="w-3 h-3" />{selectedAppointment.stato}</div> })()}
                            <div className="space-y-3 text-sm">
                                {selectedAppointment.creato_da && <div className="flex items-center gap-2 text-[#9CA3AF]"><User className="w-4 h-4" /><span>Creato da: {selectedAppointment.creato_da}</span></div>}
                                <div className="flex items-center gap-2 text-[#9CA3AF]"><Calendar className="w-4 h-4" /><span>{new Date(selectedAppointment.data_ora).toLocaleDateString('it-IT', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}</span></div>
                                <div className="flex items-center gap-2 text-[#9CA3AF]"><Clock className="w-4 h-4" /><span>{formatTime(selectedAppointment.data_ora)}{selectedAppointment.durata_minuti ? ` (${selectedAppointment.durata_minuti} min)` : ''}</span></div>
                                {selectedAppointment.modalita && <div className="flex items-center gap-2 text-[#9CA3AF]"><MapPin className="w-4 h-4" /><span>{selectedAppointment.modalita}</span></div>}
                                {selectedAppointment.contacts && <div className="bg-[#1F1F1F] rounded-xl p-3 space-y-1"><p className="text-white font-medium">{getContactName(selectedAppointment)}</p>{selectedAppointment.contacts.telefono && <p className="text-[#9CA3AF] flex items-center gap-1 text-xs"><Phone className="w-3 h-3" />{selectedAppointment.contacts.telefono}</p>}{selectedAppointment.contacts.email && <p className="text-[#9CA3AF] text-xs">{selectedAppointment.contacts.email}</p>}</div>}
                                {selectedAppointment.note && <div className="flex items-start gap-2 text-[#9CA3AF]"><FileText className="w-4 h-4 mt-0.5 flex-shrink-0" /><span>{selectedAppointment.note}</span></div>}
                                {(selectedAppointment.meet_link || selectedAppointment.hangout_link) && <a href={(selectedAppointment.meet_link || selectedAppointment.hangout_link) ?? undefined} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-blue-400 hover:underline"><Video className="w-4 h-4" />Google Meet</a>}
                                <div className="flex gap-2 mt-4 sm:mt-6 pt-4 border-t border-[#1F1F1F]">
                                    {selectedAppointment.stato !== 'cancellato' && <button onClick={async () => { await supabase.from('appointments').update({ stato: 'cancellato' }).eq('id', selectedAppointment.id); setSelectedAppointment(null); fetchAppointments() }} className="flex items-center gap-2 px-3 sm:px-4 py-2 text-xs sm:text-sm font-medium text-red-400 border border-red-400/30 rounded-xl hover:bg-red-400/10"><XCircle className="w-4 h-4" />Cancella</button>}
                                    <button onClick={async () => { await supabase.from('appointments').update({ deleted_at: new Date().toISOString() }).eq('id', selectedAppointment.id); setSelectedAppointment(null); fetchAppointments() }} className="flex items-center gap-2 px-3 sm:px-4 py-2 text-xs sm:text-sm font-medium text-[#6B7280] border border-[#2D2D2D] rounded-xl hover:bg-[#1F1F1F]"><X className="w-4 h-4" />Elimina</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
