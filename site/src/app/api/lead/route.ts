import { NextResponse } from 'next/server'

export async function POST(request: Request) {
    const token = process.env.TELEGRAM_BOT_TOKEN
    const chatId = process.env.TELEGRAM_CHAT_ID

    if (!token || !chatId) {
        console.error('TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID is not set')
        return NextResponse.json({ error: 'server not configured' }, { status: 500 })
    }

    let body: { brand?: string; model?: string; year?: string; mileage?: string; phone?: string }
    try {
        body = await request.json()
    } catch {
        return NextResponse.json({ error: 'invalid body' }, { status: 400 })
    }

    const phone = (body.phone || '').trim()
    if (!phone) {
        return NextResponse.json({ error: 'phone is required' }, { status: 400 })
    }

    const lines = [
        'Новая заявка с сайта Proday Auto 86',
        '',
        `Марка: ${body.brand?.trim() || '—'}`,
        `Модель: ${body.model?.trim() || '—'}`,
        `Год: ${body.year?.trim() || '—'}`,
        `Пробег: ${body.mileage?.trim() || '—'} км`,
        `Телефон: ${phone}`,
    ]

    const res = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            chat_id: chatId,
            text: lines.join('\n'),
        }),
    })

    if (!res.ok) {
        const errText = await res.text()
        console.error('Telegram sendMessage failed:', errText)
        return NextResponse.json({ error: 'telegram request failed' }, { status: 502 })
    }

    return NextResponse.json({ ok: true })
}
