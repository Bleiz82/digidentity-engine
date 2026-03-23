'use client'

import { useEffect, useState, useRef } from 'react'
import { supabase, Conversation, Message, AgentContact } from '@/lib/supabase'
import {
    MessageSquare, Send, Bot, User, UserCog, Phone, Mail, Search,
    ChevronLeft, Loader, MessageCircle, Smartphone, Globe, AtSign,
    Paperclip, Mic, FileText, Download, Check, CheckCheck, Image, Trash2, X
} from 'lucide-react'

const channelIcons: Record<string, any> = { whatsapp: Smartphone, telegram: Send, messenger: MessageCircle, instagram: AtSign, email: Mail, chatbot: Globe }
const channelColors: Record<string, string> = { whatsapp: 'text-green-400', telegram: 'text-blue-400', messenger: 'text-purple-400', instagram: 'text-pink-400', email: 'text-yellow-400', chatbot: 'text-cyan-400' }
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
    const [isRecording, setIsRecording] = useState(false)
    const [recordingTime, setRecordingTime] = useState(0)
    const mediaRecorderRef = useRef<MediaRecorder | null>(null)
    const audioChunksRef = useRef<Blob[]>([])
    const recordingTimerRef = useRef<NodeJS.Timeout | null>(null)
    const fileInputRef = useRef<HTMLInputElement>(null)
    const [sending, setSending] = useState(false)
    const [searchQuery, setSearchQuery] = useState('')
    const [filterChannel, setFilterChannel] = useState<string>('all')
    const [filterStatus, setFilterStatus] = useState<string>('all')
    const [mobileShowChat, setMobileShowChat] = useState(false)
    const messagesEndRef = useRef<HTMLDivElement>(null)
    const inputRef = useRef<HTMLTextAreaElement>(null)

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
            const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') ? 'audio/webm;codecs=opus' : 'audio/webm'
            const mr = new MediaRecorder(stream, { mimeType })
            mediaRecorderRef.current = mr
            audioChunksRef.current = []
            mr.ondataavailable = (e: BlobEvent) => { if (e.data.size > 0) audioChunksRef.current.push(e.data) }
            mr.onstop = async () => {
                stream.getTracks().forEach(t => t.stop())
                const blob = new Blob(audioChunksRef.current, { type: 'audio/ogg' })
                const file = new File([blob], 'vocale.ogg', { type: 'audio/ogg' })
                if (selectedConv && blob.size > 0) {
                    setSending(true)
                    try {
                        const fd = new FormData(); fd.append('file', file); fd.append('caption', 'Messaggio vocale')
                        const res = await fetch('https://agent.digidentityagency.it/api/agent/conversations/' + selectedConv + '/upload', { method: 'POST', body: fd })
                        if (res.ok) {
                            const cv = conversations.find(c => c.id === selectedConv)
                            if (cv) await supabase.from('conversations').update({ last_message_at: new Date().toISOString(), last_message_preview: 'Vocale', total_messages: cv.total_messages + 1 }).eq('id', selectedConv)
                            fetchMessages(selectedConv); fetchConversations()
                        }
                    } catch (err) { console.error('Errore invio vocale:', err) } finally { setSending(false) }
                }
            }
            mr.start(); setIsRecording(true); setRecordingTime(0)
            recordingTimerRef.current = setInterval(() => setRecordingTime(t => t + 1), 1000)
        } catch (err) { console.error('Errore microfono:', err) }
    }

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop(); setIsRecording(false)
            if (recordingTimerRef.current) { clearInterval(recordingTimerRef.current); recordingTimerRef.current = null }
            setRecordingTime(0)
        }
    }

    useEffect(() => {
        const params = new URLSearchParams(window.location.search)
        const convId = params.get("conv")
        if (convId && conversations.length > 0 && !selectedConv) { setSelectedConv(convId); setMobileShowChat(true) }
    }, [conversations])

    useEffect(() => { fetchConversations(); const i = setInterval(fetchConversations, 10000); return () => clearInterval(i) }, [])
    useEffect(() => {
        if (selectedConv) { fetchMessages(selectedConv); markAsRead(selectedConv); const i = setInterval(() => fetchMessages(selectedConv), 5000); return () => clearInterval(i) }
    }, [selectedConv])
    useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

    const fetchConversations = async () => {
        try { const { data, error } = await supabase.from('conversations').select('*, contact:contacts(*)').order('last_message_at', { ascending: false }); if (data && !error) setConversations(data as any) }
        catch (err) { console.error('Errore:', err) } finally { setLoading(false) }
    }

    const fetchMessages = async (convId: string) => {
        setLoadingMessages(true)
        try { const { data, error } = await supabase.from('messages').select('*').eq('conversation_id', convId).order('created_at', { ascending: true }); if (data && !error) setMessages(data) }
        catch (err) { console.error('Errore:', err) } finally { setLoadingMessages(false) }
    }

    const markAsRead = async (convId: string) => {
        await supabase.from('messages').update({ read: true }).eq('conversation_id', convId).eq('direction', 'inbound').eq('read', false)
        await supabase.from('conversations').update({ unread_count: 0 }).eq('id', convId)
    }

    const deleteConversation = async (convId: string) => {
        if (!confirm('Eliminare questa conversazione e tutti i messaggi?')) return
        await supabase.from('messages').delete().eq('conversation_id', convId)
        await supabase.from('conversations').delete().eq('id', convId)
        setConversations(prev => prev.filter(c => c.id !== convId))
        if (selectedConv === convId) { setSelectedConv(null); setMessages([]); setMobileShowChat(false) }
    }

    const toggleAI = async (convId: string, currentStatus: boolean) => {
        const n = !currentStatus
        await supabase.from('conversations').update({ ai_enabled: n, status: n ? 'ai' : 'human' }).eq('id', convId)
        fetchConversations()
    }

    const sendManualMessage = async () => {
        if ((!newMessage.trim() && !uploadFile) || !selectedConv || sending) return
        const conv = conversations.find(c => c.id === selectedConv); if (!conv) return
        setSending(true)
        try {
            if (uploadFile) {
                const fd = new FormData(); fd.append('file', uploadFile); if (newMessage.trim()) fd.append('caption', newMessage.trim())
                await fetch('https://agent.digidentityagency.it/api/agent/conversations/' + selectedConv + '/upload', { method: 'POST', body: fd })
            } else {
                await supabase.from('messages').insert({ conversation_id: selectedConv, contact_id: conv.contact_id, direction: 'outbound', sender_type: 'operator', sender_name: 'Stefano', content: newMessage.trim(), content_type: 'text', channel_type: conv.channel_type, delivered: false, read: false, metadata: {} })
                await fetch('https://agent.digidentityagency.it/api/agent/conversations/' + selectedConv + '/send', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ content: newMessage.trim(), sender_name: 'Stefano' })
                })
            }
            await supabase.from('conversations').update({ last_message_at: new Date().toISOString(), last_message_preview: uploadFile ? (uploadFile.name || 'File') : newMessage.trim().substring(0, 100), total_messages: conv.total_messages + 1 }).eq('id', selectedConv)
            setNewMessage(''); setUploadFile(null); fetchMessages(selectedConv); fetchConversations()
        } catch (err) { console.error('Errore:', err) } finally { setSending(false); inputRef.current?.focus() }
    }

    const handleKeyDown = (e: React.KeyboardEvent) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendManualMessage() } }
    const getContactName = (contact: AgentContact | undefined) => contact?.nome || contact?.nome_attivita || contact?.email || contact?.telefono || 'Sconosciuto'
    const formatTime = (dateStr: string) => {
        const d = new Date(dateStr), now = new Date(), diff = now.getTime() - d.getTime(), days = Math.floor(diff / 86400000)
        if (days === 0) return d.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
        if (days === 1) return 'Ieri'
        if (days < 7) return d.toLocaleDateString('it-IT', { weekday: 'short' })
        return d.toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit' })
    }
    const formatMessageTime = (dateStr: string) => new Date(dateStr).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })

    const filteredConversations = conversations.filter(conv => {
        const name = getContactName(conv.contact).toLowerCase()
        const preview = (conv.last_message_preview || '').toLowerCase()
        return (searchQuery === '' || name.includes(searchQuery.toLowerCase()) || preview.includes(searchQuery.toLowerCase()))
            && (filterChannel === 'all' || conv.channel_type === filterChannel)
            && (filterStatus === 'all' || conv.status === filterStatus)
    })

    const selectedConversation = conversations.find(c => c.id === selectedConv)
    const ChannelIcon = selectedConversation ? (channelIcons[selectedConversation.channel_type] || MessageSquare) : MessageSquare

    if (loading) return <div className="flex items-center justify-center h-[80vh]"><Loader className="w-8 h-8 text-[#F90100] animate-spin" /></div>

    return (
        <div className="h-[calc(100vh-4rem)] sm:h-[calc(100vh-4rem)]">
            <div className="mb-3 sm:mb-6">
                <h1 className="text-lg sm:text-2xl font-bold text-white">Inbox</h1>
                <p className="text-[10px] sm:text-sm text-[#6B7280] mt-0.5 sm:mt-1">{conversations.length} conversazioni · {conversations.filter(c => c.unread_count > 0).length} da leggere</p>
            </div>

            <div className="flex h-[calc(100vh-8rem)] sm:h-[calc(100vh-10rem)] rounded-2xl border border-[#1F1F1F] overflow-hidden bg-[#0A0A0A]">
                {/* Lista conversazioni */}
                <div className={`w-full sm:w-80 lg:w-96 border-r border-[#1F1F1F] flex flex-col ${mobileShowChat ? 'hidden sm:flex' : 'flex'}`}>
                    <div className="p-3 sm:p-4 border-b border-[#1F1F1F] space-y-2 sm:space-y-3">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7280]" />
                            <input type="text" placeholder="Cerca..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full bg-[#1F1F1F] border border-[#2D2D2D] rounded-xl pl-10 pr-4 py-2 sm:py-2.5 text-sm text-white placeholder-[#6B7280] focus:outline-none focus:border-[#F90100]/50" />
                        </div>
                        <div className="flex gap-2">
                            <select value={filterChannel} onChange={(e) => setFilterChannel(e.target.value)}
                                className="flex-1 bg-[#1F1F1F] border border-[#2D2D2D] rounded-lg px-2 sm:px-3 py-1.5 text-[10px] sm:text-xs text-white focus:outline-none focus:border-[#F90100]/50">
                                <option value="all">Tutti</option>
                                <option value="whatsapp">WhatsApp</option>
                                <option value="telegram">Telegram</option>
                                <option value="messenger">Messenger</option>
                                <option value="instagram">Instagram</option>
                                <option value="email">Email</option>
                                <option value="chatbot">Chatbot</option>
                            </select>
                            <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}
                                className="flex-1 bg-[#1F1F1F] border border-[#2D2D2D] rounded-lg px-2 sm:px-3 py-1.5 text-[10px] sm:text-xs text-white focus:outline-none focus:border-[#F90100]/50">
                                <option value="all">Tutti</option>
                                <option value="ai">AI</option>
                                <option value="human">Operatore</option>
                                <option value="closed">Chiuse</option>
                            </select>
                        </div>
                    </div>
                    <div className="flex-1 overflow-y-auto">
                        {filteredConversations.length === 0 ? (
                            <div className="flex flex-col items-center justify-center h-full text-[#6B7280]"><MessageSquare className="w-10 h-10 mb-3" /><p className="text-sm">Nessuna conversazione</p></div>
                        ) : filteredConversations.map((conv) => {
                            const Icon = channelIcons[conv.channel_type] || MessageSquare
                            const colorClass = channelColors[conv.channel_type] || 'text-gray-400'
                            const st = statusLabels[conv.status] || statusLabels.ai
                            return (
                                <button key={conv.id} onClick={() => { setSelectedConv(conv.id); setMobileShowChat(true) }}
                                    className={`w-full px-3 sm:px-4 py-3 sm:py-4 flex items-start gap-3 border-b border-[#1F1F1F] transition-all text-left ${selectedConv === conv.id ? 'bg-[#F90100]/5 border-l-2 border-l-[#F90100]' : 'hover:bg-[#1F1F1F]/50'}`}>
                                    <div className="relative flex-shrink-0">
                                        <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-[#1F1F1F] flex items-center justify-center"><Icon className={`w-4 h-4 sm:w-5 sm:h-5 ${colorClass}`} /></div>
                                        {conv.unread_count > 0 && <span className="absolute -top-1 -right-1 w-4 h-4 sm:w-5 sm:h-5 bg-[#F90100] rounded-full flex items-center justify-center text-[8px] sm:text-[10px] font-bold text-white">{conv.unread_count}</span>}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center justify-between">
                                            <span className={`text-xs sm:text-sm font-medium truncate ${conv.unread_count > 0 ? 'text-white' : 'text-[#9CA3AF]'}`}>{getContactName(conv.contact)}</span>
                                            <span className="text-[8px] sm:text-[10px] text-[#6B7280] flex-shrink-0 ml-2">{formatTime(conv.last_message_at)}</span>
                                        </div>
                                        <p className={`text-[10px] sm:text-xs truncate mt-0.5 ${conv.unread_count > 0 ? 'text-[#9CA3AF]' : 'text-[#6B7280]'}`}>{conv.last_message_preview || 'Nessun messaggio'}</p>
                                        <div className="flex items-center gap-2 mt-1">
                                            <span className={`text-[8px] sm:text-[10px] px-1.5 sm:px-2 py-0.5 rounded-full border ${st.color}`}>{st.label}</span>
                                            <span className="text-[8px] sm:text-[10px] text-[#6B7280]">{conv.total_messages} msg</span>
                                        </div>
                                    </div>
                                </button>
                            )
                        })}
                    </div>
                </div>

                {/* Area chat */}
                <div className={`flex-1 flex flex-col ${!mobileShowChat && !selectedConv ? 'hidden sm:flex' : 'flex'}`}>
                    {!selectedConv ? (
                        <div className="flex-1 flex flex-col items-center justify-center text-[#6B7280]">
                            <MessageSquare className="w-12 sm:w-16 h-12 sm:h-16 mb-4 text-[#2D2D2D]" />
                            <p className="text-base sm:text-lg font-medium text-[#9CA3AF]">Seleziona una conversazione</p>
                        </div>
                    ) : (
                        <>
                            {/* Header chat */}
                            <div className="px-3 sm:px-6 py-3 sm:py-4 border-b border-[#1F1F1F] flex items-center justify-between gap-2">
                                <div className="flex items-center gap-2 sm:gap-3 min-w-0">
                                    <button onClick={() => { setMobileShowChat(false); setSelectedConv(null) }} className="sm:hidden text-[#9CA3AF] hover:text-white flex-shrink-0">
                                        <ChevronLeft className="w-5 h-5" />
                                    </button>
                                    <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-[#1F1F1F] flex items-center justify-center flex-shrink-0">
                                        <ChannelIcon className={`w-4 h-4 sm:w-5 sm:h-5 ${channelColors[selectedConversation?.channel_type || ''] || 'text-gray-400'}`} />
                                    </div>
                                    <div className="min-w-0">
                                        <p className="text-xs sm:text-sm font-medium text-white truncate">{getContactName(selectedConversation?.contact)}</p>
                                        <div className="flex items-center gap-1 sm:gap-2 text-[10px] sm:text-xs text-[#6B7280]">
                                            <span className="capitalize">{selectedConversation?.channel_type}</span>
                                            {selectedConversation?.contact?.telefono && <><span className="hidden sm:inline">·</span><span className="hidden sm:inline">{selectedConversation.contact.telefono}</span></>}
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-1.5 sm:gap-3 flex-shrink-0">
                                    <span className={`hidden sm:inline-flex text-[10px] sm:text-xs px-2 sm:px-3 py-1 rounded-full border ${statusLabels[selectedConversation?.status || 'ai']?.color}`}>
                                        {statusLabels[selectedConversation?.status || 'ai']?.label}
                                    </span>
                                    <button onClick={() => selectedConversation && toggleAI(selectedConversation.id, selectedConversation.ai_enabled)}
                                        className={`flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1 sm:py-1.5 rounded-lg text-[10px] sm:text-xs font-medium transition-all ${selectedConversation?.ai_enabled ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-red-500/10 text-red-400 border border-red-500/30'}`}>
                                        <Bot className="w-3 h-3 sm:w-3.5 sm:h-3.5" />
                                        <span className="hidden sm:inline">{selectedConversation?.ai_enabled ? 'AI ON' : 'AI OFF'}</span>
                                        <span className="sm:hidden">{selectedConversation?.ai_enabled ? 'ON' : 'OFF'}</span>
                                    </button>
                                    <button onClick={() => selectedConversation && deleteConversation(selectedConversation.id)}
                                        className="p-1.5 sm:p-2 rounded-lg text-red-400 border border-red-500/30 hover:bg-red-500/10 transition-all">
                                        <Trash2 className="w-3 h-3 sm:w-3.5 sm:h-3.5" />
                                    </button>
                                </div>
                            </div>

                            {/* Messaggi */}
                            <div className="flex-1 overflow-y-auto px-3 sm:px-6 py-3 sm:py-4 space-y-3 sm:space-y-4">
                                {loadingMessages && messages.length === 0 ? (
                                    <div className="flex items-center justify-center h-full"><Loader className="w-6 h-6 text-[#F90100] animate-spin" /></div>
                                ) : messages.length === 0 ? (
                                    <div className="flex flex-col items-center justify-center h-full text-[#6B7280]"><MessageSquare className="w-10 h-10 mb-3" /><p className="text-sm">Nessun messaggio</p></div>
                                ) : messages.map((msg) => {
                                    const isInbound = msg.direction === 'inbound'
                                    const isAI = msg.sender_type === 'ai'
                                    return (
                                        <div key={msg.id} className={`flex ${isInbound ? 'justify-start' : 'justify-end'}`}>
                                            <div className={`max-w-[85%] sm:max-w-[70%] ${isInbound ? 'bg-[#1F1F1F] rounded-2xl rounded-tl-sm' : isAI ? 'bg-emerald-500/10 border border-emerald-500/20 rounded-2xl rounded-tr-sm' : 'bg-[#F90100]/10 border border-[#F90100]/20 rounded-2xl rounded-tr-sm'} px-3 sm:px-4 py-2 sm:py-3`}>
                                                {!isInbound && (
                                                    <div className="flex items-center gap-1.5 mb-1">
                                                        {isAI ? <Bot className="w-3 h-3 text-emerald-400" /> : <UserCog className="w-3 h-3 text-[#F90100]" />}
                                                        <span className={`text-[10px] font-medium ${isAI ? 'text-emerald-400' : 'text-[#F90100]'}`}>{isAI ? 'Digy AI' : msg.sender_name || 'Operatore'}</span>
                                                    </div>
                                                )}
                                                {msg.content_type === 'audio' && msg.media_url && (
                                                    <div className="mb-2">
                                                        <div className="flex items-center gap-2 text-[10px] text-[#6B7280] mb-1 italic"><Mic className="w-3 h-3" />Vocale</div>
                                                        <audio controls className="w-full max-w-[250px] sm:max-w-[280px] h-8" style={{ filter: 'invert(1) hue-rotate(180deg)' }}><source src={msg.media_url} /></audio>
                                                    </div>
                                                )}
                                                {msg.content_type === 'audio' && !msg.media_url && msg.media_transcription && (
                                                    <div className="text-[10px] text-[#6B7280] mb-1 italic flex items-center gap-1"><Mic className="w-3 h-3" />Trascritto</div>
                                                )}
                                                {msg.content_type === 'image' && msg.media_url && (
                                                    <div className="mb-2"><img src={msg.media_url} alt="" className="max-w-[220px] sm:max-w-[280px] rounded-lg cursor-pointer hover:opacity-80" onClick={() => window.open(msg.media_url ?? "", '_blank')} /></div>
                                                )}
                                                {msg.content_type === 'document' && msg.media_url && (
                                                    <a href={msg.media_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 bg-[#2D2D2D] rounded-lg px-3 py-2 mb-2 hover:bg-[#3D3D3D]">
                                                        <FileText className="w-5 h-5 text-blue-400" />
                                                        <div className="flex-1 min-w-0"><p className="text-xs text-white truncate">Documento</p></div>
                                                        <Download className="w-4 h-4 text-[#6B7280]" />
                                                    </a>
                                                )}
                                                <p className="text-xs sm:text-sm text-white whitespace-pre-wrap break-words">{msg.media_transcription || msg.content}</p>
                                                <div className="flex items-center justify-end gap-2 mt-1">
                                                    <span className="text-[10px] text-[#6B7280]">{formatMessageTime(msg.created_at)}</span>
                                                    {msg.ai_tokens_used && <span className="text-[10px] text-[#6B7280]">{msg.ai_tokens_used} tok</span>}
                                                    {msg.direction === 'outbound' && (msg.read ? <CheckCheck className="w-3 h-3 text-blue-400" /> : msg.delivered ? <CheckCheck className="w-3 h-3 text-[#6B7280]" /> : <Check className="w-3 h-3 text-[#6B7280]" />)}
                                                </div>
                                            </div>
                                        </div>
                                    )
                                })}
                                <div ref={messagesEndRef} />
                            </div>

                            {/* Input */}
                            <div className="px-3 sm:px-6 py-3 sm:py-4 border-t border-[#1F1F1F]">
                                {selectedConversation?.ai_enabled ? (
                                    <div className="flex items-center gap-3 text-[#6B7280] bg-[#1F1F1F] rounded-xl px-3 sm:px-4 py-2.5 sm:py-3">
                                        <Bot className="w-4 h-4 sm:w-5 sm:h-5 text-emerald-400 flex-shrink-0" />
                                        <p className="text-xs sm:text-sm">AI attiva — Disattiva per rispondere</p>
                                    </div>
                                ) : (
                                    <div className="flex flex-col gap-2">
                                        {uploadFile && (
                                            <div className="flex items-center gap-2 bg-[#1F1F1F] rounded-lg px-3 py-2">
                                                <FileText className="w-4 h-4 text-blue-400 flex-shrink-0" />
                                                <span className="text-xs text-white truncate flex-1">{uploadFile.name}</span>
                                                <span className="text-[10px] text-[#6B7280]">{(uploadFile.size / 1024).toFixed(0)} KB</span>
                                                <button onClick={() => setUploadFile(null)} className="text-[#6B7280] hover:text-red-400 text-xs">✕</button>
                                            </div>
                                        )}
                                        <div className="flex items-end gap-1.5 sm:gap-2">
                                            <input type="file" ref={fileInputRef} className="hidden" accept="image/*,application/pdf,.doc,.docx,.txt,.csv"
                                                onChange={(e) => { const f = e.target.files?.[0]; if (f) setUploadFile(f); e.target.value = '' }} />
                                            <button onClick={() => fileInputRef.current?.click()}
                                                className="flex-shrink-0 w-10 h-10 sm:w-11 sm:h-11 bg-[#1F1F1F] border border-[#2D2D2D] rounded-xl flex items-center justify-center text-[#6B7280] hover:text-white hover:border-[#F90100]/50 transition-all">
                                                <Paperclip className="w-4 h-4 sm:w-5 sm:h-5" />
                                            </button>
                                            <textarea ref={inputRef} value={newMessage} onChange={(e) => setNewMessage(e.target.value)} onKeyDown={handleKeyDown}
                                                placeholder="Scrivi un messaggio..." rows={1}
                                                className="flex-1 bg-[#1F1F1F] border border-[#2D2D2D] rounded-xl px-3 sm:px-4 py-2.5 sm:py-3 text-xs sm:text-sm text-white placeholder-[#6B7280] focus:outline-none focus:border-[#F90100]/50 resize-none max-h-32"
                                                style={{ minHeight: '40px' }} />
                                            <button onClick={sendManualMessage} disabled={(!newMessage.trim() && !uploadFile) || sending}
                                                className="flex-shrink-0 w-10 h-10 sm:w-11 sm:h-11 bg-[#F90100] rounded-xl flex items-center justify-center text-white disabled:opacity-30 hover:bg-[#F90100]/80 transition-all">
                                                {sending ? <Loader className="w-4 h-4 sm:w-5 sm:h-5 animate-spin" /> : <Send className="w-4 h-4 sm:w-5 sm:h-5" />}
                                            </button>
                                            <button onClick={() => isRecording ? stopRecording() : startRecording()}
                                                className={`flex-shrink-0 w-10 h-10 sm:w-11 sm:h-11 rounded-xl flex items-center justify-center transition-all ${isRecording ? 'bg-red-500 animate-pulse scale-110' : 'bg-[#1F1F1F] border border-[#2D2D2D] text-[#6B7280] hover:text-white hover:border-[#F90100]/50'}`}>
                                                <Mic className="w-4 h-4 sm:w-5 sm:h-5" />
                                            </button>
                                        </div>
                                        {isRecording && (
                                            <div className="flex items-center gap-2 px-2">
                                                <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                                                <span className="text-[10px] sm:text-xs text-red-400 font-medium">Registrazione... {recordingTime}s</span>
                                            </div>
                                        )}
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
