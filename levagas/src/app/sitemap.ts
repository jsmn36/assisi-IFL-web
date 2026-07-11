import { MetadataRoute } from 'next';
import { cottages } from '@/data/cottages';

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = 'https://levagas.com';
  
  const staticPages = [
    '',
    '/cottages',
    '/dining',
    '/wellness',
    '/experiences',
    '/gallery',
    '/about',
    '/contact',
    '/booking-lookup',
  ].map(route => ({
    url: `${baseUrl}${route}`,
    lastModified: new Date(),
    changeFrequency: 'monthly' as const,
    priority: route === '' ? 1 : 0.8,
  }));

  const cottagePages = cottages.map(c => ({
    url: `${baseUrl}/cottages/${c.slug}`,
    lastModified: new Date(),
    changeFrequency: 'monthly' as const,
    priority: 0.9,
  }));

  return [...staticPages, ...cottagePages];
}
