"use client";

import React, { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { Section } from '@/components/ui/Section';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { CheckCircle, Clock, AlertCircle, Loader2, ArrowRight, Phone } from 'lucide-react';
import { PROPERTY_INFO } from '@/lib/constants';
import { Suspense } from 'react';

function ConfirmationPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const ref = searchParams.get('ref');
  const [status, setStatus] = useState<'pending' | 'confirmed' | 'failed'>('pending');
  const [summary, setSummary] = useState<any>(null);
  const [attempts, setAttempts] = useState(0);

  useEffect(() => {
    if (!ref) return;

    const pollStatus = async () => {
      try {
        const res = await fetch(`/api/booking-status/${ref}`);
        const data = await res.json();
        
        if (data.status === 'confirmed') {
          setStatus('confirmed');
          setSummary(data.summary);
        } else if (attempts > 10) { // Max 90s roughly (with 5s interval)
          setStatus('pending'); // Keep pending but show message
        } else {
          setAttempts(prev => prev + 1);
          setTimeout(pollStatus, 5000);
        }
      } catch (err) {
        console.error(err);
      }
    };

    pollStatus();
  }, [ref, attempts]);

  return (
    <div className="pt-24 min-h-screen bg-brand-primary-bg/20">
      <Section background="white">
        <div className="max-w-3xl mx-auto flex flex-col gap-12 text-center py-12">
          
          {status === 'pending' && (
             <div className="flex flex-col items-center gap-8 animate-in fade-in zoom-in duration-700">
                <div className="w-24 h-24 rounded-full bg-brand-gold/10 flex items-center justify-center text-brand-gold">
                   <Loader2 size={48} className="animate-spin" />
                </div>
                <div className="flex flex-col gap-4">
                   <h1 className="text-4xl font-heading italic">We&apos;re verifying your retreat...</h1> 
                   <p className="text-xl text-brand-charcoal/70 font-light leading-relaxed">
                      We are currently confirming availability with our PMS. This usually takes less than 60 seconds.
                   </p>
                </div>
                <Card className="w-full bg-brand-primary-bg/50 border-none">
                   <CardContent className="p-6 flex items-center gap-4 text-left">
                      <Clock className="text-brand-forest-green shrink-0" />
                      <p className="text-sm text-brand-charcoal/80">
                         <strong>Step 1:</strong> Payment Authorized (Done) <br />
                         <strong>Step 2:</strong> Resort Confirmation (In Progress...)
                      </p>
                   </CardContent>
                </Card>
             </div>
          )}

          {status === 'confirmed' && (
             <div className="flex flex-col items-center gap-8 animate-in slide-in-from-bottom duration-1000">
                <div className="w-24 h-24 rounded-full bg-brand-forest-green flex items-center justify-center text-white shadow-2xl">
                   <CheckCircle size={48} />
                </div>
                <div className="flex flex-col gap-4">
                   <h1 className="text-4xl font-heading italic text-brand-forest-green">Reservation Confirmed!</h1>
                   <p className="text-xl text-brand-charcoal/70 font-light leading-relaxed">
                      Pack your bags! Your stay at Le Vagas is officially confirmed. 
                      A confirmation email with your stay details has been sent to your inbox.
                   </p>
                </div>

                <Card className="w-full shadow-2xl border-brand-forest-green/10">
                   <CardContent className="p-8 flex flex-col gap-6 text-left">
                      <div className="flex justify-between items-center border-b border-brand-forest-green/10 pb-4">
                         <span className="text-xs font-bold uppercase tracking-widest text-brand-warm-gray">Booking Reference</span>
                         <span className="text-lg font-bold text-brand-forest-green">{ref}</span>
                      </div>
                      <div className="grid grid-cols-2 gap-8">
                         <div className="flex flex-col gap-1">
                            <span className="text-[10px] uppercase tracking-widest text-brand-warm-gray font-bold">Resort</span>
                            <span className="font-medium">Le Vagas, Vagamon</span>
                         </div>
                         <div className="flex flex-col gap-1">
                            <span className="text-[10px] uppercase tracking-widest text-brand-warm-gray font-bold">Cottage</span>
                            <span className="font-medium">{summary?.cottage || 'Private Cottage'}</span>
                         </div>
                      </div>
                      <div className="grid grid-cols-2 gap-8">
                         <div className="flex flex-col gap-1">
                            <span className="text-[10px] uppercase tracking-widest text-brand-warm-gray font-bold">Check-in</span>
                            <span className="font-medium">{summary?.checkin}</span>
                         </div>
                         <div className="flex flex-col gap-1">
                            <span className="text-[10px] uppercase tracking-widest text-brand-warm-gray font-bold">Check-out</span>
                            <span className="font-medium">{summary?.checkout}</span>
                         </div>
                      </div>
                   </CardContent>
                </Card>

                <div className="flex flex-col sm:flex-row gap-4 w-full justify-center mt-4">
                   <Button variant="primary" onClick={() => router.push('/')} className="px-12 py-4">Return Home</Button>
                   <Button variant="secondary" onClick={() => window.print()} className="px-12 py-4">Print Summary</Button>
                </div>
             </div>
          )}

          {status === 'failed' && (
             <div className="flex flex-col items-center gap-8">
                <div className="w-24 h-24 rounded-full bg-brand-error/10 flex items-center justify-center text-brand-error">
                   <AlertCircle size={48} />
                </div>
                <div className="flex flex-col gap-4">
                   <h1 className="text-4xl font-heading italic">Something went wrong</h1>
                   <p className="text-xl text-brand-charcoal/70 font-light leading-relaxed">
                      We were unable to confirm your booking at this time. 
                      Your payment authorization will be automatically released.
                   </p>
                </div>
                <Link href={`tel:${PROPERTY_INFO.phone.replace(/\s/g, '')}`}>
                   <Button variant="primary" className="flex gap-2">
                      <Phone size={18} /> Contact Resort Directly
                   </Button>
                </Link>
             </div>
          )}
        </div>
      </Section>
    </div>
  );
}

export default function ConfirmationPage() {
  return (
    <Suspense fallback={<div className="pt-32 text-center">Loading confirmation...</div>}>
      <ConfirmationPageContent />
    </Suspense>
  );
}
