"use client";

import React from 'react';
import { Section } from '@/components/ui/Section';

export default function MyBookingsPage() {
  return (
    <div className="pt-32 min-h-screen bg-brand-primary-bg/20">
      <Section background="white" className="max-w-4xl mx-auto rounded-3xl shadow-xl p-12 text-center flex flex-col gap-6">
         <h1 className="text-4xl font-heading text-brand-forest-green italic">My Bookings</h1>
         <p className="text-brand-charcoal/70">
           Welcome to your guest dashboard. To view your bookings, please login or use the booking lookup tool.
         </p>
         <a href="/booking-lookup" className="text-brand-gold font-bold underline">Lookup a booking using Reference ID</a>
      </Section>
    </div>
  );
}
