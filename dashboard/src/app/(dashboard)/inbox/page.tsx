'use client'

import { useEffect, useState, useRef } from 'react'
import { supabase, Conversation, Message, AgentContact } from '@/lib/supabase'
import {
    MessageSquare,
    Send,
    Bot,
    User,
    UserCog,
    Phone,
    Mail,
    Search,
    ChevronLeft,
    Loader,
    AlertCircle,
    MessageCircle,
    Hash,
    Smartphone,
    Globe,
    AtSign,
    Paperclip,
    Mic,
    FileText,
    Download,
    Image
} from 'lucide-react'

const channelIcons: Record<string, any> = {
    whatsapp: Smartphone,
    telegram: Send,
    messenger: MessageCircle,
    instagram: AtSign,
    email: Mail,
    chatbot: Globe,
}

const channelColors: Record<string, string> = {
    whatsapp: 'text-green-400',
    telegram: 'text-blue-400',
    messenger: 'text-purple-400',
    instagram: 'text-pink-400',
    email: 'text-yellow-400',
    chatbot: 'text-cyan-400',
}

const statusLabels: Record<string, { label: string; color: string }> = {
    ai: { label: 'AI Attiva', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' },
    human: { label: 'Operatore', color: 'bg-orange-500/10 text-orange-400 border-orange-500/30' },
    closed: { label: 'Chiusa', color: 'bg-gray-500/10 text-gray-400 border-gray-500/30' },
}

export default function InboxPage() {
    const [conversations, setConversations] = useState<(Conversation & { contact: AgentContact })[]>([])
    const [selectedConv, setSelectedConv] = useState<string | null>(null)
    const [messages, setMessages] = useState<Message[]>([])
    const [loading, setLoading] = useState(true)
    const [loadingMessages, setLoadingMessages] = useState(false)
    const [newMessage, setNewMessage] = useState('')
    const [uploadFile, setUploadFile] = useState<File | null>(null)
    const fileInputRef = useRef<HTMLInputElement>(null)
    const [sending, setSending] = useState(false)
    const [searchQuery, setSearchQuery] = useState('')
    const [filterChannel, setFilterChannel] = useState<string>('all')
    const [filterStatus, setFilterStatus] = useState<string>('all')
    const [mobileShowChat, setMobileShowChat] = useState(false)
    const messagesEndRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        const params = new URLSearchParams(window.location.search)
        const convId = params.get("conv")
        if (convId && conversations.length > 0 && !selectedConv) {
            setSelectedConv(convId)
        }
    }, [conversations])

    const inputRef = useRef<HTMLTextAreaElement>(null)

    useEffect(() => {
        fetchConversations()
        const interval = setInterval(fetchConversations, 10000)
        return () => clearInterval(interval)
    }, [])

    useEffect(() => {
        if (selectedConv) {
            fetchMessages(selectedConv)
            markAsRead(selectedConv)
            const interval = setInterval(() => fetchMessages(selectedConv), 5000)
            return () => clearInterval(interval)
        }
    }, [selectedConv])

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    const fetchConversations = async () => {
        try {
            const { data, error } = await supabase
                .from('conversations')
                .select('*, contact:contacts(*)')
                .order('last_message_at', { ascending: false })

            if (data && !error) {
                setConversations(data as any)
            }
        } catch (err) {
            console.error('Errore fetch conversazioni:', err)
        } finally {
            setLoading(false)
        }
    }

    const fetchMessages = async (convId: string) => {
        setLoadingMessages(true)
        try {
            const { data, error } = await supabase
                .from('messages')
                .select('*')
                .eq('conversation_id', convId)
                .order('created_at', { ascending: true })

            if (data && !error) {
                setMessages(data)
            }
        } catch (err) {
            console.error('Errore fetch messaggi:', err)
        } finally {
            setLoadingMessages(false)
        }
    }

    const markAsRead = async (convId: string) => {
        await supabase
            .from('messages')
            .update({ read: true })
            .eq('conversation_id', convId)
            .eq('direction', 'inbound')
            .eq('read', false)

        await supabase
            .from('conversations')
            .update({ unread_count: 0 })
            .eq('id', convId)
    }

    const toggleAI = async (convId: string, currentStatus: boolean) => {
        const newStatus = !currentStatus
        await supabase
            .from('conversations')
            .update({
                ai_enabled: newStatus,
                status: newStatus ? 'ai' : 'human'
            })
            .eq('id', convId)
        fetchConversations()
    }

    const sendManualMessage = async () => {
        if ((!newMessage.trim() && !uploadFile) || !selectedConv || sending) return

        const conv = conversations.find(c => c.id === selectedConv)
        if (!conv) return

        setSending(true)
        try {
            // Se c'e' un file, usa l'endpoint upload
            if (uploadFile) {
                const formData = new FormData()
                formData.append('file', uploadFile)
                if (newMessage.trim()) formData.append('caption', newMessage.trim())
                
                const res = await fetch('https://agent.digidentityagency.it/api/agent/conversations/' + selectedConv + '/upload', {
                    method: 'POST',
                    body: formData
                })
                
                if (!res.ok) {
                    console.warn('Upload fallito')
                }
            } else {
                // Invio testo normale
                // Salva il messaggio in Supabase
                const { error: msgError } = await supabase
                    .from('messages')
                    .insert({
                        conversation_id: selectedConv,
                        contact_id: conv.contact_id,
                        direction: 'outbound',
                        sender_type: 'operator',
                        sender_name: 'Stefano',
                        content: newMessage.trim(),
                        content_type: 'text',
                        channel_type: conv.channel_type,
                        delivered: false,
                        read: false,
                        metadata: {}
                    })

                if (msgError) throw msgError

                // Invia tramite API agent
                const res = await fetch('https://agent.digidentityagency.it/api/agent/conversations/' + selectedConv + '/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        content: newMessage.trim(),
                        sender_name: 'Stefano'
                    })
                })

                if (!res.ok) {
                    console.warn('Invio canale fallito, messaggio salvato in DB')
                }
            }

            // Aggiorna conversazione
            await supabase
                .from('conversations')
                .update({
                    last_message_at: new Date().toISOString(),
                    last_message_preview: uploadFile ? (uploadFile.name || 'File') : newMessage.trim().substring(0, 100),
                    total_messages: conv.total_messages + 1
                })
                .eq('id', selectedConv)

            setNewMessage('')
            setUploadFile(null)
            fetchMessages(selectedConv)
            fetchConversations()
        } catch (err) {
            console.error('Errore invio messaggio:', err)
        } finally {
            setSending(false)
            inputRef.current?.focus()
        }
    }

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            sendManualMessage()
        }
    }

    const getContactName = (contact: AgentContact | undefined) => {
        if (!contact) return 'Sconosciuto'
        return contact.nome || contact.nome_attivita || contact.email || contact.telefono || 'Sconosciuto'
    }

    const formatTime = (dateStr: string) => {
        const date = new Date(dateStr)
        const now = new Date()
        const diff = now.getTime() - date.getTime()
        const days = Math.floor(diff / (1000 * 60 * 60 * 24))

        if (days === 0) {
            return date.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
        } else if (days === 1) {
            return 'Ieri'
        } else if (days < 7) {
            return date.toLocaleDateString('it-IT', { weekday: 'short' })
        }
        return date.toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit' })
    }

    const formatMessageTime = (dateStr: string) => {
        return new Date(dateStr).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
    }

    const filteredConversations = conversations.filter(conv => {
        const name = getContactName(conv.contact).toLowerCase()
        const preview = (conv.last_message_preview || '').toLowerCase()
        const matchesSearch = searchQuery === '' || name.includes(searchQuery.toLowerCase()) || preview.includes(searchQuery.toLowerCase())
        const matchesChannel = filterChannel === 'all' || conv.channel_type === filterChannel
        const matchesStatus = filterStatus === 'all' || conv.status === filterStatus
        return matchesSearch && matchesChannel && matchesStatus
    })

    const selectedConversation = conversations.find(c => c.id === selectedConv)
    const ChannelIcon = selectedConversation ? (channelIcons[selectedConversation.channel_type] || MessageSquare) : MessageSquare

    if (loading) {
        return (
            <div className="flex items-center justify-center h-[80vh]">
                <Loader className="w-8 h-8 text-[#F90100] animate-spin" />
            </div>
        )
    }

    return (
        <div className="h-[calc(100vh-4rem)]">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-white">Inbox</h1>
                <p className="text-sm text-[#6B7280] mt-1">Conversazioni in tempo reale — {conversations.length} totali, {conversations.filter(c => c.unread_count > 0).length} da leggere</p>
            </div>

            <div className="flex h-[calc(100vh-10rem)] rounded-2xl border border-[#1F1F1F] overflow-hidden bg-[#0A0A0A]">
                {/* Lista conversazioni */}
                <div className={`w-96 border-r border-[#1F1F1F] flex flex-col ${mobileShowChat ? 'hidden lg:flex' : 'flex'}`}>
                    {/* Filtri */}
                    <div className="p-4 border-b border-[#1F1F1F] space-y-3">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7280]" />
                            <input
                                type="text"
                                placeholder="Cerca conversazione..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full bg-[#1F1F1F] border border-[#2D2D2D] rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-[#6B7280] focus:outline-none focus:border-[#F90100]/50"
                            />
                        </div>
                        <div className="flex gap-2">
                            <select
                                value={filterChannel}
                                onChange={(e) => setFilterChannel(e.target.value)}
                                className="flex-1 bg-[#1F1F1F] border border-[#2D2D2D] rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-[#F90100]/50"
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
                                className="flex-1 bg-[#1F1F1F] border border-[#2D2D2D] rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-[#F90100]/50"
                            >
                                <option value="all">Tutti gli stati</option>
                                <option value="ai">AI Attiva</option>
                                <option value="human">Operatore</option>
                                <option value="closed">Chiuse</option>
                            </select>
                        </div>
                    </div>

                    {/* Lista */}
                    <div className="flex-1 overflow-y-auto">
                        {filteredConversations.length === 0 ? (
                            <div className="flex flex-col items-center justify-center h-full text-[#6B7280]">
                                <MessageSquare className="w-10 h-10 mb-3" />
                                <p className="text-sm">Nessuna conversazione</p>
                            </div>
                        ) : (
                            filteredConversations.map((conv) => {
                                const Icon = channelIcons[conv.channel_type] || MessageSquare
                                const colorClass = channelColors[conv.channel_type] || 'text-gray-400'
                                const isSelected = selectedConv === conv.id
                                const st = statusLabels[conv.status] || statusLabels.ai

                                return (
                                    <button
                                        key={conv.id}
                                        onClick={() => {
                                            setSelectedConv(conv.id)
                                            setMobileShowChat(true)
                                        }}
                                        className={`w-full px-4 py-4 flex items-start gap-3 border-b border-[#1F1F1F] transition-all duration-150 text-left ${isSelected
                                            ? 'bg-[#F90100]/5 border-l-2 border-l-[#F90100]'
                                            : 'hover:bg-[#1F1F1F]/50'
                                            }`}
                                    >
                                        <div className="relative flex-shrink-0">
                                            <div className="w-10 h-10 rounded-full bg-[#1F1F1F] flex items-center justify-center">
                                                <Icon className={`w-5 h-5 ${colorClass}`} />
                                            </div>
                                            {conv.unread_count > 0 && (
                                                <span className="absolute -top-1 -right-1 w-5 h-5 bg-[#F90100] rounded-full flex items-center justify-center text-[10px] font-bold text-white">
                                                    {conv.unread_count}
                                                </span>
                                            )}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center justify-between">
                                                <span className={`text-sm font-medium truncate ${conv.unread_count > 0 ? 'text-white' : 'text-[#9CA3AF]'}`}>
                                                    {getContactName(conv.contact)}
                                                </span>
                                                <span className="text-[10px] text-[#6B7280] flex-shrink-0 ml-2">
                                                    {formatTime(conv.last_message_at)}
                                                </span>
                                            </div>
                                            <p className={`text-xs truncate mt-0.5 ${conv.unread_count > 0 ? 'text-[#9CA3AF]' : 'text-[#6B7280]'}`}>
                                                {conv.last_message_preview || 'Nessun messaggio'}
                                            </p>
                                            <div className="flex items-center gap-2 mt-1.5">
                                                <span className={`text-[10px] px-2 py-0.5 rounded-full border ${st.color}`}>
                                                    {st.label}
                                                </span>
                                                <span className="text-[10px] text-[#6B7280]">
                                                    {conv.total_messages} msg
                                                </span>
                                            </div>
                                        </div>
                                    </button>
                                )
                            })
                        )}
                    </div>
                </div>

                {/* Area chat */}
                <div className={`flex-1 flex flex-col ${!mobileShowChat && !selectedConv ? 'hidden lg:flex' : 'flex'}`}>
                    {!selectedConv ? (
                        <div className="flex-1 flex flex-col items-center justify-center text-[#6B7280]">
                            <MessageSquare className="w-16 h-16 mb-4 text-[#2D2D2D]" />
                            <p className="text-lg font-medium text-[#9CA3AF]">Seleziona una conversazione</p>
                            <p className="text-sm mt-1">Scegli una chat dalla lista per visualizzare i messaggi</p>
                        </div>
                    ) : (
                        <>
                            {/* Header chat */}
                            <div className="px-6 py-4 border-b border-[#1F1F1F] flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <button
                                        onClick={() => {
                                            setMobileShowChat(false)
                                            setSelectedConv(null)
                                        }}
                                        className="lg:hidden text-[#9CA3AF] hover:text-white"
                                    >
                                        <ChevronLeft className="w-5 h-5" />
                                    </button>
                                    <div className="w-10 h-10 rounded-full bg-[#1F1F1F] flex items-center justify-center">
                                        <ChannelIcon className={`w-5 h-5 ${channelColors[selectedConversation?.channel_type || ''] || 'text-gray-400'}`} />
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium text-white">
                                            {getContactName(selectedConversation?.contact)}
                                        </p>
                                        <div className="flex items-center gap-2 text-xs text-[#6B7280]">
                                            <span className="capitalize">{selectedConversation?.channel_type}</span>
                                            {selectedConversation?.contact?.telefono && (
                                                <>
                                                    <span>·</span>
                                                    <Phone className="w-3 h-3" />
                                                    <span>{selectedConversation.contact.telefono}</span>
                                                </>
                                            )}
                                            {selectedConversation?.contact?.email && (
                                                <>
                                                    <span>·</span>
                                                    <Mail className="w-3 h-3" />
                                                    <span>{selectedConversation.contact.email}</span>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3">
                                    <span className={`text-xs px-3 py-1 rounded-full border ${statusLabels[selectedConversation?.status || 'ai']?.color}`}>
                                        {statusLabels[selectedConversation?.status || 'ai']?.label}
                                    </span>
                                    <button
                                        onClick={() => selectedConversation && toggleAI(selectedConversation.id, selectedConversation.ai_enabled)}
                                        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${selectedConversation?.ai_enabled
                                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 hover:bg-red-500/10 hover:text-red-400 hover:border-red-500/30'
                                            : 'bg-red-500/10 text-red-400 border border-red-500/30 hover:bg-emerald-500/10 hover:text-emerald-400 hover:border-emerald-500/30'
                                            }`}
                                    >
                                        <Bot className="w-3.5 h-3.5" />
                                        {selectedConversation?.ai_enabled ? 'AI ON — Clicca per disattivare' : 'AI OFF — Clicca per attivare'}
                                    </button>
                                </div>
                            </div>

                            {/* Messaggi */}
                            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
                                {loadingMessages && messages.length === 0 ? (
                                    <div className="flex items-center justify-center h-full">
                                        <Loader className="w-6 h-6 text-[#F90100] animate-spin" />
                                    </div>
                                ) : messages.length === 0 ? (
                                    <div className="flex flex-col items-center justify-center h-full text-[#6B7280]">
                                        <MessageSquare className="w-10 h-10 mb-3" />
                                        <p className="text-sm">Nessun messaggio</p>
                                    </div>
                                ) : (
                                    messages.map((msg) => {
                                        const isInbound = msg.direction === 'inbound'
                                        const isAI = msg.sender_type === 'ai'
                                        const isAgent = msg.sender_type === 'agent'

                                        return (
                                            <div
                                                key={msg.id}
                                                className={`flex ${isInbound ? 'justify-start' : 'justify-end'}`}
                                            >
                                                <div className={`max-w-[70%] ${isInbound
                                                    ? 'bg-[#1F1F1F] rounded-2xl rounded-tl-sm'
                                                    : isAI
                                                        ? 'bg-emerald-500/10 border border-emerald-500/20 rounded-2xl rounded-tr-sm'
                                                        : 'bg-[#F90100]/10 border border-[#F90100]/20 rounded-2xl rounded-tr-sm'
                                                    } px-4 py-3`}
                                                >
                                                    {!isInbound && (
                                                        <div className="flex items-center gap-1.5 mb-1">
                                                            {isAI ? (
                                                                <Bot className="w-3 h-3 text-emerald-400" />
                                                            ) : (
                                                                <UserCog className="w-3 h-3 text-[#F90100]" />
                                                            )}
                                                            <span className={`text-[10px] font-medium ${isAI ? 'text-emerald-400' : 'text-[#F90100]'}`}>
                                                                {isAI ? 'Digy AI' : msg.sender_name || 'Operatore'}
                                                            </span>
                                                        </div>
                                                    )}
                                                    {/* Media content */}
                                                    {msg.content_type === 'audio' && msg.media_url && (
                                                        <div className="mb-2">
                                                            <div className="flex items-center gap-2 text-[10px] text-[#6B7280] mb-1 italic">
                                                                <Mic className="w-3 h-3" />
                                                                Messaggio vocale
                                                            </div>
                                                            <audio controls className="w-full max-w-[280px] h-8" style={{ filter: 'invert(1) hue-rotate(180deg)' }}>
                                                                <source src={msg.media_url} />
                                                            </audio>
                                                        </div>
                                                    )}
                                                    {msg.content_type === 'audio' && !msg.media_url && msg.media_transcription && (
                                                        <div className="text-[10px] text-[#6B7280] mb-1 italic flex items-center gap-1">
                                                            <Mic className="w-3 h-3" />
                                                            Vocale trascritto
                                                        </div>
                                                    )}
                                                    {msg.content_type === 'image' && msg.media_url && (
                                                        <div className="mb-2">
                                                            <img src={msg.media_url} alt="Immagine" className="max-w-[280px] rounded-lg cursor-pointer hover:opacity-80 transition-opacity" onClick={() => window.open(msg.media_url ?? "", '_blank')} />
                                                        </div>
                                                    )}
                                                    {msg.content_type === 'document' && msg.media_url && (
                                                        <a href={msg.media_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 bg-[#2D2D2D] rounded-lg px-3 py-2 mb-2 hover:bg-[#3D3D3D] transition-colors">
                                                            <FileText className="w-5 h-5 text-blue-400" />
                                                            <div className="flex-1 min-w-0">
                                                                <p className="text-xs text-white truncate">Documento</p>
                                                                <p className="text-[10px] text-[#6B7280]">Clicca per aprire</p>
                                                            </div>
                                                            <Download className="w-4 h-4 text-[#6B7280]" />
                                                        </a>
                                                    )}
                                                    <p className="text-sm text-white whitespace-pre-wrap break-words">
                                                        {msg.media_transcription || msg.content}
                                                    </p>
                                                    <div className="flex items-center justify-end gap-2 mt-1.5">
                                                        <span className="text-[10px] text-[#6B7280]">
                                                            {formatMessageTime(msg.created_at)}
                                                        </span>
                                                        {msg.ai_tokens_used && (
                                                            <span className="text-[10px] text-[#6B7280]">
                                                                {msg.ai_tokens_used} tok
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        )
                                    })
                                )}
                                <div ref={messagesEndRef} />
                            </div>

                            {/* Input messaggio */}
                            <div className="px-6 py-4 border-t border-[#1F1F1F]">
                                {selectedConversation?.ai_enabled ? (
                                    <div className="flex items-center gap-3 text-[#6B7280] bg-[#1F1F1F] rounded-xl px-4 py-3">
                                        <Bot className="w-5 h-5 text-emerald-400" />
                                        <p className="text-sm">AI attiva — Disattiva l&apos;AI per rispondere manualmente</p>
                                    </div>
                                ) : (
                                    <div className="flex flex-col gap-2">
                                        {/* File preview */}
                                        {uploadFile && (
                                            <div className="flex items-center gap-2 bg-[#1F1F1F] rounded-lg px-3 py-2">
                                                <FileText className="w-4 h-4 text-blue-400" />
                                                <span className="text-xs text-white truncate flex-1">{uploadFile.name}</span>
                                                <span className="text-[10px] text-[#6B7280]">{(uploadFile.size / 1024).toFixed(0)} KB</span>
                                                <button onClick={() => setUploadFile(null)} className="text-[#6B7280] hover:text-red-400 text-xs">✕</button>
                                            </div>
                                        )}
                                        <div className="flex items-end gap-2">
                                        <input
                                            type="file"
                                            ref={fileInputRef}
                                            className="hidden"
                                            accept="image/*,application/pdf,.doc,.docx,.txt,.csv"
                                            onChange={(e) => {
                                                const f = e.target.files?.[0]
                                                if (f) setUploadFile(f)
                                                e.target.value = ''
                                            }}
                                        />
                                        <button
                                            onClick={() => fileInputRef.current?.click()}
                                            className="flex-shrink-0 w-11 h-11 bg-[#1F1F1F] border border-[#2D2D2D] rounded-xl flex items-center justify-center text-[#6B7280] hover:text-white hover:border-[#F90100]/50 transition-all"
                                            title="Allega file"
                                        >
                                            <Paperclip className="w-5 h-5" />
                                        </button>
                                        <textarea
                                            ref={inputRef}
                                            value={newMessage}
                                            onChange={(e) => setNewMessage(e.target.value)}
                                            onKeyDown={handleKeyDown}
                                            placeholder="Scrivi un messaggio..."
                                            rows={1}
                                            className="flex-1 bg-[#1F1F1F] border border-[#2D2D2D] rounded-xl px-4 py-3 text-sm text-white placeholder-[#6B7280] focus:outline-none focus:border-[#F90100]/50 resize-none max-h-32"
                                            style={{ minHeight: '44px' }}
                                        />
                                        <button
                                            onClick={sendManualMessage}
                                            disabled={!newMessage.trim() || sending}
                                            className="flex-shrink-0 w-11 h-11 bg-[#F90100] rounded-xl flex items-center justify-center text-white disabled:opacity-30 disabled:cursor-not-allowed hover:bg-[#F90100]/80 transition-all"
                                        >
                                            {sending ? (
                                                <Loader className="w-5 h-5 animate-spin" />
                                            ) : (
                                                <Send className="w-5 h-5" />
                                            )}
                                        </button>
                                    </div>
                                    </div>
                                )}
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    )
}
