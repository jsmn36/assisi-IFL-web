import React from 'react';
import { Section } from '@/components/ui/Section';

export default function PrivacyPage() {
  return (
    <div className="pt-24 min-h-screen">
      <Section background="white">
        <div className="max-w-3xl mx-auto flex flex-col gap-8">
           <h1 className="text-4xl font-heading text-brand-forest-green italic">Privacy Policy</h1>
           <div className="text-brand-charcoal/70 flex flex-col gap-4">
              <p>Your privacy is important to us. This policy explains how we collect, use, and store your data.</p>
              <h2 className="text-xl font-heading text-brand-charcoal mt-4">Data Collection</h2>
              <p>We do not store payment card information. All transactions are securely processed via certified providers.</p>
           </div>
        </div>
      </Section>
    </div>
  );
}
