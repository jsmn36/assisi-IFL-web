const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
      },
    ],
    // Images are sourced from Unsplash CDN which handles its own optimization.
    // Disabling Next.js image optimization avoids proxy 404s in restricted networks.
    unoptimized: true,
  },
};

export default nextConfig;
