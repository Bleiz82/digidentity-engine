'use client'

import { useEffect, useState } from 'react'
import { supabase, AgentContact, Conversation, Appointment } from '@/lib/supabase'
import {
    Contact, Search, Phone, Mail, MapPin, Store, Loader, X, MessageSquare,
    CalendarDays, Smartphone, Send, MessageCircle, AtSign, Globe, Tag,
    Clock, ChevronDown, ChevronUp, ExternalLink, User
} from 'lucide-react'
import Link from 'next/link'

const channelIcons: Record<string, any> = { whatsapp: Smartphone, telegram: Send, messenger: MessageCircle, instagram: AtSign, email: Mail, chatbot: Globe }
const channelColors: Record<string, string> = {
    whatsapp: 'text-green-400 bg-green-500/10 border-green-500/20', telegram: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
    messenger: 'text-purple-400 bg-purple-500/10 border-purple-500/20', instagram: 'text-pink-400 bg-pink-500/10 border-pink-500/20',
    email: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20', chatbot: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
}
const statusColors: Record<string, string> = {
    new: 'bg-blue-500/10 text-blue-400 border-blue-500/20', contacted: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    qualified: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20', converted: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    lost: 'bg-red-500/10 text-red-400 border-red-500/20',
}

export default function ContattiPage() {
    const [contacts, setContacts] = useState<AgentContact[]>([])
    const [loading, setLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState('')
    const [filterChannel, setFilterChannel] = useState('all')
    const [filterStatus, setFilterStatus] = useState('all')
    const [selectedContact, setSelectedContact] = useState<AgentContact | null>(null)
    const [contactConversations, setContactConversations] = useState<Conversation[]>([])
    const [contactAppointments, setContactAppointments] = useState<Appointment[]>([])
    const [loadingDetail, setLoadingDetail] = useState(false)
    const [sortField, setSortField] = useState<'created_at' | 'updated_at' | 'lead_score'>('updated_at')
    const [sortAsc, setSortAsc] = useState(false)

    useEffect(() => { fetchContacts(); const i = setInterval(fetchContacts, 30000); return () => clearInterval(i) }, [])

    const fetchContacts = async () => {
        try { const { data, error } = await supabase.from('contacts').select('*').order('updated_at', { ascending: false }); if (data && !error) setContacts(data) }
        catch (err) { console.error('Errore:', err) } finally { setLoading(false) }
    }

    const openContactDetail = async (contact: AgentContact) => {
        setSelectedContact(contact); setLoadingDetail(true)
        try {
            const [convRes, apptRes] = await Promise.all([
                supabase.from('conversations').select('*').eq('contact_id', contact.id).order('last_message_at', { ascending: false }),
                supabase.from('appointments').select('*').eq('contact_id', contact.id).is('deleted_at', null).order('data_ora', { ascending: false })
            ])
            if (convRes.data) setContactConversations(convRes.data)
            if (apptRes.data) setContactAppointments(apptRes.data)
        } catch (err) { console.error('Errore:', err) } finally { setLoadingDetail(false) }
    }

    const getContactName = (c: AgentContact) => c.nome || c.nome_attivita || c.email || c.telefono || 'Sconosciuto'
    const getActiveChannels = (c: AgentContact) => {
        const ch: string[] = []
        if (c.whatsapp_id) ch.push('whatsapp'); if (c.telegram_id) ch.push('telegram'); if (c.messenger_id) ch.push('messenger')
        if (c.instagram_id) ch.push('instagram'); if (c.email_channel_id) ch.push('email'); if (c.chatbot_session) ch.push('chatbot')
        return ch
    }

    const filteredContacts = contacts.filter(c => {
        const name = getContactName(c).toLowerCase()
        const matchesSearch = searchQuery === '' || name.includes(searchQuery.toLowerCase()) || (c.email || '').toLowerCase().includes(searchQuery.toLowerCase()) || (c.telefono || '').toLowerCase().includes(searchQuery.toLowerCase()) || (c.nome_attivita || '').toLowerCase().includes(searchQuery.toLowerCase())
        return matchesSearch && (filterChannel === 'all' || c.canale_primo_contatto === filterChannel) && (filterStatus === 'all' || c.lead_status === filterStatus)
    }).sort((a, b) => {
        const aVal = a[sortField]; const bVal = b[sortField]
        if (typeof aVal === 'number' && typeof bVal === 'number') return sortAsc ? aVal - bVal : bVal - aVal
        return sortAsc ? String(aVal || '').localeCompare(String(bVal || '')) : String(bVal || '').localeCompare(String(aVal || ''))
    })

    const toggleSort = (field: typeof sortField) => { if (sortField === field) setSortAsc(!sortAsc); else { setSortField(field); setSortAsc(false) } }
    const SortIcon = ({ field }: { field: typeof sortField }) => { if (sortField !== field) return null; return sortAsc ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" /> }

    if (loading) return <div className="flex items-center justify-center h-[80vh]"><Loader className="w-8 h-8 text-[#F90100] animate-spin" /></div>

    return (
        <div className="max-w-full overflow-x-hidden">
            <div className="mb-4 sm:mb-6">
                <h1 className="text-lg sm:text-2xl font-bold text-white">Contatti Agent</h1>
                <p className="text-[10px] sm:text-sm text-[#6B7280] mt-0.5 sm:mt-1">{contacts.length} contatti totali</p>
            </div>

            <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 mb-4 sm:mb-6">
                <div className="relative flex-1 min-w-0">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7280]" />
                    <input type="text" placeholder="Cerca nome, email, telefono..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-[#6B7280] focus:outline-none focus:border-[#F90100]/50" />
                </div>
                <div className="flex gap-2">
                    <select value={filterChannel} onChange={(e) => setFilterChannel(e.target.value)}
                        className="flex-1 sm:flex-none bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl px-3 py-2.5 text-xs sm:text-sm text-white focus:outline-none focus:border-[#F90100]/50">
                        <option value="all">Tutti i canali</option>
                        <option value="whatsapp">WhatsApp</option><option value="telegram">Telegram</option>
                        <option value="messenger">Messenger</option><option value="instagram">Instagram</option>
                        <option value="email">Email</option><option value="chatbot">Chatbot</option>
                    </select>
                    <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}
                        className="flex-1 sm:flex-none bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl px-3 py-2.5 text-xs sm:text-sm text-white focus:outline-none focus:border-[#F90100]/50">
                        <option value="all">Tutti</option><option value="new">Nuovo</option>
                        <option value="contacted">Contattato</option><option value="qualified">Qualificato</option>
                        <option value="converted">Convertito</option><option value="lost">Perso</option>
                    </select>
                </div>
            </div>

            {/* Mobile cards */}
            <div className="sm:hidden space-y-3">
                {filteredContacts.map((contact) => {
                    const channels = getActiveChannels(contact)
                    const stColor = statusColors[contact.lead_status] || statusColors.new
                    return (
                        <div key={contact.id} onClick={() => openContactDetail(contact)}
                            className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-2xl p-4 space-y-3 active:bg-[#1F1F1F]/50 cursor-pointer">
                            <div className="flex items-start justify-between">
                                <div className="flex items-center gap-3 min-w-0 flex-1">
                                    <div className="w-9 h-9 rounded-full bg-[#1F1F1F] flex items-center justify-center flex-shrink-0">
                                        <User className="w-4 h-4 text-[#6B7280]" />
                                    </div>
                                    <div className="min-w-0">
                                        <p className="text-sm font-medium text-white truncate">{getContactName(contact)}</p>
                                        {contact.nome_attivita && <p className="text-[10px] text-[#6B7280] truncate flex items-center gap-1"><Store className="w-3 h-3" />{contact.nome_attivita}</p>}
                                    </div>
                                </div>
                                <span className={`text-[10px] px-2 py-0.5 rounded-full border flex-shrink-0 ${stColor}`}>{contact.lead_status}</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-1">
                                    {channels.map(ch => {
                                        const Icon = channelIcons[ch] || Globe
                                        const color = channelColors[ch] || 'text-gray-400 bg-gray-500/10 border-gray-500/20'
                                        return <span key={ch} className={`w-6 h-6 rounded-md border flex items-center justify-center ${color}`}><Icon className="w-3 h-3" /></span>
                                    })}
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="w-12 h-1.5 bg-[#1F1F1F] rounded-full overflow-hidden">
                                        <div className="h-full bg-[#F90100] rounded-full" style={{ width: `${Math.min(contact.lead_score * 10, 100)}%` }} />
                                    </div>
                                    <span className="text-[10px] text-[#9CA3AF]">{contact.lead_score}</span>
                                </div>
                            </div>
                            <div className="flex items-center gap-3 text-[10px] text-[#6B7280]">
                                {contact.telefono && <span className="flex items-center gap-1"><Phone className="w-3 h-3" />{contact.telefono}</span>}
                                {contact.email && <span className="flex items-center gap-1 truncate"><Mail className="w-3 h-3" />{contact.email}</span>}
                            </div>
                        </div>
                    )
                })}
                {filteredContacts.length === 0 && <div className="flex flex-col items-center justify-center py-12 text-[#6B7280]"><Contact className="w-10 h-10 mb-3" /><p className="text-sm">Nessun contatto trovato</p></div>}
            </div>

            {/* Desktop table */}
            <div className="hidden sm:block rounded-2xl border border-[#1F1F1F] overflow-hidden bg-[#0A0A0A]">
                <div className="overflow-x-auto">
                    <table className="w-full min-w-[700px]">
                        <thead>
                            <tr className="border-b border-[#1F1F1F]">
                                <th className="text-left px-6 py-4 text-xs font-semibold text-[#6B7280] uppercase tracking-wider">Contatto</th>
                                <th className="text-left px-4 py-4 text-xs font-semibold text-[#6B7280] uppercase tracking-wider">Canali</th>
                                <th className="text-left px-4 py-4 text-xs font-semibold text-[#6B7280] uppercase tracking-wider">Status</th>
                                <th className="text-left px-4 py-4 text-xs font-semibold text-[#6B7280] uppercase tracking-wider cursor-pointer hover:text-white" onClick={() => toggleSort('lead_score')}>
                                    <span className="flex items-center gap-1">Score <SortIcon field="lead_score" /></span>
                                </th>
                                <th className="text-left px-4 py-4 text-xs font-semibold text-[#6B7280] uppercase tracking-wider cursor-pointer hover:text-white" onClick={() => toggleSort('updated_at')}>
                                    <span className="flex items-center gap-1">Aggiornato <SortIcon field="updated_at" /></span>
                                </th>
                                <th className="text-left px-4 py-4 text-xs font-semibold text-[#6B7280] uppercase tracking-wider">Azioni</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredContacts.map((contact) => {
                                const channels = getActiveChannels(contact)
                                const stColor = statusColors[contact.lead_status] || statusColors.new
                                return (
                                    <tr key={contact.id} className="border-b border-[#1F1F1F] hover:bg-[#1F1F1F]/30 transition-colors cursor-pointer" onClick={() => openContactDetail(contact)}>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-9 h-9 rounded-full bg-[#1F1F1F] flex items-center justify-center flex-shrink-0"><User className="w-4 h-4 text-[#6B7280]" /></div>
                                                <div>
                                                    <p className="text-sm font-medium text-white">{getContactName(contact)}</p>
                                                    <div className="flex items-center gap-3 text-xs text-[#6B7280] mt-0.5">
                                                        {contact.telefono && <span className="flex items-center gap-1"><Phone className="w-3 h-3" />{contact.telefono}</span>}
                                                        {contact.email && <span className="flex items-center gap-1"><Mail className="w-3 h-3" />{contact.email}</span>}
                                                    </div>
                                                    {contact.nome_attivita && <span className="text-xs text-[#6B7280] flex items-center gap-1 mt-0.5"><Store className="w-3 h-3" />{contact.nome_attivita}{contact.tipo_attivita && ` · ${contact.tipo_attivita}`}</span>}
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-4 py-4"><div className="flex items-center gap-1.5">{channels.map(ch => { const Icon = channelIcons[ch] || Globe; const color = channelColors[ch] || 'text-gray-400 bg-gray-500/10 border-gray-500/20'; return <span key={ch} className={`w-7 h-7 rounded-lg border flex items-center justify-center ${color}`}><Icon className="w-3.5 h-3.5" /></span> })}</div></td>
                                        <td className="px-4 py-4"><span className={`text-xs px-2.5 py-1 rounded-full border ${stColor}`}>{contact.lead_status}</span></td>
                                        <td className="px-4 py-4"><div className="flex items-center gap-2"><div className="w-16 h-1.5 bg-[#1F1F1F] rounded-full overflow-hidden"><div className="h-full bg-[#F90100] rounded-full" style={{ width: `${Math.min(contact.lead_score * 10, 100)}%` }} /></div><span className="text-xs text-[#9CA3AF]">{contact.lead_score}</span></div></td>
                                        <td className="px-4 py-4"><span className="text-xs text-[#6B7280]">{new Date(contact.updated_at).toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' })}</span></td>
                                        <td className="px-4 py-4"><button onClick={(e) => { e.stopPropagation(); openContactDetail(contact) }} className="text-xs text-[#F90100] hover:underline">Dettagli</button></td>
                                    </tr>
                                )
                            })}
                        </tbody>
                    </table>
                </div>
                {filteredContacts.length === 0 && <div className="flex flex-col items-center justify-center py-16 text-[#6B7280]"><Contact className="w-10 h-10 mb-3" /><p className="text-sm">Nessun contatto</p></div>}
            </div>

            {/* Modale dettaglio */}
            {selectedContact && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-end sm:items-center justify-center" onClick={() => setSelectedContact(null)}>
                    <div className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-t-2xl sm:rounded-2xl w-full sm:max-w-2xl max-h-[90vh] sm:max-h-[85vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-between p-4 sm:p-6 border-b border-[#1F1F1F] sticky top-0 bg-[#0A0A0A] z-10">
                            <div className="flex items-center gap-3 min-w-0">
                                <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-[#1F1F1F] flex items-center justify-center flex-shrink-0"><User className="w-5 h-5 sm:w-6 sm:h-6 text-[#6B7280]" /></div>
                                <div className="min-w-0">
                                    <h2 className="text-base sm:text-lg font-bold text-white truncate">{getContactName(selectedContact)}</h2>
                                    <p className="text-[10px] sm:text-xs text-[#6B7280]">{selectedContact.canale_primo_contatto} · {new Date(selectedContact.created_at).toLocaleDateString('it-IT')}</p>
                                </div>
                            </div>
                            <button onClick={() => setSelectedContact(null)} className="text-[#6B7280] hover:text-white p-1"><X className="w-5 h-5" /></button>
                        </div>
                        <div className="p-4 sm:p-6 space-y-4 sm:space-y-6">
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                {selectedContact.telefono && <div className="bg-[#1F1F1F] rounded-xl p-3 flex items-center gap-3"><Phone className="w-4 h-4 text-[#F90100] flex-shrink-0" /><div><p className="text-[10px] text-[#6B7280] uppercase">Telefono</p><p className="text-sm text-white">{selectedContact.telefono}</p></div></div>}
                                {selectedContact.email && <div className="bg-[#1F1F1F] rounded-xl p-3 flex items-center gap-3"><Mail className="w-4 h-4 text-[#F90100] flex-shrink-0" /><div className="min-w-0"><p className="text-[10px] text-[#6B7280] uppercase">Email</p><p className="text-sm text-white truncate">{selectedContact.email}</p></div></div>}
                                {selectedContact.nome_attivita && <div className="bg-[#1F1F1F] rounded-xl p-3 flex items-center gap-3"><Store className="w-4 h-4 text-[#F90100] flex-shrink-0" /><div><p className="text-[10px] text-[#6B7280] uppercase">Attività</p><p className="text-sm text-white">{selectedContact.nome_attivita}</p></div></div>}
                                {selectedContact.indirizzo && <div className="bg-[#1F1F1F] rounded-xl p-3 flex items-center gap-3"><MapPin className="w-4 h-4 text-[#F90100] flex-shrink-0" /><div><p className="text-[10px] text-[#6B7280] uppercase">Indirizzo</p><p className="text-sm text-white">{selectedContact.indirizzo}</p></div></div>}
                            </div>
                            {selectedContact.tags && selectedContact.tags.length > 0 && (
                                <div><p className="text-xs font-semibold text-[#6B7280] uppercase tracking-wider mb-2">Tags</p><div className="flex flex-wrap gap-2">{selectedContact.tags.map(tag => <span key={tag} className="text-xs px-2.5 py-1 rounded-full bg-[#F90100]/10 text-[#F90100] border border-[#F90100]/20 flex items-center gap-1"><Tag className="w-3 h-3" />{tag}</span>)}</div></div>
                            )}
                            {selectedContact.note && <div><p className="text-xs font-semibold text-[#6B7280] uppercase tracking-wider mb-2">Note</p><p className="text-sm text-[#9CA3AF] bg-[#1F1F1F] rounded-xl p-3">{selectedContact.note}</p></div>}
                            {loadingDetail ? <div className="flex items-center justify-center py-8"><Loader className="w-6 h-6 text-[#F90100] animate-spin" /></div> : (
                                <>
                                    <div>
                                        <p className="text-xs font-semibold text-[#6B7280] uppercase tracking-wider mb-3 flex items-center gap-2"><MessageSquare className="w-4 h-4" />Conversazioni ({contactConversations.length})</p>
                                        {contactConversations.length === 0 ? <p className="text-sm text-[#6B7280]">Nessuna</p> : (
                                            <div className="space-y-2">{contactConversations.map(conv => {
                                                const Icon = channelIcons[conv.channel_type] || MessageSquare
                                                return <Link key={conv.id} href={`/inbox?conv=${conv.id}`} className="flex items-center gap-3 bg-[#1F1F1F] rounded-xl p-3 hover:bg-[#2D2D2D] transition-colors">
                                                    <Icon className={`w-4 h-4 flex-shrink-0 ${channelColors[conv.channel_type]?.split(' ')[0] || 'text-gray-400'}`} />
                                                    <div className="flex-1 min-w-0"><p className="text-sm text-white truncate">{conv.last_message_preview || 'Nessun messaggio'}</p><p className="text-[10px] text-[#6B7280]">{conv.total_messages} msg · {conv.channel_type}</p></div>
                                                    <ExternalLink className="w-4 h-4 text-[#6B7280] flex-shrink-0" />
                                                </Link>
                                            })}</div>
                                        )}
                                    </div>
                                    <div>
                                        <p className="text-xs font-semibold text-[#6B7280] uppercase tracking-wider mb-3 flex items-center gap-2"><CalendarDays className="w-4 h-4" />Appuntamenti ({contactAppointments.length})</p>
                                        {contactAppointments.length === 0 ? <p className="text-sm text-[#6B7280]">Nessuno</p> : (
                                            <div className="space-y-2">{contactAppointments.map(appt => (
                                                <div key={appt.id} className="bg-[#1F1F1F] rounded-xl p-3">
                                                    <div className="flex items-center justify-between"><p className="text-sm font-medium text-white">{appt.titolo}</p><span className={`text-[10px] px-2 py-0.5 rounded-full border ${appt.stato === 'confermato' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : appt.stato === 'cancellato' ? 'bg-red-500/10 text-red-400 border-red-500/20' : 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'}`}>{appt.stato}</span></div>
                                                    <div className="flex flex-wrap items-center gap-2 sm:gap-3 mt-1.5 text-[10px] sm:text-xs text-[#6B7280]">
                                                        <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{new Date(appt.data_ora).toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' })}</span>
                                                        <span>{appt.durata_minuti} min</span><span className="capitalize">{appt.modalita}</span>
                                                    </div>
                                                    {appt.meet_link && <a href={appt.meet_link} target="_blank" rel="noopener noreferrer" className="text-xs text-[#F90100] hover:underline mt-1.5 inline-flex items-center gap-1"><ExternalLink className="w-3 h-3" />Meet</a>}
                                                </div>
                                            ))}</div>
                                        )}
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
