import React from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { Section } from '@/components/ui/Section';
import { Card, CardContent, CardFooter } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { BookingWidget } from '@/components/booking/BookingWidget';
import { cottages } from '@/data/cottages';

export const metadata = {
  title: 'Luxury Private Cottages',
  description: 'Explore our 5 unique boutique cottages in Vagamon, each offering breathtaking views and modern luxury.',
};

export default function CottagesPage() {
  return (
    <div className="pt-20">
      {/* Sticky Availability Bar */}
      <div className="sticky top-16 md:top-[72px] z-30 bg-brand-primary-bg/80 backdrop-blur-md border-b border-brand-forest-green/10 py-4 shadow-sm">
        <div className="max-w-7xl mx-auto px-6">
          <BookingWidget className="shadow-none border-none bg-transparent p-0" />
        </div>
      </div>

      <Section background="white">
        <div className="flex flex-col gap-12">
          <div className="max-w-3xl">
            <h1 className="text-5xl md:text-6xl font-heading mb-6 tracking-tight">Our Luxury Private Cottages</h1>
            <p className="text-lg text-brand-charcoal/70 leading-relaxed font-light">
              Each cottage at Le Vagas is a sanctuary designed to provide the ultimate in privacy, comfort, and panoramic views of the surrounding hills and misty valleys.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-16">
            {cottages.map((cottage) => (
              <Card key={cottage.slug} className="group border-none shadow-none bg-transparent overflow-visible">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
                  {/* Left: Image Stack */}
                  <div className="flex flex-col gap-4">
                    <div className="relative aspect-[16/10] rounded-2xl overflow-hidden shadow-2xl group-hover:-translate-y-1 transition-transform duration-500">
                      <Image
                        src={cottage.images.hero}
                        alt={cottage.name}
                        fill
                        className="object-cover"
                      />
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                      {cottage.images.gallery.slice(0, 3).map((img, i) => (
                        <div key={i} className="relative aspect-square rounded-xl overflow-hidden shadow-md group-hover:scale-105 transition-transform duration-500" style={{ transitionDelay: `${i * 100}ms` }}>
                          <Image src={img} alt={`${cottage.name} gallery ${i}`} fill className="object-cover" />
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Right: Info */}
                  <div className="flex flex-col gap-8 lg:pt-4">
                    <div className="flex flex-col gap-2">
                      <div className="flex justify-between items-start">
                        <h2 className="text-3xl md:text-4xl font-heading">{cottage.name}</h2>
                        <div className="text-right">
                          <span className="text-[10px] font-bold uppercase tracking-widest text-brand-warm-gray block">Starting from</span>
                          <span className="text-2xl font-bold text-brand-forest-green italic">₹{cottage.priceFrom.toLocaleString()}</span>
                        </div>
                      </div>
                      <p className="text-brand-charcoal/70 leading-relaxed">
                        {cottage.description}
                      </p>
                    </div>

                    <div className="grid grid-cols-2 gap-y-4 gap-x-8">
                      {cottage.features.map((feature, i) => (
                        <div key={i} className="flex items-center gap-2 text-sm text-brand-charcoal/80 font-medium">
                          {feature}
                        </div>
                      ))}
                    </div>

                    <div className="flex flex-col gap-4 border-t border-brand-forest-green/10 pt-8">
                      <h4 className="text-xs font-bold uppercase tracking-widest text-brand-forest-green">Key Amenities</h4>
                      <ul className="grid grid-cols-2 gap-2">
                        {cottage.amenities.slice(0, 6).map((amenity, i) => (
                          <li key={i} className="text-xs text-brand-charcoal/80 flex items-center gap-2">
                            <span className="w-1 h-1 bg-brand-gold rounded-full" /> {amenity}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="flex gap-4 pt-4">
                      <Link href={`/cottages/${cottage.slug}`} className="flex-grow">
                        <Button variant="primary" className="w-full py-4 text-base">View Full Details</Button>
                      </Link>
                      <Button variant="secondary" className="px-8">Check Availability</Button>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </Section>
    </div>
  );
}
