import type { Metadata } from 'next'
import { Playfair_Display, Source_Serif_4, Golos_Text } from 'next/font/google'
import Analytics from '@/components/Analytics'
import './globals.css'

const display = Playfair_Display({
    subsets: ['latin', 'cyrillic'],
    weight: ['400', '500', '600', '700', '800', '900'],
    style: ['normal', 'italic'],
    variable: '--font-display',
    display: 'swap',
})

const body = Source_Serif_4({
    subsets: ['latin', 'cyrillic'],
    weight: ['300', '400', '500', '600'],
    style: ['normal', 'italic'],
    variable: '--font-body',
    display: 'swap',
})

const nav = Golos_Text({
    subsets: ['latin', 'cyrillic'],
    weight: ['400', '500', '600', '700'],
    variable: '--font-nav',
    display: 'swap',
})

const SITE_URL = 'https://avto-vykup86.ru'
const SITE_NAME = 'PRODAYAUTO86'
const DESCRIPTION =
    'Профессиональный выкуп автомобилей в Сургуте и ХМАО-ЯНАО. Выкупаем авто в любом состоянии – до 90% рыночной стоимости. Расчёт наличными в день обращения.'

export const metadata: Metadata = {
    metadataBase: new URL(SITE_URL),
    title: SITE_NAME,
    description: DESCRIPTION,
    keywords: [
        'выкуп авто',
        'выкуп автомобилей',
        'срочный выкуп авто',
        'выкуп авто Сургут',
        'выкуп авто ХМАО',
        'выкуп авто ЯНАО',
        'продать авто быстро',
        'выкуп авто после ДТП',
        'выкуп кредитных авто',
        'PRODAYAUTO86',
    ],
    applicationName: SITE_NAME,
    category: 'business',
    alternates: {
        canonical: '/',
    },
    openGraph: {
        type: 'website',
        locale: 'ru_RU',
        url: SITE_URL,
        siteName: SITE_NAME,
        title: SITE_NAME,
        description: DESCRIPTION,
        images: [
            {
                url: '/logo.jpg',
                width: 1024,
                height: 1024,
                alt: SITE_NAME,
            },
        ],
    },
    twitter: {
        card: 'summary_large_image',
        title: SITE_NAME,
        description: DESCRIPTION,
        images: ['/logo.jpg'],
    },
    robots: {
        index: true,
        follow: true,
        googleBot: {
            index: true,
            follow: true,
            'max-image-preview': 'large',
        },
    },
    formatDetection: {
        telephone: true,
    },
    verification: {
        // Google Search Console → Настройки → Проверка прав → тег HTML
        google: process.env.NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION,
        other: process.env.NEXT_PUBLIC_YANDEX_VERIFICATION
            ? { 'yandex-verification': process.env.NEXT_PUBLIC_YANDEX_VERIFICATION }
            : undefined,
    },
}

const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'AutomotiveBusiness',
    name: SITE_NAME,
    description: DESCRIPTION,
    url: SITE_URL,
    image: `${SITE_URL}/logo.jpg`,
    telephone: '+7-000-000-00-00',
    priceRange: '₽₽',
    address: {
        '@type': 'PostalAddress',
        addressLocality: 'Сургут',
        addressRegion: 'ХМАО-Югра',
        addressCountry: 'RU',
    },
    areaServed: ['Сургут', 'ХМАО-Югра', 'ЯНАО'],
    sameAs: [
        'https://t.me/your_channel',
        'https://www.instagram.com/your_account',
        'https://vk.com/your_group',
    ],
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang='ru' className={`${display.variable} ${body.variable} ${nav.variable}`}>
            <head>
                <meta name='theme-color' content='#000000' />
                <script
                    type='application/ld+json'
                    dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
                />
            </head>
            <body>
                <Analytics />
                {children}
            </body>
        </html>
    )
}
