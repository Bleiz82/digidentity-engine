import { NextRequest, NextResponse } from 'next/server'
import { validateToken } from '@/lib/auth'

const API_URL = process.env.INTERNAL_API_URL || 'http://digidentity-backend:8080'
const INTERNAL_KEY = process.env.INTERNAL_API_KEY || 'dIgId_int3rn4L_X9kM2pV7nQ4wL6jR8'

export async function POST(request: NextRequest) {
    // Verifica autenticazione dashboard
    const token = request.cookies.get('admin_token')?.value
    if (!token || !validateToken(token)) {
        return NextResponse.json({ error: 'Non autorizzato' }, { status: 401 })
    }

    try {
        const body = await request.json()
        const { action, lead_id, url_sito, email } = body

        let endpoint = ''
        let payload: any = {}

        switch (action) {
            case 'premium':
                endpoint = '/api/payment/internal/genera-premium'
                payload = { lead_id }
                break
            case 'free':
                endpoint = '/api/payment/internal/genera-free'
                payload = { lead_id }
                break
            case 'geo':
                endpoint = '/api/payment/internal/genera-geo'
                payload = { url_sito: url_sito || '', email: email || 'digidentityagency@gmail.com' }
                break
            default:
                return NextResponse.json({ error: 'Azione non valida' }, { status: 400 })
        }

        const res = await fetch(`${API_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Internal-Key': INTERNAL_KEY,
            },
            body: JSON.stringify(payload),
        })

        const data = await res.json()
        if (!res.ok) {
            return NextResponse.json({ error: data.detail || 'Errore backend' }, { status: res.status })
        }

        return NextResponse.json(data)
    } catch (error: any) {
        return NextResponse.json({ error: error.message || 'Errore server' }, { status: 500 })
    }
}
