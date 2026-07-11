import React from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { Section } from '@/components/ui/Section';

export const AboutHome = () => {
  return (
    <Section background="white">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
        <div className="relative aspect-square md:aspect-[4/3] rounded-3xl overflow-hidden shadow-2xl">
          <Image
            src="https://images.unsplash.com/photo-1540331547168-8b6310f62424?q=80&w=1200"
            alt="Le Vagas Aerial View"
            fill
            className="object-cover"
          />
        </div>
        <div className="flex flex-col gap-8">
          <div className="flex flex-col gap-2">
            <span className="tagline text-brand-forest-green uppercase tracking-widest text-sm font-bold">Welcome to Tranquility</span>
            <h2 className="text-4xl md:text-5xl font-heading leading-tight">Escape to the misty heart of Vagamon</h2>
          </div>
          <div className="flex flex-col gap-4 text-brand-charcoal/80 leading-relaxed text-lg">
            <p>
              Hidden among the serene hills of Vagamon, Le Vagas is designed for travelers seeking tranquility and natural beauty. Our property blends modern luxury with the raw charm of nature, offering guests breathtaking valley views, private cottages, and unforgettable experiences.
            </p>
            <p>
              Whether you are planning a romantic getaway, a honeymoon escape, or a peaceful family vacation, Le Vagas promises a stay filled with relaxation, comfort, and scenic beauty.
            </p>
          </div>
          <Link href="/about" className="text-brand-forest-green font-bold flex items-center gap-2 group hover:gap-4 transition-all">
            Read Our Full Story <span className="text-xl">→</span>
          </Link>
        </div>
      </div>
    </Section>
  );
};
