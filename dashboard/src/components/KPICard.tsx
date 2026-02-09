import { LucideIcon } from 'lucide-react'

interface KPICardProps {
    title: string
    value: string | number
    subtitle?: string
    icon: LucideIcon
    trend?: 'up' | 'down' | 'neutral'
    trendValue?: string
    color?: 'red' | 'green' | 'blue' | 'error' | 'purple' | 'yellow'
}

const iconColorMap = {
    red: '#F90100',
    green: '#10b981',
    blue: '#3b82f6',
    error: '#ef4444',
    purple: '#a855f7',
    yellow: '#eab308',
}

const bgColorMap = {
    red: 'bg-[#F90100]/10 border-[#F90100]/20',
    green: 'bg-emerald-500/10 border-emerald-500/20',
    blue: 'bg-blue-500/10 border-blue-500/20',
    error: 'bg-red-500/10 border-red-500/20',
    purple: 'bg-purple-500/10 border-purple-500/20',
    yellow: 'bg-yellow-500/10 border-yellow-500/20',
}

export default function KPICard({ title, value, subtitle, icon: Icon, trend, trendValue, color = 'red' }: KPICardProps) {
    return (
        <div className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-2xl p-6 hover:border-[#333333] transition-all duration-300 group">
            <div className="flex items-start justify-between mb-4">
                <div className={`w-12 h-12 rounded-xl ${bgColorMap[color]} border flex items-center justify-center group-hover:scale-110 transition-transform duration-300`}>
                    <Icon className="w-6 h-6" style={{ color: iconColorMap[color] }} />
                </div>
                {trend && trendValue && (
                    <span className={`text-xs font-medium px-2 py-1 rounded-lg ${trend === 'up' ? 'bg-emerald-500/10 text-emerald-400' :
                            trend === 'down' ? 'bg-red-500/10 text-red-400' :
                                'bg-[#1F1F1F] text-[#9CA3AF]'
                        }`}>
                        {trend === 'up' ? '+' : trend === 'down' ? '-' : ''}{trendValue}
                    </span>
                )}
            </div>
            <p className="text-3xl font-bold text-white mb-1">{value}</p>
            <p className="text-sm text-[#9CA3AF]">{title}</p>
            {subtitle && <p className="text-xs text-[#6B7280] mt-1">{subtitle}</p>}
        </div>
    )
}
