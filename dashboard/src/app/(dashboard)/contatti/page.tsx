'use client'

import { useEffect, useState } from 'react'
import { supabase, AgentContact, Conversation, Appointment } from '@/lib/supabase'
import {
    Contact,
    Search,
    Phone,
    Mail,
    MapPin,
    Store,
    Loader,
    X,
    MessageSquare,
    CalendarDays,
    Smartphone,
    Send,
    MessageCircle,
    AtSign,
    Globe,
    Tag,
    Clock,
    ChevronDown,
    ChevronUp,
    ExternalLink,
    User
} from 'lucide-react'
import Link from 'next/link'

const channelIcons: Record<string, any> = {
    whatsapp: Smartphone,
    telegram: Send,
    messenger: MessageCircle,
    instagram: AtSign,
    email: Mail,
    chatbot: Globe,
}

const channelColors: Record<string, string> = {
    whatsapp: 'text-green-400 bg-green-500/10 border-green-500/20',
    telegram: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
    messenger: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
    instagram: 'text-pink-400 bg-pink-500/10 border-pink-500/20',
    email: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
    chatbot: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
}

const statusColors: Record<string, string> = {
    new: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    contacted: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    qualified: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    converted: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
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

    useEffect(() => {
        fetchContacts()
        const interval = setInterval(fetchContacts, 30000)
        return () => clearInterval(interval)
    }, [])

    const fetchContacts = async () => {
        try {
            const { data, error } = await supabase
                .from('contacts')
                .select('*')
                .order('updated_at', { ascending: false })

            if (data && !error) {
                setContacts(data)
            }
        } catch (err) {
            console.error('Errore fetch contatti:', err)
        } finally {
            setLoading(false)
        }
    }

    const openContactDetail = async (contact: AgentContact) => {
        setSelectedContact(contact)
        setLoadingDetail(true)
        try {
            const [convRes, apptRes] = await Promise.all([
                supabase
                    .from('conversations')
                    .select('*')
                    .eq('contact_id', contact.id)
                    .order('last_message_at', { ascending: false }),
                supabase
                    .from('appointments')
                    .select('*')
                    .eq('contact_id', contact.id)
                    .is('deleted_at', null)
                    .order('data_ora', { ascending: false })
            ])

            if (convRes.data) setContactConversations(convRes.data)
            if (apptRes.data) setContactAppointments(apptRes.data)
        } catch (err) {
            console.error('Errore fetch dettaglio contatto:', err)
        } finally {
            setLoadingDetail(false)
        }
    }

    const getContactName = (c: AgentContact) => {
        return c.nome || c.nome_attivita || c.email || c.telefono || 'Sconosciuto'
    }

    const getActiveChannels = (c: AgentContact) => {
        const channels: string[] = []
        if (c.whatsapp_id) channels.push('whatsapp')
        if (c.telegram_id) channels.push('telegram')
        if (c.messenger_id) channels.push('messenger')
        if (c.instagram_id) channels.push('instagram')
        if (c.email_channel_id) channels.push('email')
        if (c.chatbot_session) channels.push('chatbot')
        return channels
    }

    const filteredContacts = contacts
        .filter(c => {
            const name = getContactName(c).toLowerCase()
            const email = (c.email || '').toLowerCase()
            const phone = (c.telefono || '').toLowerCase()
            const attivita = (c.nome_attivita || '').toLowerCase()
            const matchesSearch = searchQuery === '' ||
                name.includes(searchQuery.toLowerCase()) ||
                email.includes(searchQuery.toLowerCase()) ||
                phone.includes(searchQuery.toLowerCase()) ||
                attivita.includes(searchQuery.toLowerCase())
            const matchesChannel = filterChannel === 'all' || c.canale_primo_contatto === filterChannel
            const matchesStatus = filterStatus === 'all' || c.lead_status === filterStatus
            return matchesSearch && matchesChannel && matchesStatus
        })
        .sort((a, b) => {
            const aVal = a[sortField]
            const bVal = b[sortField]
            if (typeof aVal === 'number' && typeof bVal === 'number') {
                return sortAsc ? aVal - bVal : bVal - aVal
            }
            return sortAsc
                ? String(aVal || '').localeCompare(String(bVal || ''))
                : String(bVal || '').localeCompare(String(aVal || ''))
        })

    const toggleSort = (field: typeof sortField) => {
        if (sortField === field) {
            setSortAsc(!sortAsc)
        } else {
            setSortField(field)
            setSortAsc(false)
        }
    }

    const SortIcon = ({ field }: { field: typeof sortField }) => {
        if (sortField !== field) return null
        return sortAsc ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center h-[80vh]">
                <Loader className="w-8 h-8 text-[#F90100] animate-spin" />
            </div>
        )
    }

    return (
        <div>
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-white">Contatti Agent</h1>
                <p className="text-sm text-[#6B7280] mt-1">{contacts.length} contatti totali</p>
            </div>

            {/* Filtri */}
            <div className="flex flex-wrap gap-3 mb-6">
                <div className="relative flex-1 min-w-[250px]">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7280]" />
                    <input
                        type="text"
                        placeholder="Cerca per nome, email, telefono, attività..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-[#6B7280] focus:outline-none focus:border-[#F90100]/50"
                    />
                </div>
                <select
                    value={filterChannel}
                    onChange={(e) => setFilterChannel(e.target.value)}
                    className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-[#F90100]/50"
                >
                    <option value="all">Tutti i canali</option>
                    <option value="whatsapp">WhatsApp</option>
                    <option value="telegram">Telegram</option>
                    <option value="messenger">Messenger</option>
                    <option value="instagram">Instagram</option>
                    <option value="email">Email</option>
                    <option value="chatbot">Chatbot</option>
                </select>
                <select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value)}
                    className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-[#F90100]/50"
                >
                    <option value="all">Tutti gli stati</option>
                    <option value="new">Nuovo</option>
                    <option value="contacted">Contattato</option>
                    <option value="qualified">Qualificato</option>
                    <option value="converted">Convertito</option>
                    <option value="lost">Perso</option>
                </select>
            </div>

            {/* Tabella */}
            <div className="rounded-2xl border border-[#1F1F1F] overflow-hidden bg-[#0A0A0A]">
                <table className="w-full">
                    <thead>
                        <tr className="border-b border-[#1F1F1F]">
                            <th className="text-left px-6 py-4 text-xs font-semibold text-[#6B7280] uppercase tracking-wider">Contatto</th>
                            <th className="text-left px-4 py-4 text-xs font-semibold text-[#6B7280] uppercase tracking-wider">Canali</th>
                            <th className="text-left px-4 py-4 text-xs font-semibold text-[#6B7280] uppercase tracking-wider">Status</th>
                            <th
                                className="text-left px-4 py-4 text-xs font-semibold text-[#6B7280] uppercase tracking-wider cursor-pointer hover:text-white flex items-center gap-1"
                                onClick={() => toggleSort('lead_score')}
                            >
                                Score <SortIcon field="lead_score" />
                            </th>
                            <th
                                className="text-left px-4 py-4 text-xs font-semibold text-[#6B7280] uppercase tracking-wider cursor-pointer hover:text-white"
                                onClick={() => toggleSort('updated_at')}
                            >
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
                                <tr
                                    key={contact.id}
                                    className="border-b border-[#1F1F1F] hover:bg-[#1F1F1F]/30 transition-colors cursor-pointer"
                                    onClick={() => openContactDetail(contact)}
                                >
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-3">
                                            <div className="w-9 h-9 rounded-full bg-[#1F1F1F] flex items-center justify-center flex-shrink-0">
                                                <User className="w-4 h-4 text-[#6B7280]" />
                                            </div>
                                            <div>
                                                <p className="text-sm font-medium text-white">{getContactName(contact)}</p>
                                                <div className="flex items-center gap-3 text-xs text-[#6B7280] mt-0.5">
                                                    {contact.telefono && (
                                                        <span className="flex items-center gap-1">
                                                            <Phone className="w-3 h-3" />{contact.telefono}
                                                        </span>
                                                    )}
                                                    {contact.email && (
                                                        <span className="flex items-center gap-1">
                                                            <Mail className="w-3 h-3" />{contact.email}
                                                        </span>
                                                    )}
                                                </div>
                                                {contact.nome_attivita && (
                                                    <span className="text-xs text-[#6B7280] flex items-center gap-1 mt-0.5">
                                                        <Store className="w-3 h-3" />{contact.nome_attivita}
                                                        {contact.tipo_attivita && ` · ${contact.tipo_attivita}`}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-4 py-4">
                                        <div className="flex items-center gap-1.5">
                                            {channels.map(ch => {
                                                const Icon = channelIcons[ch] || Globe
                                                const color = channelColors[ch] || 'text-gray-400 bg-gray-500/10 border-gray-500/20'
                                                return (
                                                    <span key={ch} className={`w-7 h-7 rounded-lg border flex items-center justify-center ${color}`}>
                                                        <Icon className="w-3.5 h-3.5" />
                                                    </span>
                                                )
                                            })}
                                        </div>
                                    </td>
                                    <td className="px-4 py-4">
                                        <span className={`text-xs px-2.5 py-1 rounded-full border ${stColor}`}>
                                            {contact.lead_status}
                                        </span>
                                    </td>
                                    <td className="px-4 py-4">
                                        <div className="flex items-center gap-2">
                                            <div className="w-16 h-1.5 bg-[#1F1F1F] rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-[#F90100] rounded-full"
                                                    style={{ width: `${Math.min(contact.lead_score * 10, 100)}%` }}
                                                />
                                            </div>
                                            <span className="text-xs text-[#9CA3AF]">{contact.lead_score}</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-4">
                                        <span className="text-xs text-[#6B7280]">
                                            {new Date(contact.updated_at).toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' })}
                                        </span>
                                    </td>
                                    <td className="px-4 py-4">
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation()
                                                openContactDetail(contact)
                                            }}
                                            className="text-xs text-[#F90100] hover:underline"
                                        >
                                            Dettagli
                                        </button>
                                    </td>
                                </tr>
                            )
                        })}
                    </tbody>
                </table>

                {filteredContacts.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-16 text-[#6B7280]">
                        <Contact className="w-10 h-10 mb-3" />
                        <p className="text-sm">Nessun contatto trovato</p>
                    </div>
                )}
            </div>

            {/* Modale dettaglio contatto */}
            {selectedContact && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setSelectedContact(null)}>
                    <div className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-2xl w-full max-w-2xl max-h-[85vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
                        {/* Header modale */}
                        <div className="flex items-center justify-between p-6 border-b border-[#1F1F1F]">
                            <div className="flex items-center gap-3">
                                <div className="w-12 h-12 rounded-full bg-[#1F1F1F] flex items-center justify-center">
                                    <User className="w-6 h-6 text-[#6B7280]" />
                                </div>
                                <div>
                                    <h2 className="text-lg font-bold text-white">{getContactName(selectedContact)}</h2>
                                    <p className="text-xs text-[#6B7280]">
                                        Primo contatto: {selectedContact.canale_primo_contatto} · {new Date(selectedContact.created_at).toLocaleDateString('it-IT')}
                                    </p>
                                </div>
                            </div>
                            <button onClick={() => setSelectedContact(null)} className="text-[#6B7280] hover:text-white">
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="p-6 space-y-6">
                            {/* Info contatto */}
                            <div className="grid grid-cols-2 gap-4">
                                {selectedContact.telefono && (
                                    <div className="bg-[#1F1F1F] rounded-xl p-3 flex items-center gap-3">
                                        <Phone className="w-4 h-4 text-[#F90100]" />
                                        <div>
                                            <p className="text-[10px] text-[#6B7280] uppercase">Telefono</p>
                                            <p className="text-sm text-white">{selectedContact.telefono}</p>
                                        </div>
                                    </div>
                                )}
                                {selectedContact.email && (
                                    <div className="bg-[#1F1F1F] rounded-xl p-3 flex items-center gap-3">
                                        <Mail className="w-4 h-4 text-[#F90100]" />
                                        <div>
                                            <p className="text-[10px] text-[#6B7280] uppercase">Email</p>
                                            <p className="text-sm text-white">{selectedContact.email}</p>
                                        </div>
                                    </div>
                                )}
                                {selectedContact.nome_attivita && (
                                    <div className="bg-[#1F1F1F] rounded-xl p-3 flex items-center gap-3">
                                        <Store className="w-4 h-4 text-[#F90100]" />
                                        <div>
                                            <p className="text-[10px] text-[#6B7280] uppercase">Attività</p>
                                            <p className="text-sm text-white">{selectedContact.nome_attivita}</p>
                                        </div>
                                    </div>
                                )}
                                {selectedContact.indirizzo && (
                                    <div className="bg-[#1F1F1F] rounded-xl p-3 flex items-center gap-3">
                                        <MapPin className="w-4 h-4 text-[#F90100]" />
                                        <div>
                                            <p className="text-[10px] text-[#6B7280] uppercase">Indirizzo</p>
                                            <p className="text-sm text-white">{selectedContact.indirizzo}</p>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Tags */}
                            {selectedContact.tags && selectedContact.tags.length > 0 && (
                                <div>
                                    <p className="text-xs font-semibold text-[#6B7280] uppercase tracking-wider mb-2">Tags</p>
                                    <div className="flex flex-wrap gap-2">
                                        {selectedContact.tags.map(tag => (
                                            <span key={tag} className="text-xs px-2.5 py-1 rounded-full bg-[#F90100]/10 text-[#F90100] border border-[#F90100]/20 flex items-center gap-1">
                                                <Tag className="w-3 h-3" />{tag}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Note */}
                            {selectedContact.note && (
                                <div>
                                    <p className="text-xs font-semibold text-[#6B7280] uppercase tracking-wider mb-2">Note</p>
                                    <p className="text-sm text-[#9CA3AF] bg-[#1F1F1F] rounded-xl p-3">{selectedContact.note}</p>
                                </div>
                            )}

                            {loadingDetail ? (
                                <div className="flex items-center justify-center py-8">
                                    <Loader className="w-6 h-6 text-[#F90100] animate-spin" />
                                </div>
                            ) : (
                                <>
                                    {/* Conversazioni */}
                                    <div>
                                        <p className="text-xs font-semibold text-[#6B7280] uppercase tracking-wider mb-3 flex items-center gap-2">
                                            <MessageSquare className="w-4 h-4" />
                                            Conversazioni ({contactConversations.length})
                                        </p>
                                        {contactConversations.length === 0 ? (
                                            <p className="text-sm text-[#6B7280]">Nessuna conversazione</p>
                                        ) : (
                                            <div className="space-y-2">
                                                {contactConversations.map(conv => {
                                                    const Icon = channelIcons[conv.channel_type] || MessageSquare
                                                    return (
                                                        <Link
                                                            key={conv.id}
                                                            href={`/inbox?conv=${conv.id}`}
                                                            className="flex items-center gap-3 bg-[#1F1F1F] rounded-xl p-3 hover:bg-[#2D2D2D] transition-colors"
                                                        >
                                                            <Icon className={`w-4 h-4 ${channelColors[conv.channel_type]?.split(' ')[0] || 'text-gray-400'}`} />
                                                            <div className="flex-1 min-w-0">
                                                                <p className="text-sm text-white truncate">{conv.last_message_preview || 'Nessun messaggio'}</p>
                                                                <p className="text-[10px] text-[#6B7280]">{conv.total_messages} messaggi · {conv.channel_type}</p>
                                                            </div>
                                                            <ExternalLink className="w-4 h-4 text-[#6B7280]" />
                                                        </Link>
                                                    )
                                                })}
                                            </div>
                                        )}
                                    </div>

                                    {/* Appuntamenti */}
                                    <div>
                                        <p className="text-xs font-semibold text-[#6B7280] uppercase tracking-wider mb-3 flex items-center gap-2">
                                            <CalendarDays className="w-4 h-4" />
                                            Appuntamenti ({contactAppointments.length})
                                        </p>
                                        {contactAppointments.length === 0 ? (
                                            <p className="text-sm text-[#6B7280]">Nessun appuntamento</p>
                                        ) : (
                                            <div className="space-y-2">
                                                {contactAppointments.map(appt => (
                                                    <div key={appt.id} className="bg-[#1F1F1F] rounded-xl p-3">
                                                        <div className="flex items-center justify-between">
                                                            <p className="text-sm font-medium text-white">{appt.titolo}</p>
                                                            <span className={`text-[10px] px-2 py-0.5 rounded-full border ${appt.stato === 'confermato'
                                                                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                                                                : appt.stato === 'cancellato'
                                                                    ? 'bg-red-500/10 text-red-400 border-red-500/20'
                                                                    : 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
                                                                }`}>
                                                                {appt.stato}
                                                            </span>
                                                        </div>
                                                        <div className="flex items-center gap-3 mt-1.5 text-xs text-[#6B7280]">
                                                            <span className="flex items-center gap-1">
                                                                <Clock className="w-3 h-3" />
                                                                {new Date(appt.data_ora).toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' })}
                                                            </span>
                                                            <span>{appt.durata_minuti} min</span>
                                                            <span className="capitalize">{appt.modalita}</span>
                                                        </div>
                                                        {appt.meet_link && (
                                                            <a href={appt.meet_link} target="_blank" rel="noopener noreferrer" className="text-xs text-[#F90100] hover:underline mt-1.5 inline-flex items-center gap-1">
                                                                <ExternalLink className="w-3 h-3" />Google Meet
                                                            </a>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
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
