'use client'

import { useEffect, useState, useCallback } from 'react'
import {
    Share2,
    Facebook,
    Instagram,
    MessageSquare,
    Heart,
    Send,
    Loader,
    ExternalLink,
    Trash2,
    Image as ImageIcon,
    Video,
    RefreshCw,
    ChevronDown,
    Plus,
    X,
    ThumbsUp,
    Eye,
    TrendingUp,
    Calendar,
    MoreHorizontal,
    Link as LinkIcon,
    Type,
    Camera
} from 'lucide-react'

const AGENT_API = process.env.NEXT_PUBLIC_AGENT_API_URL || 'https://agent.digidentityagency.it'
const PAGE_ID = '218598614662100'

interface Post {
    id: string
    message?: string
    story?: string
    created_time: string
    full_picture?: string
    permalink_url: string
    type?: string
    likes?: { summary: { total_count: number } }
    comments?: { summary: { total_count: number } }
    reactions?: { summary: { total_count: number } }
}

interface Comment {
    id: string
    message?: string
    text?: string
    from?: { id: string; name: string }
    username?: string
    created_time?: string
    timestamp?: string
    like_count?: number
}

interface IgMedia {
    id: string
    caption?: string
    media_type: string
    media_url?: string
    thumbnail_url?: string
    permalink: string
    timestamp: string
    like_count?: number
    comments_count?: number
}

interface Stats {
    facebook: { id?: string; name?: string; category?: string }
    instagram: { followers_count?: number; media_count?: number; id?: string }
}

