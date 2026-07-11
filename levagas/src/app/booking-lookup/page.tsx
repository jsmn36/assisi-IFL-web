"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Section } from '@/components/ui/Section';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { Search, Loader2 } from 'lucide-react';

export default function BookingLookupPage() {
  const router = useRouter();
  const [ref, setRef] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLookup = (e: React.FormEvent) => {
    e.preventDefault();
    if (!ref) return;
    setLoading(true);
    // In a real app we would call /api/booking-status/[ref]
    router.push(`/confirmation?ref=${ref}`);
  };

  return (
    <div className="pt-32 min-h-screen bg-brand-primary-bg/20">
      <Section background="white" className="max-w-3xl mx-auto rounded-3xl shadow-xl">
         <div className="flex flex-col gap-8 text-center items-center py-8">
            <div className="w-16 h-16 rounded-full bg-brand-forest-green/10 flex items-center justify-center text-brand-forest-green mb-2">
               <Search size={32} />
            </div>
            <h1 className="text-4xl font-heading text-brand-forest-green italic">Find Your Booking</h1>
            <p className="text-brand-charcoal/70 font-light text-lg">
              Enter your booking reference or email address to view the status of your stay.
            </p>
            <form onSubmit={handleLookup} className="flex flex-col gap-6 w-full max-w-md mt-4">
               <Input 
                  label="Booking Reference or Email" 
                  placeholder="e.g. LV-2026-1234 or your@email.com" 
                  value={ref}
                  onChange={(e) => setRef(e.target.value)}
                  required 
               />
               <Button type="submit" variant="cta-large" className="w-full flex gap-2 items-center justify-center">
                  {loading ? <Loader2 size={20} className="animate-spin" /> : "Lookup Booking"}
               </Button>
            </form>
         </div>
      </Section>
    </div>
  );
}
