'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useState, useEffect } from 'react'
import {
    LayoutDashboard,
    Users,
    FileText,
    CreditCard,
    TrendingUp,
    MapPin,
    Cpu,
    Settings,
    LogOut,
    Fingerprint,
    Globe,
    MessageSquare,
    Contact,
    CalendarDays,
    Menu,
    X,
    Share2,
    FileEdit,
    Building2
} from 'lucide-react'

const menuItems = [
    { href: '/', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/leads', label: 'Lead Pipeline', icon: Users },
    { href: '/diagnosi', label: 'Diagnosi', icon: FileText },
    { href: '/geo-audits', label: 'GEO Audits', icon: Globe },
    { href: '/pagamenti', label: 'Pagamenti', icon: CreditCard },
    { href: '/revenue', label: 'Revenue', icon: TrendingUp },
    { href: '/provincie', label: 'Mappa Provincie', icon: MapPin },
    { href: '/costi-ai', label: 'Costi AI', icon: Cpu },
    { href: '/impostazioni', label: 'Impostazioni', icon: Settings },
]

const agentMenuItems = [
    { href: '/inbox', label: 'Inbox', icon: MessageSquare },
    { href: '/contatti', label: 'Contatti Agent', icon: Contact },
    { href: '/calendario', label: 'Calendario', icon: CalendarDays },
]

const socialMenuItems = [
    { href: '/social', label: 'Social Manager', icon: Share2 },
    { href: '/templates', label: 'Templates', icon: FileEdit },
    { href: '/business', label: 'Business', icon: Building2 },
]

export default function Sidebar() {
    const pathname = usePathname()
    const router = useRouter()
    const [open, setOpen] = useState(false)

    useEffect(() => { setOpen(false) }, [pathname])
    useEffect(() => {
        document.body.style.overflow = open ? 'hidden' : ''
        return () => { document.body.style.overflow = '' }
    }, [open])

    const handleLogout = async () => {
        document.cookie = 'admin_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT'
        router.push('/login')
        router.refresh()
    }

    const renderSection = (title: string, items: typeof menuItems) => (
        <>
            <div className="pt-4 pb-2 px-4">
                <p className="text-xs font-semibold text-[#F90100] uppercase tracking-wider">{title}</p>
            </div>
            {items.map((item) => {
                const isActive = pathname === item.href || pathname?.startsWith(item.href + '/')
                const Icon = item.icon
                return (
                    <Link
                        key={item.href}
                        href={item.href}
                        className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${isActive
                            ? 'bg-[#F90100]/10 text-[#F90100] border border-[#F90100]/30'
                            : 'text-[#9CA3AF] hover:text-white hover:bg-[#1F1F1F]'
                        }`}
                    >
                        <Icon className="w-5 h-5" />
                        {item.label}
                    </Link>
                )
            })}
        </>
    )

    const sidebarContent = (
        <>
            <div className="p-6 border-b border-[#1F1F1F] flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-[#F90100] flex items-center justify-center shadow-lg shadow-[#F90100]/20">
                        <Fingerprint className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <h1 className="text-lg font-bold text-white tracking-tight">DigIdentity</h1>
                        <p className="text-xs text-[#6B7280]">Engine Dashboard</p>
                    </div>
                </div>
                <button onClick={() => setOpen(false)} className="lg:hidden text-[#9CA3AF] hover:text-white p-1">
                    <X className="w-6 h-6" />
                </button>
            </div>

            <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
                {menuItems.map((item) => {
                    const isActive = pathname === item.href
                    const Icon = item.icon
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${isActive
                                ? 'bg-[#F90100]/10 text-[#F90100] border border-[#F90100]/30'
                                : 'text-[#9CA3AF] hover:text-white hover:bg-[#1F1F1F]'
                            }`}
                        >
                            <Icon className="w-5 h-5" />
                            {item.label}
                        </Link>
                    )
                })}

                {renderSection('Digy Agent', agentMenuItems)}
                {renderSection('Social & Marketing', socialMenuItems)}
            </nav>

            <div className="p-4 border-t border-[#1F1F1F]">
                <div className="flex items-center gap-3 px-4 py-2 mb-3">
                    <div className="w-8 h-8 rounded-full bg-[#F90100] flex items-center justify-center">
                        <span className="text-xs font-bold text-white">S</span>
                    </div>
                    <div>
                        <p className="text-sm font-medium text-white">Stefano</p>
                        <p className="text-xs text-[#6B7280]">Amministratore</p>
                    </div>
                </div>
                <button
                    onClick={handleLogout}
                    className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-[#9CA3AF] hover:text-[#F90100] hover:bg-[#F90100]/10 transition-all duration-200 w-full"
                >
                    <LogOut className="w-5 h-5" />
                    Esci
                </button>
            </div>
        </>
    )

    return (
        <>
            <button
                onClick={() => setOpen(true)}
                className="lg:hidden fixed top-4 left-4 z-[60] bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl p-2 text-white shadow-lg"
            >
                <Menu className="w-6 h-6" />
            </button>
            {open && (
                <div
                    className="lg:hidden fixed inset-0 bg-black/60 z-[70] backdrop-blur-sm"
                    onClick={() => setOpen(false)}
                />
            )}
            <aside className={`lg:hidden fixed left-0 top-0 h-full w-72 bg-[#0A0A0A] border-r border-[#1F1F1F] flex flex-col z-[80] transform transition-transform duration-300 ${open ? 'translate-x-0' : '-translate-x-full'}`}>
                {sidebarContent}
            </aside>
            <aside className="hidden lg:flex fixed left-0 top-0 h-full w-64 bg-[#0A0A0A] border-r border-[#1F1F1F] flex-col z-50">
                {sidebarContent}
            </aside>
        </>
    )
}