export default function SocialManagerPage() {
    const [tab, setTab] = useState<'facebook' | 'instagram'>('facebook')
    const [posts, setPosts] = useState<Post[]>([])
    const [igMedia, setIgMedia] = useState<IgMedia[]>([])
    const [stats, setStats] = useState<Stats | null>(null)
    const [loading, setLoading] = useState(true)
    const [selectedPost, setSelectedPost] = useState<string | null>(null)
    const [comments, setComments] = useState<Comment[]>([])
    const [loadingComments, setLoadingComments] = useState(false)
    const [replyText, setReplyText] = useState('')
    const [sending, setSending] = useState(false)
    const [newPostText, setNewPostText] = useState('')
    const [newPostImage, setNewPostImage] = useState('')
    const [newPostLink, setNewPostLink] = useState('')
    const [postType, setPostType] = useState<'text' | 'photo' | 'link'>('text')
    const [showNewPost, setShowNewPost] = useState(false)
    const [publishing, setPublishing] = useState(false)
    const [postMenuOpen, setPostMenuOpen] = useState<string | null>(null)

    useEffect(() => { loadData() }, [])

    const loadData = useCallback(async () => {
        setLoading(true)
        try {
            const [postsRes, igRes, statsRes] = await Promise.all([
                fetch(`${AGENT_API}/api/social/pages/${PAGE_ID}/posts?limit=25`),
                fetch(`${AGENT_API}/api/social/instagram/media?limit=25`),
                fetch(`${AGENT_API}/api/social/stats`),
            ])
            if (postsRes.ok) { const d = await postsRes.json(); setPosts(d.posts || []) }
            if (igRes.ok) { const d = await igRes.json(); setIgMedia(d.media || []) }
            if (statsRes.ok) { const d = await statsRes.json(); setStats(d) }
        } catch (e) { console.error('Errore caricamento:', e) }
        setLoading(false)
    }, [])

    const loadComments = async (postId: string) => {
        if (selectedPost === postId) { setSelectedPost(null); return }
        setSelectedPost(postId)
        setLoadingComments(true)
        setReplyText('')
        try {
            const endpoint = tab === 'facebook'
                ? `${AGENT_API}/api/social/posts/${postId}/comments`
                : `${AGENT_API}/api/social/instagram/media/${postId}/comments`
            const res = await fetch(endpoint)
            if (res.ok) { const d = await res.json(); setComments(d.comments || []) }
        } catch (e) { console.error('Errore commenti:', e) }
        setLoadingComments(false)
    }

    const sendReply = async (postId: string) => {
        if (!replyText.trim()) return
        setSending(true)
        try {
            const endpoint = tab === 'facebook'
                ? `${AGENT_API}/api/social/posts/${postId}/comments`
                : `${AGENT_API}/api/social/instagram/media/${postId}/comments`
            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: replyText }),
            })
            if (res.ok) { setReplyText(''); loadComments(postId) }
        } catch (e) { console.error('Errore invio:', e) }
        setSending(false)
    }

    const publishPost = async () => {
        if (!newPostText.trim() && !newPostImage.trim() && !newPostLink.trim()) return
        setPublishing(true)
        try {
            let endpoint = `${AGENT_API}/api/social/pages/${PAGE_ID}/posts`
            let body: any = {}
            if (postType === 'photo' && newPostImage.trim()) {
                endpoint = `${AGENT_API}/api/social/pages/${PAGE_ID}/photos`
                body = { url: newPostImage, caption: newPostText }
            } else if (postType === 'link' && newPostLink.trim()) {
                body = { message: newPostText, link: newPostLink }
            } else {
                body = { message: newPostText }
            }
            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            })
            if (res.ok) { setNewPostText(''); setNewPostImage(''); setNewPostLink(''); setShowNewPost(false); setPostType('text'); loadData() }
        } catch (e) { console.error('Errore pubblicazione:', e) }
        setPublishing(false)
    }

    const deletePost = async (postId: string) => {
        if (!confirm('Eliminare questo post?')) return
        setPostMenuOpen(null)
        try {
            await fetch(`${AGENT_API}/api/social/posts/${postId}`, { method: 'DELETE' })
            loadData()
        } catch (e) { console.error('Errore eliminazione:', e) }
    }

    const formatDate = (d: string) => {
        const date = new Date(d)
        const now = new Date()
        const diffMs = now.getTime() - date.getTime()
        const diffH = Math.floor(diffMs / 3600000)
        const diffD = Math.floor(diffMs / 86400000)
        if (diffH < 1) return `${Math.floor(diffMs / 60000)}m fa`
        if (diffH < 24) return `${diffH}h fa`
        if (diffD < 7) return `${diffD}g fa`
        return date.toLocaleDateString('it-IT', { day: '2-digit', month: 'short', year: diffD > 365 ? 'numeric' : undefined })
    }

    const formatNumber = (n: number) => {
        if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
        if (n >= 1000) return (n / 1000).toFixed(1) + 'K'
        return n.toString()
    }

    const totalReactions = posts.reduce((sum, p) => sum + (p.reactions?.summary?.total_count || p.likes?.summary?.total_count || 0), 0)
    const totalComments = posts.reduce((sum, p) => sum + (p.comments?.summary?.total_count || 0), 0)

    if (loading) return (
        <div className="flex items-center justify-center h-[60vh]">
            <div className="text-center">
                <Loader className="w-8 h-8 text-[#F90100] animate-spin mx-auto mb-3" />
                <p className="text-sm text-[#6B7280]">Caricamento social...</p>
            </div>
        </div>
    )

    return (
        <div className="space-y-4 sm:space-y-6 pb-8">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                    <h1 className="text-xl sm:text-2xl font-bold text-white flex items-center gap-2.5">
                        <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-xl bg-[#F90100]/10 border border-[#F90100]/20 flex items-center justify-center">
                            <Share2 className="w-4 h-4 sm:w-5 sm:h-5 text-[#F90100]" />
                        </div>
                        Social Manager
                    </h1>
                    <p className="text-xs sm:text-sm text-[#6B7280] mt-1 ml-[42px] sm:ml-[46px]">Post, commenti e analytics</p>
                </div>
                <div className="flex gap-2 ml-[42px] sm:ml-0">
                    <button onClick={() => setShowNewPost(!showNewPost)} className="flex items-center gap-2 px-4 py-2.5 bg-[#F90100] text-white text-sm font-medium rounded-xl hover:bg-[#D50000] shadow-lg shadow-[#F90100]/10 transition-all active:scale-95">
                        <Plus className="w-4 h-4" /> <span className="hidden sm:inline">Nuovo</span> Post
                    </button>
                    <button onClick={loadData} className="p-2.5 bg-[#0F0F0F] border border-[#1F1F1F] text-[#9CA3AF] rounded-xl hover:text-white hover:border-[#2A2A2A] transition-all active:scale-95">
                        <RefreshCw className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* Stats Overview */}
            <div className="grid grid-cols-2 lg:grid-cols-5 gap-2 sm:gap-3">
                <div className="bg-[#0F0F0F] border border-[#1F1F1F] rounded-xl p-3 sm:p-4 hover:border-[#2A2A2A] transition-all">
                    <div className="flex items-center gap-2 mb-2">
                        <div className="w-7 h-7 rounded-lg bg-blue-500/10 flex items-center justify-center">
                            <Facebook className="w-3.5 h-3.5 text-blue-400" />
                        </div>
                        <span className="text-[10px] sm:text-xs text-[#6B7280] uppercase tracking-wider">Pagina</span>
                    </div>
                    <p className="text-sm sm:text-base font-bold text-white truncate">{stats?.facebook?.name || '-'}</p>
                    <p className="text-[10px] text-[#6B7280] mt-0.5">{stats?.facebook?.category}</p>
                </div>
                <div className="bg-[#0F0F0F] border border-[#1F1F1F] rounded-xl p-3 sm:p-4 hover:border-[#2A2A2A] transition-all">
                    <div className="flex items-center gap-2 mb-2">
                        <div className="w-7 h-7 rounded-lg bg-blue-500/10 flex items-center justify-center">
                            <Calendar className="w-3.5 h-3.5 text-blue-400" />
                        </div>
                        <span className="text-[10px] sm:text-xs text-[#6B7280] uppercase tracking-wider">Post</span>
                    </div>
                    <p className="text-xl sm:text-2xl font-bold text-white">{posts.length}</p>
                </div>
                <div className="bg-[#0F0F0F] border border-[#1F1F1F] rounded-xl p-3 sm:p-4 hover:border-[#2A2A2A] transition-all">
                    <div className="flex items-center gap-2 mb-2">
                        <div className="w-7 h-7 rounded-lg bg-red-500/10 flex items-center justify-center">
                            <Heart className="w-3.5 h-3.5 text-red-400" />
                        </div>
                        <span className="text-[10px] sm:text-xs text-[#6B7280] uppercase tracking-wider">Reactions</span>
                    </div>
                    <p className="text-xl sm:text-2xl font-bold text-white">{formatNumber(totalReactions)}</p>
                </div>
                <div className="bg-[#0F0F0F] border border-[#1F1F1F] rounded-xl p-3 sm:p-4 hover:border-[#2A2A2A] transition-all">
                    <div className="flex items-center gap-2 mb-2">
                        <div className="w-7 h-7 rounded-lg bg-pink-500/10 flex items-center justify-center">
                            <Instagram className="w-3.5 h-3.5 text-pink-400" />
                        </div>
                        <span className="text-[10px] sm:text-xs text-[#6B7280] uppercase tracking-wider">Follower IG</span>
                    </div>
                    <p className="text-xl sm:text-2xl font-bold text-white">{formatNumber(stats?.instagram?.followers_count || 0)}</p>
                </div>
                <div className="col-span-2 lg:col-span-1 bg-[#0F0F0F] border border-[#1F1F1F] rounded-xl p-3 sm:p-4 hover:border-[#2A2A2A] transition-all">
                    <div className="flex items-center gap-2 mb-2">
                        <div className="w-7 h-7 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                            <MessageSquare className="w-3.5 h-3.5 text-emerald-400" />
                        </div>
                        <span className="text-[10px] sm:text-xs text-[#6B7280] uppercase tracking-wider">Commenti</span>
                    </div>
                    <p className="text-xl sm:text-2xl font-bold text-white">{formatNumber(totalComments)}</p>
                </div>
            </div>

            {/* New Post Composer */}
            {showNewPost && (
                <div className="bg-[#0F0F0F] border border-[#F90100]/20 rounded-xl overflow-hidden shadow-lg shadow-[#F90100]/5">
                    <div className="p-4 border-b border-[#1F1F1F] flex items-center justify-between">
                        <h3 className="text-sm font-semibold text-white">Crea nuovo post</h3>
                        <button onClick={() => { setShowNewPost(false); setPostType('text') }} className="text-[#6B7280] hover:text-white transition-all"><X className="w-4 h-4" /></button>
                    </div>
                    <div className="p-4 space-y-3">
                        <div className="flex gap-1 bg-[#1A1A1A] rounded-xl p-1">
                            {([
                                { type: 'text' as const, icon: Type, label: 'Testo' },
                                { type: 'photo' as const, icon: Camera, label: 'Foto' },
                                { type: 'link' as const, icon: LinkIcon, label: 'Link' },
                            ]).map(t => (
                                <button key={t.type} onClick={() => setPostType(t.type)} className={`flex-1 flex items-center justify-center gap-1.5 py-2 text-xs font-medium rounded-lg transition-all ${postType === t.type ? 'bg-[#F90100]/15 text-[#F90100] shadow-sm' : 'text-[#6B7280] hover:text-white'}`}>
                                    <t.icon className="w-3.5 h-3.5" /> {t.label}
                                </button>
                            ))}
                        </div>
                        <textarea
                            value={newPostText}
                            onChange={(e) => setNewPostText(e.target.value)}
                            placeholder={postType === 'photo' ? "Caption della foto..." : "Cosa vuoi condividere?"}
                            className="w-full bg-[#1A1A1A] border border-[#2A2A2A] text-white rounded-xl p-3.5 text-sm resize-none h-28 focus:outline-none focus:border-[#F90100]/30 placeholder:text-[#4A4A4A] transition-all"
                        />
                        {postType === 'photo' && (
                            <div className="space-y-2">
                                <input
                                    value={newPostImage}
                                    onChange={(e) => setNewPostImage(e.target.value)}
                                    placeholder="URL immagine (https://...)"
                                    className="w-full bg-[#1A1A1A] border border-[#2A2A2A] text-white rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:border-[#F90100]/30 placeholder:text-[#4A4A4A] transition-all"
                                />
                                {newPostImage && (
                                    <div className="relative rounded-xl overflow-hidden border border-[#2A2A2A]">
                                        <img src={newPostImage} alt="Preview" className="w-full max-h-52 object-cover" onError={(e) => (e.target as HTMLImageElement).style.display = 'none'} />
                                        <button onClick={() => setNewPostImage('')} className="absolute top-2 right-2 p-1.5 bg-black/70 rounded-lg text-white hover:bg-black transition-all">
                                            <X className="w-3.5 h-3.5" />
                                        </button>
                                    </div>
                                )}
                            </div>
                        )}
                        {postType === 'link' && (
                            <input
                                value={newPostLink}
                                onChange={(e) => setNewPostLink(e.target.value)}
                                placeholder="URL del link (https://...)"
                                className="w-full bg-[#1A1A1A] border border-[#2A2A2A] text-white rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:border-[#F90100]/30 placeholder:text-[#4A4A4A] transition-all"
                            />
                        )}
                    </div>
                    <div className="px-4 py-3 border-t border-[#1F1F1F] flex justify-end gap-2 bg-[#0A0A0A]">
                        <button onClick={() => { setShowNewPost(false); setPostType('text') }} className="px-4 py-2 text-sm text-[#9CA3AF] hover:text-white rounded-xl transition-all">Annulla</button>
                        <button onClick={publishPost} disabled={publishing || (!newPostText.trim() && !newPostImage.trim() && !newPostLink.trim())} className="flex items-center gap-2 px-5 py-2 bg-[#F90100] text-white text-sm font-medium rounded-xl hover:bg-[#D50000] disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-[#F90100]/10 transition-all active:scale-95">
                            {publishing ? <Loader className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />} Pubblica
                        </button>
                    </div>
                </div>
            )}

            {/* Platform Tabs */}
            <div className="flex gap-1.5 bg-[#0F0F0F] border border-[#1F1F1F] rounded-xl p-1.5">
                <button onClick={() => { setTab('facebook'); setSelectedPost(null) }} className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${tab === 'facebook' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20 shadow-sm' : 'text-[#6B7280] hover:text-white'}`}>
                    <Facebook className="w-4 h-4" /> Facebook <span className="text-[10px] opacity-60 hidden sm:inline">({posts.length})</span>
                </button>
                <button onClick={() => { setTab('instagram'); setSelectedPost(null) }} className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${tab === 'instagram' ? 'bg-gradient-to-r from-purple-500/10 to-pink-500/10 text-pink-400 border border-pink-500/20 shadow-sm' : 'text-[#6B7280] hover:text-white'}`}>
                    <Instagram className="w-4 h-4" /> Instagram <span className="text-[10px] opacity-60 hidden sm:inline">({igMedia.length})</span>
                </button>
            </div>

            {/* Facebook Posts */}
            {tab === 'facebook' && (
                <div className="space-y-3">
                    {posts.length === 0 ? (
                        <div className="text-center py-16 bg-[#0F0F0F] border border-[#1F1F1F] rounded-xl">
                            <Facebook className="w-10 h-10 text-[#2A2A2A] mx-auto mb-3" />
                            <p className="text-sm text-[#6B7280]">Nessun post trovato</p>
                            <button onClick={() => setShowNewPost(true)} className="mt-3 text-sm text-[#F90100] hover:underline">Crea il primo post</button>
                        </div>
                    ) : posts.map((post) => {
                        const reactions = post.reactions?.summary?.total_count || post.likes?.summary?.total_count || 0
                        const commentCount = post.comments?.summary?.total_count || 0
                        return (
                            <div key={post.id} className="bg-[#0F0F0F] border border-[#1F1F1F] rounded-xl overflow-hidden hover:border-[#2A2A2A] transition-all group">
                                {/* Post Header */}
                                <div className="px-3 sm:px-4 pt-3 sm:pt-4 flex items-center justify-between">
                                    <div className="flex items-center gap-2.5">
                                        <div className="w-9 h-9 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center shrink-0">
                                            <Facebook className="w-4 h-4 text-blue-400" />
                                        </div>
                                        <div>
                                            <p className="text-xs sm:text-sm font-semibold text-white">DigIdentity Agency</p>
                                            <p className="text-[10px] text-[#6B7280]">{formatDate(post.created_time)}</p>
                                        </div>
                                    </div>
                                    <div className="relative">
                                        <button onClick={() => setPostMenuOpen(postMenuOpen === post.id ? null : post.id)} className="p-1.5 text-[#4A4A4A] hover:text-white rounded-lg hover:bg-[#1A1A1A] transition-all opacity-0 group-hover:opacity-100 sm:opacity-100">
                                            <MoreHorizontal className="w-4 h-4" />
                                        </button>
                                        {postMenuOpen === post.id && (
                                            <>
                                                <div className="fixed inset-0 z-10" onClick={() => setPostMenuOpen(null)} />
                                                <div className="absolute right-0 top-8 z-20 bg-[#1A1A1A] border border-[#2A2A2A] rounded-xl shadow-xl py-1 min-w-[140px]">
                                                    <a href={post.permalink_url} target="_blank" rel="noopener" className="flex items-center gap-2 px-3 py-2 text-xs text-[#D1D5DB] hover:bg-[#2A2A2A] transition-all">
                                                        <ExternalLink className="w-3.5 h-3.5" /> Apri su Facebook
                                                    </a>
                                                    <button onClick={() => deletePost(post.id)} className="w-full flex items-center gap-2 px-3 py-2 text-xs text-red-400 hover:bg-red-500/10 transition-all">
                                                        <Trash2 className="w-3.5 h-3.5" /> Elimina post
                                                    </button>
                                                </div>
                                            </>
                                        )}
                                    </div>
                                </div>

                                {/* Post Content */}
                                <div className="px-3 sm:px-4 py-2.5">
                                    <p className="text-sm text-[#E5E7EB] leading-relaxed whitespace-pre-line line-clamp-4">{post.message || post.story || ''}</p>
                                </div>

                                {/* Post Image */}
                                {post.full_picture && (
                                    <div className="mx-3 sm:mx-4 mb-3 rounded-xl overflow-hidden border border-[#1F1F1F]">
                                        <img src={post.full_picture} alt="" className="w-full max-h-80 object-cover" />
                                    </div>
                                )}

                                {/* Engagement Bar */}
                                <div className="px-3 sm:px-4 py-2.5 border-t border-[#1F1F1F] flex items-center gap-1">
                                    <div className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs text-[#9CA3AF] hover:bg-[#1A1A1A] transition-all">
                                        <Heart className={`w-4 h-4 ${reactions > 0 ? 'text-red-400' : ''}`} />
                                        <span className={reactions > 0 ? 'text-red-400 font-medium' : ''}>{formatNumber(reactions)}</span>
                                    </div>
                                    <button onClick={() => loadComments(post.id)} className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs transition-all ${selectedPost === post.id ? 'bg-[#F90100]/10 text-[#F90100]' : 'text-[#9CA3AF] hover:bg-[#1A1A1A]'}`}>
                                        <MessageSquare className="w-4 h-4" />
                                        <span className={commentCount > 0 ? 'font-medium' : ''}>{formatNumber(commentCount)}</span>
                                        <ChevronDown className={`w-3 h-3 transition-transform duration-200 ${selectedPost === post.id ? 'rotate-180' : ''}`} />
                                    </button>
                                    <a href={post.permalink_url} target="_blank" rel="noopener" className="ml-auto flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs text-[#6B7280] hover:text-white hover:bg-[#1A1A1A] transition-all">
                                        <ExternalLink className="w-3.5 h-3.5" /> <span className="hidden sm:inline">Apri</span>
                                    </a>
                                </div>

                                {/* Comments Section */}
                                {selectedPost === post.id && (
                                    <div className="border-t border-[#1F1F1F] bg-[#0A0A0A]">
                                        <div className="p-3 sm:p-4">
                                            {loadingComments ? (
                                                <div className="flex justify-center py-6"><Loader className="w-5 h-5 text-[#F90100] animate-spin" /></div>
                                            ) : comments.length === 0 ? (
                                                <p className="text-xs text-[#4A4A4A] text-center py-6">Nessun commento su questo post</p>
                                            ) : (
                                                <div className="space-y-2.5 mb-3 max-h-72 overflow-y-auto scrollbar-thin">
                                                    {comments.map((c) => (
                                                        <div key={c.id} className="flex gap-2.5">
                                                            <div className="w-7 h-7 rounded-full bg-[#1F1F1F] flex items-center justify-center shrink-0 mt-0.5">
                                                                <span className="text-[10px] font-bold text-[#9CA3AF]">{(c.from?.name || c.username || 'U')[0].toUpperCase()}</span>
                                                            </div>
                                                            <div className="flex-1 min-w-0">
                                                                <div className="bg-[#1A1A1A] rounded-xl rounded-tl-sm px-3 py-2">
                                                                    <span className="text-xs font-semibold text-white">{c.from?.name || c.username || 'Utente'}</span>
                                                                    <p className="text-xs text-[#D1D5DB] mt-0.5">{c.message || c.text}</p>
                                                                </div>
                                                                <div className="flex items-center gap-3 mt-1 px-1">
                                                                    <span className="text-[10px] text-[#4A4A4A]">{formatDate(c.created_time || c.timestamp || '')}</span>
                                                                    {(c.like_count || 0) > 0 && <span className="text-[10px] text-[#6B7280] flex items-center gap-0.5"><ThumbsUp className="w-2.5 h-2.5" />{c.like_count}</span>}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                            <div className="flex gap-2 items-end">
                                                <div className="flex-1 relative">
                                                    <input
                                                        value={replyText}
                                                        onChange={(e) => setReplyText(e.target.value)}
                                                        placeholder="Scrivi un commento..."
                                                        className="w-full bg-[#1A1A1A] border border-[#2A2A2A] text-white text-sm rounded-xl px-3.5 py-2.5 pr-10 focus:outline-none focus:border-[#F90100]/30 placeholder:text-[#4A4A4A] transition-all"
                                                        onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendReply(post.id)}
                                                    />
                                                </div>
                                                <button onClick={() => sendReply(post.id)} disabled={sending || !replyText.trim()} className="p-2.5 bg-[#F90100] text-white rounded-xl hover:bg-[#D50000] disabled:opacity-40 transition-all active:scale-95 shrink-0">
                                                    {sending ? <Loader className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )
                    })}
                </div>
            )}

            {/* Instagram Grid */}
            {tab === 'instagram' && (
                <div className="space-y-3">
                    {igMedia.length === 0 ? (
                        <div className="text-center py-16 bg-[#0F0F0F] border border-[#1F1F1F] rounded-xl">
                            <Instagram className="w-10 h-10 text-[#2A2A2A] mx-auto mb-3" />
                            <p className="text-sm text-[#6B7280]">Nessun media trovato</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                            {igMedia.map((media) => (
                                <div key={media.id} className="bg-[#0F0F0F] border border-[#1F1F1F] rounded-xl overflow-hidden hover:border-[#2A2A2A] transition-all group">
                                    {/* Media */}
                                    <div className="relative aspect-square bg-[#0A0A0A]">
                                        <img src={media.media_type === 'VIDEO' ? (media.thumbnail_url || '') : (media.media_url || '')} alt="" className="w-full h-full object-cover" />
                                        {/* Overlay on hover */}
                                        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-all flex items-center justify-center gap-6">
                                            <span className="flex items-center gap-1.5 text-white font-semibold text-sm"><Heart className="w-5 h-5" />{media.like_count || 0}</span>
                                            <span className="flex items-center gap-1.5 text-white font-semibold text-sm"><MessageSquare className="w-5 h-5" />{media.comments_count || 0}</span>
                                        </div>
                                        {/* Type badge */}
                                        <div className="absolute top-2 left-2">
                                            <span className="bg-black/60 backdrop-blur-sm text-white text-[10px] font-medium px-2 py-1 rounded-lg flex items-center gap-1">
                                                {media.media_type === 'VIDEO' ? <><Video className="w-3 h-3" />Reel</> : <><ImageIcon className="w-3 h-3" />Foto</>}
                                            </span>
                                        </div>
                                        {/* Open link */}
                                        <a href={media.permalink} target="_blank" rel="noopener" className="absolute top-2 right-2 p-1.5 bg-black/60 backdrop-blur-sm rounded-lg text-white opacity-0 group-hover:opacity-100 transition-all hover:bg-black/80">
                                            <ExternalLink className="w-3.5 h-3.5" />
                                        </a>
                                    </div>

                                    {/* Info */}
                                    <div className="p-3">
                                        <p className="text-xs text-[#D1D5DB] line-clamp-2 min-h-[2rem]">{media.caption || '(senza caption)'}</p>
                                        <div className="flex items-center justify-between mt-2.5 pt-2.5 border-t border-[#1F1F1F]">
                                            <div className="flex items-center gap-3">
                                                <span className="flex items-center gap-1 text-xs text-[#6B7280]"><Heart className={`w-3.5 h-3.5 ${(media.like_count || 0) > 0 ? 'text-red-400' : ''}`} />{media.like_count || 0}</span>
                                                <span className="flex items-center gap-1 text-xs text-[#6B7280]"><MessageSquare className="w-3.5 h-3.5" />{media.comments_count || 0}</span>
                                            </div>
                                            <span className="text-[10px] text-[#4A4A4A]">{formatDate(media.timestamp)}</span>
                                        </div>
                                        <button onClick={() => loadComments(media.id)} className="w-full mt-2 flex items-center justify-center gap-1.5 text-xs text-[#6B7280] hover:text-white py-2 bg-[#1A1A1A] hover:bg-[#2A2A2A] rounded-lg transition-all font-medium">
                                            <MessageSquare className="w-3.5 h-3.5" /> {selectedPost === media.id ? 'Chiudi' : 'Commenti'}
                                        </button>
                                    </div>

                                    {/* Comments */}
                                    {selectedPost === media.id && (
                                        <div className="border-t border-[#1F1F1F] p-3 bg-[#0A0A0A]">
                                            {loadingComments ? (
                                                <div className="flex justify-center py-4"><Loader className="w-4 h-4 text-[#F90100] animate-spin" /></div>
                                            ) : comments.length === 0 ? (
                                                <p className="text-xs text-[#4A4A4A] text-center py-4">Nessun commento</p>
                                            ) : (
                                                <div className="space-y-2 mb-3 max-h-48 overflow-y-auto">
                                                    {comments.map((c: any) => (
                                                        <div key={c.id} className="flex gap-2">
                                                            <div className="w-6 h-6 rounded-full bg-[#1F1F1F] flex items-center justify-center shrink-0">
                                                                <span className="text-[9px] font-bold text-[#9CA3AF]">{(c.username || c.from?.name || 'U')[0].toUpperCase()}</span>
                                                            </div>
                                                            <div className="flex-1 min-w-0">
                                                                <div className="bg-[#1A1A1A] rounded-lg rounded-tl-sm px-2.5 py-1.5">
                                                                    <span className="text-[10px] font-semibold text-white">{c.username || c.from?.name || 'Utente'}</span>
                                                                    <p className="text-[11px] text-[#D1D5DB]">{c.text || c.message}</p>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                            <div className="flex gap-2">
                                                <input
                                                    value={replyText}
                                                    onChange={(e) => setReplyText(e.target.value)}
                                                    placeholder="Rispondi..."
                                                    className="flex-1 bg-[#1A1A1A] border border-[#2A2A2A] text-white text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-[#F90100]/30 transition-all"
                                                    onKeyDown={(e) => e.key === 'Enter' && sendReply(media.id)}
                                                />
                                                <button onClick={() => sendReply(media.id)} disabled={sending || !replyText.trim()} className="p-2 bg-[#F90100] text-white rounded-lg disabled:opacity-40 transition-all active:scale-95">
                                                    <Send className="w-3.5 h-3.5" />
                                                </button>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
