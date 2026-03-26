import { NextRequest, NextResponse } from 'next/server'

const FB_APP_ID = process.env.FB_APP_ID || '854572453816993'
const FB_APP_SECRET = process.env.FB_APP_SECRET || ''

export async function POST(request: NextRequest) {
    try {
        const { shortLivedToken, userID } = await request.json()

        if (!shortLivedToken) {
            return NextResponse.json({ error: 'Missing token' }, { status: 400 })
        }

        if (!FB_APP_SECRET) {
            return NextResponse.json({
                accessToken: shortLivedToken,
                tokenType: 'short_lived',
                note: 'App Secret not configured'
            })
        }

        const url = `https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=${FB_APP_ID}&client_secret=${FB_APP_SECRET}&fb_exchange_token=${shortLivedToken}`

        const res = await fetch(url)
        const data = await res.json()

        if (data.error) {
            console.error('Token exchange error:', data.error)
            return NextResponse.json({
                accessToken: shortLivedToken,
                tokenType: 'short_lived',
                exchangeError: data.error.message
            })
        }

        return NextResponse.json({
            accessToken: data.access_token,
            tokenType: 'long_lived',
            expiresIn: data.expires_in
        })
    } catch (error) {
        console.error('Exchange token error:', error)
        return NextResponse.json({ error: 'Internal error' }, { status: 500 })
    }
}
