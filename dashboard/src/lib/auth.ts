export function validateCredentials(username: string, password: string): boolean {
    const validUsername = process.env.ADMIN_USERNAME || 'stefano'
    const validPassword = process.env.ADMIN_PASSWORD || 'DigIdentity2026!'
    return username === validUsername && password === validPassword
}

export function generateToken(username: string): string {
    const secret = process.env.NEXTAUTH_SECRET || 'fallback-secret'
    const payload = `${username}:${Date.now()}:${secret}`
    return Buffer.from(payload).toString('base64')
}

export function validateToken(token: string): boolean {
    try {
        const decoded = Buffer.from(token, 'base64').toString('utf-8')
        const parts = decoded.split(':')
        if (parts.length < 3) return false
        const timestamp = parseInt(parts[1])
        const now = Date.now()
        const maxAge = 24 * 60 * 60 * 1000 // 24 ore
        return (now - timestamp) < maxAge
    } catch {
        return false
    }
}
