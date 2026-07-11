"use client";

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Section } from '@/components/ui/Section';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useBooking } from '@/hooks/useBookingState';
import { cottages } from '@/data/cottages';
import { Check, Calendar, Users, ArrowRight, Loader2 } from 'lucide-react';
import Image from 'next/image';
import { Suspense } from 'react';

function BookingPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { state, setDates, setGuests, selectCottage } = useBooking();
  const [loading, setLoading] = useState(false);
  const [availableCottages, setAvailableCottages] = useState<any[]>([]);

  useEffect(() => {
    const checkin = searchParams.get('checkin') || state.checkinDate;
    const checkout = searchParams.get('checkout') || state.checkoutDate;
    const guests = searchParams.get('guests') || state.guestCount.toString();

    if (checkin && checkout) {
      checkAvailability(checkin, checkout, parseInt(guests));
    }
  }, [searchParams, state.checkinDate, state.checkoutDate, state.guestCount]);

  const checkAvailability = async (checkin: string, checkout: string, guests: number) => {
    setLoading(true);
    try {
      const res = await fetch('/api/availability', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ checkin, checkout, guests }),
      });
      const data = await res.json();
      if (data.success) {
        setAvailableCottages(data.results);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (slug: string, name: string, price: number) => {
    selectCottage({ slug, name, price });
    router.push('/checkout');
  };

  return (
    <div className="pt-24 min-h-screen bg-brand-primary-bg/20">
      <Section background="white" className="py-12 md:py-16">
        <div className="max-w-5xl mx-auto flex flex-col gap-12">
          {/* Progress Header */}
          <div className="flex flex-col gap-4">
             <div className="flex items-center gap-2 text-brand-forest-green font-bold text-xs uppercase tracking-widest">
                <span className="w-6 h-6 rounded-full bg-brand-forest-green text-white flex items-center justify-center">1</span>
                Select Your Cottage
             </div>
             <h1 className="text-4xl md:text-5xl font-heading italic">Available Retreats</h1>
             <div className="flex flex-wrap gap-6 text-brand-charcoal/80 text-sm border-y border-brand-forest-green/10 py-4">
                <div className="flex items-center gap-2">
                   <Calendar size={16} /> {state.checkinDate} — {state.checkoutDate}
                </div>
                <div className="flex items-center gap-2">
                   <Users size={16} /> {state.guestCount} Guests
                </div>
             </div>
          </div>

          {/* Results Area */}
          <div className="flex flex-col gap-8">
             {loading ? (
                <div className="flex flex-col items-center justify-center py-24 gap-4 animate-pulse">
                   <Loader2 size={48} className="animate-spin text-brand-gold" />
                   <p className="text-brand-warm-gray font-medium italic">Scanning our hill sanctuary for availability...</p>
                </div>
             ) : availableCottages.length > 0 ? (
                <div className="grid grid-cols-1 gap-8">
                   {availableCottages.map((result) => {
                      const cottage = cottages.find(c => c.slug === result.slug);
                      if (!cottage) return null;
                      return (
                         <Card key={result.slug} className="group overflow-hidden border-none shadow-xl hover:shadow-2xl transition-all duration-500">
                            <CardContent className="p-0 flex flex-col md:flex-row">
                               <div className="relative w-full md:w-[350px] aspect-video md:aspect-auto">
                                  <Image src={cottage.images.hero} alt={cottage.name} fill className="object-cover" />
                               </div>
                               <div className="flex-grow p-8 flex flex-col justify-between gap-6">
                                  <div className="flex flex-col gap-2">
                                     <div className="flex justify-between items-start">
                                        <h3 className="text-2xl font-heading">{cottage.name}</h3>
                                        <div className="text-right">
                                           <span className="text-brand-forest-green font-bold text-2xl italic">₹{result.price.toLocaleString()}</span>
                                           <span className="text-[10px] block font-bold text-brand-warm-gray uppercase tracking-widest">Per Night</span>
                                        </div>
                                     </div>
                                     <p className="text-brand-charcoal/70 text-sm leading-relaxed max-w-xl">{cottage.description}</p>
                                  </div>
                                  
                                  <div className="flex flex-wrap gap-4 items-center justify-between">
                                     <ul className="flex gap-4">
                                        {cottage.features.slice(0, 3).map((f, i) => (
                                           <li key={i} className="text-xs text-brand-charcoal/80 flex items-center gap-1.5 bg-brand-forest-green/5 px-3 py-1.5 rounded-full font-medium italic">
                                              <Check size={12} className="text-brand-forest-green" /> {f}
                                           </li>
                                        ))}
                                     </ul>
                                     <Button 
                                        variant="cta-large" 
                                        className="h-12 px-8 flex gap-2 group"
                                        onClick={() => handleSelect(result.slug, result.name, result.price)}
                                     >
                                        Select Cottage <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                                     </Button>
                                  </div>
                               </div>
                            </CardContent>
                         </Card>
                      );
                   })}
                </div>
             ) : (
                <div className="bg-brand-primary-bg/50 p-12 rounded-3xl border border-brand-forest-green/10 text-center flex flex-col gap-6 items-center">
                   <div className="w-16 h-16 rounded-full bg-brand-gold/10 flex items-center justify-center text-brand-gold">
                      <Calendar size={32} />
                   </div>
                   <div className="max-w-md">
                      <h3 className="text-2xl font-heading mb-2">No availability for these dates</h3>
                      <p className="text-brand-charcoal/80 leading-relaxed font-light">Le Vagas is a small boutique property with only 5 cottages. Please try different dates or contact us directly for waiting list enquiries.</p>
                   </div>
                   <Button variant="secondary" onClick={() => router.push('/')}>Change Dates</Button>
                </div>
             )}
          </div>
        </div>
      </Section>
    </div>
  );
}

export default function BookingPage() {
  return (
    <Suspense fallback={<div className="pt-32 text-center">Loading booking...</div>}>
      <BookingPageContent />
    </Suspense>
  );
}
