"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Calendar, Users } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export const BookingWidget = ({ className }: { className?: string }) => {
  const router = useRouter();
  const [checkin, setCheckin] = useState('');
  const [checkout, setCheckout] = useState('');
  const [guests, setGuests] = useState('2');

  const handleCheckAvailability = (e: React.FormEvent) => {
    e.preventDefault();
    const params = new URLSearchParams({
      checkin,
      checkout,
      guests
    });
    router.push(`/book?${params.toString()}`);
  };

  return (
    <div className={`bg-white/90 backdrop-blur-md p-6 rounded-xl shadow-2xl border border-brand-forest-green/10 ${className}`}>
      <form onSubmit={handleCheckAvailability} className="flex flex-col lg:flex-row gap-4 items-end">
        <div className="flex-grow grid grid-cols-1 md:grid-cols-3 gap-4 w-full">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="bw-checkin" className="text-xs font-bold uppercase tracking-wider text-brand-forest-green flex items-center gap-2">
              <Calendar size={14} aria-hidden="true" /> Check-in
            </label>
            <input
              id="bw-checkin"
              type="date"
              required
              value={checkin}
              onChange={(e) => setCheckin(e.target.value)}
              className="bg-transparent border-b-2 border-brand-forest-green/20 focus:border-brand-forest-green outline-none py-2 text-brand-charcoal font-medium transition-colors"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="bw-checkout" className="text-xs font-bold uppercase tracking-wider text-brand-forest-green flex items-center gap-2">
              <Calendar size={14} aria-hidden="true" /> Check-out
            </label>
            <input
              id="bw-checkout"
              type="date"
              required
              value={checkout}
              onChange={(e) => setCheckout(e.target.value)}
              className="bg-transparent border-b-2 border-brand-forest-green/20 focus:border-brand-forest-green outline-none py-2 text-brand-charcoal font-medium transition-colors"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="bw-guests" className="text-xs font-bold uppercase tracking-wider text-brand-forest-green flex items-center gap-2">
              <Users size={14} aria-hidden="true" /> Guests
            </label>
            <select
              id="bw-guests"
              value={guests}
              onChange={(e) => setGuests(e.target.value)}
              className="bg-transparent border-b-2 border-brand-forest-green/20 focus:border-brand-forest-green outline-none py-2 text-brand-charcoal font-medium transition-colors appearance-none cursor-pointer"
            >
              <option value="1">1 Guest</option>
              <option value="2">2 Guests</option>
              <option value="3">3 Guests</option>
              <option value="4">4 Guests</option>
              <option value="5">5 Guests</option>
              <option value="6">6 Guests</option>
            </select>
          </div>
        </div>
        <Button type="submit" variant="cta-large" className="w-full lg:w-auto h-[52px]">
          Check Availability
        </Button>
      </form>
    </div>
  );
};
