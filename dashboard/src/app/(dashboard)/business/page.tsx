'use client'

import { useEffect, useState } from 'react'
import {
    Building2,
    Facebook,
    Instagram,
    Globe,
    MapPin,
    Phone,
    Mail,
    Clock,
    Edit3,
    Save,
    X,
    Loader,
    ExternalLink,
    Users,
    FileText,
    Image as ImageIcon
} from 'lucide-react'

const AGENT_API = process.env.NEXT_PUBLIC_AGENT_API_URL || 'https://agent.digidentityagency.it'
const PAGE_ID = '218598614662100'

interface PageMetadata {
    id: string
    name: string
    about?: string
    bio?: string
    category?: string
    description?: string
    website?: string
    phone?: string
    single_line_address?: string
    emails?: string[]
    fan_count?: number
    followers_count?: number
    picture?: { data: { url: string } }
    cover?: { source: string }
}

interface BusinessInfo {
    user: { id: string; name: string; category?: string }
    pages: any[]
    instagram: {
        id: string
        username: string
        name: string
        profile_picture_url?: string
        followers_count?: number
        media_count?: number
        biography?: string
    } | null
}

export default function BusinessPage() {
    const [metadata, setMetadata] = useState<PageMetadata | null>(null)
    const [business, setBusiness] = useState<BusinessInfo | null>(null)
    const [loading, setLoading] = useState(true)
    const [editing, setEditing] = useState(false)
    const [saving, setSaving] = useState(false)
    const [form, setForm] = useState({ about: '', description: '', website: '', phone: '' })

    useEffect(() => { loadData() }, [])

    const loadData = async () => {
        setLoading(true)
        try {
            const [metaRes, bizRes] = await Promise.all([
                fetch(`${AGENT_API}/api/social/pages/${PAGE_ID}/metadata`),
                fetch(`${AGENT_API}/api/social/business`),
            ])
            if (metaRes.ok) {
                const d = await metaRes.json()
                setMetadata(d)
                setForm({ about: d.about || '', description: d.description || '', website: d.website || '', phone: d.phone || '' })
            }
            if (bizRes.ok) { const d = await bizRes.json(); setBusiness(d) }
        } catch (e) { console.error(e) }
        setLoading(false)
    }

    const saveMetadata = async () => {
        setSaving(true)
        try {
            const res = await fetch(`${AGENT_API}/api/social/pages/${PAGE_ID}/metadata`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(form),
            })
            if (res.ok) { setEditing(false); loadData() }
        } catch (e) { console.error(e) }
        setSaving(false)
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
                        <Building2 className="w-5 h-5 sm:w-6 sm:h-6 text-[#F90100]" />
                        Business Overview
                    </h1>
                    <p className="text-xs sm:text-sm text-[#6B7280] mt-1">Pagine, account e impostazioni</p>
                </div>
                <button onClick={() => setEditing(!editing)} className="flex items-center gap-2 px-3 py-2 bg-[#1A1A1A] border border-[#2A2A2A] text-[#9CA3AF] text-sm rounded-xl hover:text-white transition-all">
                    <Edit3 className="w-4 h-4" /> {editing ? 'Annulla' : 'Modifica'}
                </button>
            </div>

            {/* Facebook Page Card */}
            <div className="bg-[#0F0F0F] border border-[#1F1F1F] rounded-xl overflow-hidden">
                {metadata?.cover && (
                    <div className="h-32 sm:h-48 bg-cover bg-center" style={{ backgroundImage: `url(${metadata.cover.source})` }} />
                )}
                <div className="p-4 sm:p-6">
                    <div className="flex flex-col sm:flex-row sm:items-start gap-4">
                        {metadata?.picture && (
                            <img src={metadata.picture.data.url} alt="" className="w-16 h-16 sm:w-20 sm:h-20 rounded-xl border-2 border-[#1F1F1F] shrink-0 -mt-8 sm:-mt-12 bg-[#0A0A0A]" />
                        )}
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                                <Facebook className="w-5 h-5 text-blue-400 shrink-0" />
                                <h2 className="text-lg font-bold text-white truncate">{metadata?.name}</h2>
                            </div>
                            <p className="text-xs text-[#6B7280] mb-3">{metadata?.category}</p>
                            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                                <div className="bg-[#1A1A1A] rounded-lg p-3">
                                    <p className="text-[10px] text-[#6B7280] uppercase">Fan</p>
                                    <p className="text-lg font-bold text-white">{metadata?.fan_count || 0}</p>
                                </div>
                                <div className="bg-[#1A1A1A] rounded-lg p-3">
                                    <p className="text-[10px] text-[#6B7280] uppercase">Follower</p>
                                    <p className="text-lg font-bold text-white">{metadata?.followers_count || 0}</p>
                                </div>
                                <div className="bg-[#1A1A1A] rounded-lg p-3 col-span-2 sm:col-span-1">
                                    <p className="text-[10px] text-[#6B7280] uppercase">ID</p>
                                    <p className="text-xs font-mono text-white truncate">{metadata?.id}</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Metadata Details */}
                    <div className="mt-4 space-y-3">
                        {editing ? (
                            <div className="space-y-3">
                                <div>
                                    <label className="text-[10px] text-[#6B7280] uppercase mb-1 block">About</label>
                                    <textarea value={form.about} onChange={e => setForm({ ...form, about: e.target.value })} className="w-full bg-[#1A1A1A] border border-[#2A2A2A] text-white text-sm rounded-lg px-3 py-2 h-20 resize-none focus:outline-none focus:border-[#F90100]/50" />
                                </div>
                                <div>
                                    <label className="text-[10px] text-[#6B7280] uppercase mb-1 block">Descrizione</label>
                                    <textarea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} className="w-full bg-[#1A1A1A] border border-[#2A2A2A] text-white text-sm rounded-lg px-3 py-2 h-20 resize-none focus:outline-none focus:border-[#F90100]/50" />
                                </div>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                    <div>
                                        <label className="text-[10px] text-[#6B7280] uppercase mb-1 block">Sito Web</label>
                                        <input value={form.website} onChange={e => setForm({ ...form, website: e.target.value })} className="w-full bg-[#1A1A1A] border border-[#2A2A2A] text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-[#F90100]/50" />
                                    </div>
                                    <div>
                                        <label className="text-[10px] text-[#6B7280] uppercase mb-1 block">Telefono</label>
                                        <input value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} className="w-full bg-[#1A1A1A] border border-[#2A2A2A] text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-[#F90100]/50" />
                                    </div>
                                </div>
                                <div className="flex justify-end">
                                    <button onClick={saveMetadata} disabled={saving} className="flex items-center gap-2 px-4 py-2 bg-[#F90100] text-white text-sm rounded-xl hover:bg-[#F90100]/80 disabled:opacity-50 transition-all">
                                        {saving ? <Loader className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />} Salva
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <div className="space-y-2">
                                {metadata?.about && (
                                    <div className="bg-[#1A1A1A] rounded-lg p-3">
                                        <p className="text-[10px] text-[#6B7280] uppercase mb-1">About</p>
                                        <p className="text-sm text-[#D1D5DB] whitespace-pre-line">{metadata.about}</p>
                                    </div>
                                )}
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                    {metadata?.website && (
                                        <div className="flex items-center gap-2 bg-[#1A1A1A] rounded-lg p-3">
                                            <Globe className="w-4 h-4 text-[#6B7280] shrink-0" />
                                            <a href={metadata.website} target="_blank" rel="noopener" className="text-sm text-blue-400 truncate hover:underline">{metadata.website}</a>
                                        </div>
                                    )}
                                    {metadata?.phone && (
                                        <div className="flex items-center gap-2 bg-[#1A1A1A] rounded-lg p-3">
                                            <Phone className="w-4 h-4 text-[#6B7280] shrink-0" />
                                            <span className="text-sm text-[#D1D5DB]">{metadata.phone}</span>
                                        </div>
                                    )}
                                    {metadata?.single_line_address && (
                                        <div className="flex items-center gap-2 bg-[#1A1A1A] rounded-lg p-3">
                                            <MapPin className="w-4 h-4 text-[#6B7280] shrink-0" />
                                            <span className="text-sm text-[#D1D5DB]">{metadata.single_line_address}</span>
                                        </div>
                                    )}
                                    {metadata?.emails?.[0] && (
                                        <div className="flex items-center gap-2 bg-[#1A1A1A] rounded-lg p-3">
                                            <Mail className="w-4 h-4 text-[#6B7280] shrink-0" />
                                            <span className="text-sm text-[#D1D5DB]">{metadata.emails[0]}</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Instagram Card */}
            {business?.instagram && (
                <div className="bg-[#0F0F0F] border border-[#1F1F1F] rounded-xl p-4 sm:p-6">
                    <div className="flex items-start gap-4">
                        {business.instagram.profile_picture_url && (
                            <img src={business.instagram.profile_picture_url} alt="" className="w-14 h-14 sm:w-16 sm:h-16 rounded-xl shrink-0" />
                        )}
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                                <Instagram className="w-5 h-5 text-pink-400 shrink-0" />
                                <h2 className="text-base font-bold text-white truncate">{business.instagram.name}</h2>
                            </div>
                            <a href={`https://instagram.com/${business.instagram.username}`} target="_blank" rel="noopener" className="text-xs text-pink-400 hover:underline flex items-center gap-1">
                                @{business.instagram.username} <ExternalLink className="w-3 h-3" />
                            </a>
                            {business.instagram.biography && (
                                <p className="text-xs text-[#9CA3AF] mt-2 whitespace-pre-line">{business.instagram.biography}</p>
                            )}
                            <div className="grid grid-cols-2 gap-3 mt-3">
                                <div className="bg-[#1A1A1A] rounded-lg p-3">
                                    <p className="text-[10px] text-[#6B7280] uppercase flex items-center gap-1"><Users className="w-3 h-3" />Follower</p>
                                    <p className="text-lg font-bold text-white">{business.instagram.followers_count || 0}</p>
                                </div>
                                <div className="bg-[#1A1A1A] rounded-lg p-3">
                                    <p className="text-[10px] text-[#6B7280] uppercase flex items-center gap-1"><ImageIcon className="w-3 h-3" />Media</p>
                                    <p className="text-lg font-bold text-white">{business.instagram.media_count || 0}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Connected Pages */}
            <div className="bg-[#0F0F0F] border border-[#1F1F1F] rounded-xl p-4 sm:p-6">
                <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                    <FileText className="w-4 h-4 text-[#F90100]" /> Pagine Collegate
                </h3>
                <div className="space-y-2">
                    {business?.pages?.map((page: any) => (
                        <div key={page.id} className="flex items-center justify-between bg-[#1A1A1A] rounded-lg p-3">
                            <div className="flex items-center gap-2">
                                <Facebook className="w-4 h-4 text-blue-400" />
                                <span className="text-sm text-white">{page.name}</span>
                                <span className="text-[10px] text-[#6B7280]">{page.category}</span>
                            </div>
                            <span className="text-[10px] font-mono text-[#6B7280]">{page.id}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}
