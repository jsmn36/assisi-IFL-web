import React from 'react';
import Link from 'next/link';
import { Section } from '@/components/ui/Section';
import { Button } from '@/components/ui/Button';
import { PROPERTY_INFO } from '@/lib/constants';

export const FinalCTA = () => {
  return (
    <Section background="forest" className="relative overflow-hidden py-32 md:py-48">
      {/* Decorative Elements */}
      <div className="absolute top-0 left-0 w-64 h-64 bg-white/5 rounded-full -translate-x-1/2 -translate-y-1/2 blur-3xl" />
      <div className="absolute bottom-0 right-0 w-96 h-96 bg-brand-gold/10 rounded-full translate-x-1/3 translate-y-1/3 blur-3xl" />

      <div className="relative z-10 text-center max-w-4xl mx-auto flex flex-col gap-12">
        <div className="flex flex-col gap-6">
          <span className="tagline text-white uppercase tracking-[0.3em] text-sm font-bold">Your Escape Awaits</span>
          <h2 className="text-5xl md:text-7xl font-heading leading-tight text-white italic">
            Ready to experience tranquility?
          </h2>
          <p className="text-white/95 text-xl md:text-2xl font-light">
            Discover where the hills whisper peace. Book your stay at Le Vagas and reconnect with nature in the most luxurious way.
          </p>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-6 justify-center items-center">
          <Link href="/book" className="w-full sm:w-auto">
            <Button variant="cta-large" className="w-full bg-brand-gold border-brand-gold hover:bg-brand-gold/90 text-brand-charcoal px-12 py-5 text-xl">
              Book Your Escape
            </Button>
          </Link>
          <Link href={`tel:${PROPERTY_INFO.phone.replace(/\s/g, '')}`} className="w-full sm:w-auto font-bold text-white hover:text-brand-gold transition-colors flex items-center gap-3 text-lg border-2 border-white/20 px-8 py-4 rounded-md hover:border-brand-gold/50">
            📞 Call Us: {PROPERTY_INFO.phone}
          </Link>
        </div>
      </div>
    </Section>
  );
};
