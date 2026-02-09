'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Fingerprint, Eye, EyeOff } from 'lucide-react'

export default function LoginPage() {
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [showPassword, setShowPassword] = useState(false)
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const router = useRouter()

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')
        setLoading(true)

        try {
            const res = await fetch('/api/auth', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            })

            if (res.ok) {
                router.push('/')
                router.refresh()
            } else {
                const data = await res.json()
                setError(data.error || 'Credenziali non valide')
            }
        } catch {
            setError('Errore di connessione')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-black flex items-center justify-center p-4">
            <div className="w-full max-w-md">
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-[#F90100] mb-6 shadow-2xl shadow-[#F90100]/30">
                        <Fingerprint className="w-10 h-10 text-white" />
                    </div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">DigIdentity</h1>
                    <p className="text-[#9CA3AF] mt-2">Dashboard Amministrazione</p>
                </div>

                <form onSubmit={handleSubmit} className="bg-[#0A0A0A] border border-[#1F1F1F] rounded-2xl p-8 space-y-6">
                    {error && (
                        <div className="bg-[#F90100]/10 border border-[#F90100]/30 rounded-xl p-4 text-[#F90100] text-sm text-center font-medium">
                            {error}
                        </div>
                    )}

                    <div>
                        <label className="block text-sm font-medium text-[#9CA3AF] mb-2">Username</label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="w-full px-4 py-3 bg-black border border-[#1F1F1F] rounded-xl text-white placeholder-[#6B7280] focus:outline-none focus:ring-2 focus:ring-[#F90100]/50 focus:border-[#F90100]/50 transition-all"
                            placeholder="Inserisci username"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-[#9CA3AF] mb-2">Password</label>
                        <div className="relative">
                            <input
                                type={showPassword ? 'text' : 'password'}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full px-4 py-3 bg-black border border-[#1F1F1F] rounded-xl text-white placeholder-[#6B7280] focus:outline-none focus:ring-2 focus:ring-[#F90100]/50 focus:border-[#F90100]/50 transition-all pr-12"
                                placeholder="Inserisci password"
                                required
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-4 top-1/2 -translate-y-1/2 text-[#6B7280] hover:text-white transition-colors"
                            >
                                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                            </button>
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full py-3.5 bg-[#F90100] hover:bg-[#d40100] text-white font-semibold rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-[#F90100]/20 hover:shadow-[#F90100]/40"
                    >
                        {loading ? 'Accesso in corso...' : 'Accedi alla Dashboard'}
                    </button>
                </form>

                <p className="text-center text-[#6B7280] text-xs mt-8">
                    DigIdentity Engine v1.0 — Dashboard Admin
                </p>
            </div>
        </div>
    )
}
