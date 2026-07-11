import React from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { Section } from '@/components/ui/Section';
import { Card, CardContent, CardFooter } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { cottages } from '@/data/cottages';

export const FeaturedCottages = () => {
  // Show only 3 featured cottages as per PRD
  const featured = cottages.filter(c => 
    ['mist-valley', 'emerald-hills', 'celeste-honeymoon-villa'].includes(c.slug)
  );

  return (
    <Section background="primary">
      <div className="text-center max-w-3xl mx-auto mb-16 flex flex-col gap-4">
        <h2 className="text-4xl md:text-5xl font-heading">Luxury Private Cottages</h2>
        <p className="text-brand-charcoal/70 text-lg">
          Each cottage thoughtfully designed to provide privacy, comfort, and panoramic views of the surrounding hills.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {featured.map((cottage) => (
          <Card key={cottage.slug} className="group h-full flex flex-col">
            <div className="relative aspect-[4/3] overflow-hidden">
              <Image
                src={cottage.images.hero}
                alt={cottage.name}
                fill
                className="object-cover group-hover:scale-110 transition-transform duration-700"
              />
              {cottage.slug === 'celeste-honeymoon-villa' && (
                <div className="absolute top-4 right-4 bg-brand-gold text-brand-charcoal text-[10px] font-bold uppercase tracking-widest px-3 py-1.5 rounded-full shadow-lg">
                  🤍 Honeymoon Special
                </div>
              )}
              {cottage.slug === 'mist-valley' && (
                <div className="absolute top-4 right-4 bg-brand-forest-green text-white text-[10px] font-bold uppercase tracking-widest px-3 py-1.5 rounded-full shadow-lg">
                  Most Popular
                </div>
              )}
            </div>
            <CardContent className="flex flex-col gap-4 pt-6 flex-grow">
              <h3 className="text-2xl font-heading">{cottage.name}</h3>
              <p className="text-brand-charcoal/70 text-sm line-clamp-2">
                {cottage.description}
              </p>
              <ul className="flex flex-wrap gap-x-4 gap-y-2">
                {cottage.features.slice(0, 4).map((feature, i) => (
                  <li key={i} className="text-xs font-medium text-brand-charcoal/80 bg-brand-forest-green/5 px-2 py-1 rounded">
                    {feature}
                  </li>
                ))}
              </ul>
            </CardContent>
            <CardFooter className="flex justify-between items-center border-t border-brand-forest-green/5 pt-6 bg-brand-forest-green/[0.02]">
              <div className="flex flex-col">
                <span className="text-[10px] font-bold uppercase tracking-widest text-brand-warm-gray">From</span>
                <span className="text-xl font-bold text-brand-forest-green italic">₹{cottage.priceFrom.toLocaleString()}<span className="text-xs font-normal">/night</span></span>
              </div>
              <Link href={`/cottages/${cottage.slug}`}>
                <Button variant="secondary" className="px-4 py-2 text-sm">View Details</Button>
              </Link>
            </CardFooter>
          </Card>
        ))}
      </div>

      <div className="mt-16 text-center">
        <Link href="/cottages">
          <Button variant="ghost" className="text-lg gap-2 group">
            Explore All 5 Cottages <span className="group-hover:translate-x-1 transition-transform">→</span>
          </Button>
        </Link>
      </div>
    </Section>
  );
};
