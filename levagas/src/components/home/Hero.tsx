import React from 'react';
import Image from 'next/image';
import { BookingWidget } from '@/components/booking/BookingWidget';
import { PROPERTY_INFO } from '@/lib/constants';

export const Hero = () => {
  return (
    <section className="relative h-screen w-full flex items-center justify-center overflow-hidden">
      {/* Background Image */}
      <div className="absolute inset-0 z-0 bg-brand-forest-green/20">
        <Image
          src="https://images.unsplash.com/photo-1542401886-65d6c60db275?q=80&w=1600"
          alt="Le Vagas Resort - Mist Valley Morning"
          fill
          priority
          className="object-cover object-center"
        />
        <div className="absolute inset-0 bg-brand-charcoal/30 flex flex-col items-center justify-center text-center px-6">
          <div className="max-w-4xl animate-in fade-in zoom-in duration-1000">
            <h2 className="tagline text-white text-lg md:text-xl mb-4 drop-shadow-lg">
              {PROPERTY_INFO.tagline}
            </h2>
            <h1 className="text-5xl md:text-7xl lg:text-8xl text-white font-heading mb-6 drop-shadow-2xl">
              Where the Hills Whisper Peace
            </h1>
            <p className="text-white/90 text-xl md:text-2xl max-w-2xl mx-auto mb-12 drop-shadow-lg font-light">
              Experience the perfect blend of luxury and nature in a boutique hill retreat nestled in the misty landscapes of Vagamon.
            </p>
          </div>
        </div>
      </div>

      {/* Floating Booking Widget */}
      <div className="absolute bottom-12 left-6 right-6 z-10 max-w-6xl mx-auto">
        <BookingWidget />
      </div>

      {/* Scroll Indicator */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-white animate-bounce cursor-pointer">
        <span className="text-[10px] uppercase tracking-[0.3em] font-bold">Discover</span>
        <div className="w-[1px] h-8 bg-white/60" />
      </div>
    </section>
  );
};
