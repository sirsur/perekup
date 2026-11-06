import type { MetadataRoute } from 'next'

export default function sitemap(): MetadataRoute.Sitemap {
    return [
        {
            url: 'https://avto-vykup86.ru',
            lastModified: new Date(),
            changeFrequency: 'weekly',
            priority: 1,
        },
    ]
}
