'use client'

import { useEffect, useState } from 'react'
import {
    FileEdit,
    Plus,
    Trash2,
    Edit3,
    Send,
    Loader,
    Smartphone,
    MessageCircle,
    Mail,
    AtSign,
    Save,
    X,
    Copy,
    Check,
    Search
} from 'lucide-react'

const AGENT_API = process.env.NEXT_PUBLIC_AGENT_API_URL || 'https://agent.digidentityagency.it'

const channelOptions = [
    { value: 'whatsapp', label: 'WhatsApp', icon: Smartphone, color: 'text-green-400' },
    { value: 'messenger', label: 'Messenger', icon: MessageCircle, color: 'text-purple-400' },
    { value: 'instagram', label: 'Instagram', icon: AtSign, color: 'text-pink-400' },
    { value: 'email', label: 'Email', icon: Mail, color: 'text-yellow-400' },
]

const categoryOptions = ['utility', 'marketing', 'followup', 'reminder', 'welcome']

interface Template {
    id: string
    name: string
    channel: string
    category: string
    content: string
    placeholders: string[]
    is_active: boolean
    created_at: string
    updated_at: string
}

export default function TemplatesPage() {
    const [templates, setTemplates] = useState<Template[]>([])
    const [loading, setLoading] = useState(true)
    const [editing, setEditing] = useState<Template | null>(null)
    const [creating, setCreating] = useState(false)
    const [saving, setSaving] = useState(false)
    const [searchQuery, setSearchQuery] = useState('')
    const [filterChannel, setFilterChannel] = useState('all')
    const [copiedId, setCopiedId] = useState<string | null>(null)
    const [form, setForm] = useState({ name: '', channel: 'whatsapp', category: 'utility', content: '', placeholders: '' })

    useEffect(() => { loadTemplates() }, [])

    const loadTemplates = async () => {
        setLoading(true)
        try {
            const res = await fetch(`${AGENT_API}/api/social/templates`)
            if (res.ok) { const d = await res.json(); setTemplates(d.templates || []) }
        } catch (e) { console.error(e) }
        setLoading(false)
    }

    const saveTemplate = async () => {
        setSaving(true)
        try {
            const body = {
                name: form.name,
                channel: form.channel,
                category: form.category,
                content: form.content,
                placeholders: form.placeholders.split(',').map(p => p.trim()).filter(Boolean),
            }
            const url = editing ? `${AGENT_API}/api/social/templates/${editing.id}` : `${AGENT_API}/api/social/templates`
            const method = editing ? 'PUT' : 'POST'
            const res = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
            if (res.ok) { setEditing(null); setCreating(false); loadTemplates() }
        } catch (e) { console.error(e) }
        setSaving(false)
    }

    const deleteTemplate = async (id: string) => {
        if (!confirm('Eliminare questo template?')) return
        await fetch(`${AGENT_API}/api/social/templates/${id}`, { method: 'DELETE' })
        loadTemplates()
    }

    const startEdit = (t: Template) => {
        setEditing(t)
        setCreating(false)
        setForm({ name: t.name, channel: t.channel, category: t.category, content: t.content, placeholders: t.placeholders.join(', ') })
    }

    const startCreate = () => {
        setCreating(true)
        setEditing(null)
        setForm({ name: '', channel: 'whatsapp', category: 'utility', content: '', placeholders: '' })
    }

    const cancelEdit = () => { setEditing(null); setCreating(false) }

    const copyContent = (t: Template) => {
        navigator.clipboard.writeText(t.content)
        setCopiedId(t.id)
        setTimeout(() => setCopiedId(null), 2000)
    }

    const filtered = templates.filter(t => {
        if (filterChannel !== 'all' && t.channel !== filterChannel) return false
        if (searchQuery && !t.name.toLowerCase().includes(searchQuery.toLowerCase()) && !t.content.toLowerCase().includes(searchQuery.toLowerCase())) return false
        return true
    })

    const previewContent = (content: string) => {
        return content.replace(/\{\{(\w+)\}\}/g, (_, key) => `[${key}]`)
    }

    if (loading) return (
        <div className="flex items-center justify-center h-[60vh]">
            <Loader className="w-8 h-8 text-[#F90100] animate-spin" />
        </div>
    )

    return (
        <div className="space-y-4 sm:space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                    <h1 className="text-xl sm:text-2xl font-bold text-white flex items-center gap-2">
                        <FileEdit className="w-5 h-5 sm:w-6 sm:h-6 text-[#F90100]" />
                        Message Templates
                    </h1>
                    <p className="text-xs sm:text-sm text-[#6B7280] mt-1">{templates.length} template{templates.length !== 1 ? 's' : ''} configurati</p>
                </div>
                <button onClick={startCreate} className="flex items-center gap-2 px-3 py-2 bg-[#F90100] text-white text-sm rounded-xl hover:bg-[#F90100]/80 transition-all">
                    <Plus className="w-4 h-4" /> Nuovo Template
                </button>
            </div>

            {/* Filters */}
            <div className="flex flex-col sm:flex-row gap-2">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7280]" />
                    <input
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Cerca template..."
                        className="w-full bg-[#0F0F0F] border border-[#1F1F1F] text-white text-sm rounded-xl pl-9 pr-3 py-2.5 focus:outline-none focus:border-[#F90100]/50"
                    />
                </div>
                <select value={filterChannel} onChange={(e) => setFilterChannel(e.target.value)} className="bg-[#0F0F0F] border border-[#1F1F1F] text-white text-sm rounded-xl px-3 py-2.5 focus:outline-none">
                    <option value="all">Tutti i canali</option>
                    {channelOptions.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                </select>
            </div>

            {/* Create/Edit Form */}
            {(creating || editing) && (
                <div className="bg-[#0F0F0F] border border-[#F90100]/30 rounded-xl p-4 space-y-3">
                    <div className="flex items-center justify-between">
                        <h3 className="text-sm font-semibold text-white">{editing ? 'Modifica Template' : 'Nuovo Template'}</h3>
                        <button onClick={cancelEdit} className="text-[#6B7280] hover:text-white"><X className="w-4 h-4" /></button>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                        <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Nome template" className="bg-[#1A1A1A] border border-[#2A2A2A] text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-[#F90100]/50" />
                        <select value={form.channel} onChange={e => setForm({ ...form, channel: e.target.value })} className="bg-[#1A1A1A] border border-[#2A2A2A] text-white text-sm rounded-lg px-3 py-2 focus:outline-none">
                            {channelOptions.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                        </select>
                        <select value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} className="bg-[#1A1A1A] border border-[#2A2A2A] text-white text-sm rounded-lg px-3 py-2 focus:outline-none">
                            {categoryOptions.map(c => <option key={c} value={c}>{c}</option>)}
                        </select>
                    </div>
                    <textarea value={form.content} onChange={e => setForm({ ...form, content: e.target.value })} placeholder="Contenuto messaggio... Usa {{nome}}, {{data}}, {{ora}} per i placeholder" className="w-full bg-[#1A1A1A] border border-[#2A2A2A] text-white text-sm rounded-lg px-3 py-2 h-24 resize-none focus:outline-none focus:border-[#F90100]/50" />
                    <input value={form.placeholders} onChange={e => setForm({ ...form, placeholders: e.target.value })} placeholder="Placeholder (separati da virgola): nome, data, ora" className="w-full bg-[#1A1A1A] border border-[#2A2A2A] text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-[#F90100]/50" />
                    {form.content && (
                        <div className="bg-[#1A1A1A] rounded-lg p-3">
                            <p className="text-[10px] text-[#6B7280] mb-1 uppercase tracking-wider">Anteprima</p>
                            <p className="text-sm text-[#D1D5DB]">{previewContent(form.content)}</p>
                        </div>
                    )}
                    <div className="flex justify-end">
                        <button onClick={saveTemplate} disabled={saving || !form.name || !form.content} className="flex items-center gap-2 px-4 py-2 bg-[#F90100] text-white text-sm rounded-xl hover:bg-[#F90100]/80 disabled:opacity-50 transition-all">
                            {saving ? <Loader className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />} Salva
                        </button>
                    </div>
                </div>
            )}

            {/* Templates List */}
            <div className="space-y-3">
                {filtered.length === 0 ? (
                    <div className="text-center py-12 text-[#6B7280]">Nessun template trovato</div>
                ) : filtered.map((t) => {
                    const ch = channelOptions.find(c => c.value === t.channel)
                    const ChIcon = ch?.icon || Smartphone
                    return (
                        <div key={t.id} className="bg-[#0F0F0F] border border-[#1F1F1F] rounded-xl p-3 sm:p-4">
                            <div className="flex items-start justify-between gap-2 mb-2">
                                <div className="flex items-center gap-2 min-w-0">
                                    <ChIcon className={`w-4 h-4 shrink-0 ${ch?.color || 'text-white'}`} />
                                    <h3 className="text-sm font-semibold text-white truncate">{t.name}</h3>
                                    <span className="text-[10px] px-2 py-0.5 bg-[#1A1A1A] border border-[#2A2A2A] text-[#9CA3AF] rounded-full shrink-0">{t.category}</span>
                                </div>
                                <div className="flex gap-1 shrink-0">
                                    <button onClick={() => copyContent(t)} className="p-1.5 text-[#6B7280] hover:text-white transition-all">
                                        {copiedId === t.id ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
                                    </button>
                                    <button onClick={() => startEdit(t)} className="p-1.5 text-[#6B7280] hover:text-blue-400 transition-all">
                                        <Edit3 className="w-3.5 h-3.5" />
                                    </button>
                                    <button onClick={() => deleteTemplate(t.id)} className="p-1.5 text-[#6B7280] hover:text-red-400 transition-all">
                                        <Trash2 className="w-3.5 h-3.5" />
                                    </button>
                                </div>
                            </div>
                            <p className="text-xs text-[#9CA3AF] line-clamp-2">{previewContent(t.content)}</p>
                            {t.placeholders.length > 0 && (
                                <div className="flex flex-wrap gap-1 mt-2">
                                    {t.placeholders.map(p => (
                                        <span key={p} className="text-[10px] px-1.5 py-0.5 bg-[#F90100]/10 text-[#F90100] border border-[#F90100]/20 rounded">{`{{${p}}}`}</span>
                                    ))}
                                </div>
                            )}
                        </div>
                    )
                })}
            </div>
        </div>
    )
}
