'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
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
    Fingerprint
} from 'lucide-react'

const menuItems = [
    { href: '/', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/leads', label: 'Lead Pipeline', icon: Users },
    { href: '/diagnosi', label: 'Diagnosi', icon: FileText },
    { href: '/pagamenti', label: 'Pagamenti', icon: CreditCard },
    { href: '/revenue', label: 'Revenue', icon: TrendingUp },
    { href: '/provincie', label: 'Mappa Provincie', icon: MapPin },
    { href: '/costi-ai', label: 'Costi AI', icon: Cpu },
    { href: '/impostazioni', label: 'Impostazioni', icon: Settings },
]

export default function Sidebar() {
    const pathname = usePathname()
    const router = useRouter()

    const handleLogout = async () => {
        document.cookie = 'admin_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT'
        router.push('/login')
        router.refresh()
    }

    return (
        <aside className="fixed left-0 top-0 h-full w-64 bg-[#0A0A0A] border-r border-[#1F1F1F] flex flex-col z-50">
            <div className="p-6 border-b border-[#1F1F1F]">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-[#F90100] flex items-center justify-center shadow-lg shadow-[#F90100]/20">
                        <Fingerprint className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <h1 className="text-lg font-bold text-white tracking-tight">DigIdentity</h1>
                        <p className="text-xs text-[#6B7280]">Engine Dashboard</p>
                    </div>
                </div>
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
        </aside>
    )
}
