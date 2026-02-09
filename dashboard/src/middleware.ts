import { NextRequest, NextResponse } from 'next/server'

export function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl

    // Non proteggere login e API auth
    if (pathname === '/login' || pathname === '/api/auth') {
        return NextResponse.next()
    }

    // Controlla token
    const token = request.cookies.get('admin_token')?.value

    if (!token) {
        return NextResponse.redirect(new URL('/login', request.url))
    }

    // Validazione base del token (decodifica e check scadenza)
    try {
        const decoded = Buffer.from(token, 'base64').toString('utf-8')
        const parts = decoded.split(':')
        if (parts.length < 3) {
            return NextResponse.redirect(new URL('/login', request.url))
        }
        const timestamp = parseInt(parts[1])
        const now = Date.now()
        const maxAge = 24 * 60 * 60 * 1000
        if ((now - timestamp) >= maxAge) {
            return NextResponse.redirect(new URL('/login', request.url))
        }
    } catch {
        return NextResponse.redirect(new URL('/login', request.url))
    }

    return NextResponse.next()
}

export const config = {
    matcher: ['/((?!_next/static|_next/image|favicon.ico|login|api/auth).*)']
}
