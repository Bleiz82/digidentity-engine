import { NextRequest, NextResponse } from 'next/server'
import { validateCredentials, generateToken } from '@/lib/auth'

export async function POST(request: NextRequest) {
    try {
        const { username, password } = await request.json()

        if (!username || !password) {
            return NextResponse.json(
                { error: 'Credenziali mancanti' },
                { status: 400 }
            )
        }

        if (!validateCredentials(username, password)) {
            return NextResponse.json(
                { error: 'Credenziali non valide' },
                { status: 401 }
            )
        }

        const token = generateToken(username)

        const response = NextResponse.json({ success: true })
        response.cookies.set('admin_token', token, {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'strict',
            maxAge: 86400, // 24 ore
            path: '/'
        })

        return response
    } catch {
        return NextResponse.json(
            { error: 'Errore server' },
            { status: 500 }
        )
    }
}
