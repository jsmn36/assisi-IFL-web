import { MetadataRoute } from 'next';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
      disallow: ['/api/', '/confirmation', '/checkout'],
    },
    sitemap: 'https://levagas.com/sitemap.xml',
  };
}
