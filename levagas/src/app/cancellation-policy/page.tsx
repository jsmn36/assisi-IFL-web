import React from 'react';
import { Section } from '@/components/ui/Section';

export default function CancellationPage() {
  return (
    <div className="pt-24 min-h-screen">
      <Section background="white">
        <div className="max-w-3xl mx-auto flex flex-col gap-8">
           <h1 className="text-4xl font-heading text-brand-forest-green italic">Cancellation Policy</h1>
           <div className="text-brand-charcoal/70 flex flex-col gap-4">
              <h2 className="text-xl font-heading text-brand-charcoal mt-4">Free Cancellation</h2>
              <p>Guests may cancel their booking free of charge up to 7 days before the check-in date.</p>
              <h2 className="text-xl font-heading text-brand-charcoal mt-4">Late Cancellation</h2>
              <p>Cancellations made between 3 and 7 days prior to check-in will incur a 50% charge of the total booking cost.</p>
              <h2 className="text-xl font-heading text-brand-charcoal mt-4">No Show & Last Minute</h2>
              <p>Cancellations within 3 days of arrival, or no-shows, are strictly non-refundable.</p>
              <p className="mt-8 font-light italic">For emergency situations, please contact the property directly.</p>
           </div>
        </div>
      </Section>
    </div>
  );
}
