import React from 'react';
import { Section } from '@/components/ui/Section';

export default function LegalPage() {
  return (
    <div className="pt-24 min-h-screen">
      <Section background="white">
        <div className="max-w-3xl mx-auto flex flex-col gap-8">
           <h1 className="text-4xl font-heading text-brand-forest-green italic">Terms & Conditions</h1>
           <div className="text-brand-charcoal/70 flex flex-col gap-4">
              <p>Welcome to Le Vagas. These terms and conditions outline the rules and regulations for the use of our services.</p>
              <p>By booking a stay at Le Vagas, you accept these terms and conditions in full.</p>
              <h2 className="text-xl font-heading text-brand-charcoal mt-4">1. Booking Policies</h2>
              <p>All bookings require payment authorization. Availability is subject to confirmation.</p>
              <h2 className="text-xl font-heading text-brand-charcoal mt-4">2. Property Rules</h2>
              <p>Guests are expected to respect nature, keep noise to a minimum, and adhere to local environmental guidelines.</p>
           </div>
        </div>
      </Section>
    </div>
  );
}
