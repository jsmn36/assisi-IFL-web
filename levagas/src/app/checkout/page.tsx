"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Section } from '@/components/ui/Section';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useBooking } from '@/hooks/useBookingState';
import { ShieldCheck, CreditCard, Lock, ArrowLeft, Loader2 } from 'lucide-react';

export default function CheckoutPage() {
  const router = useRouter();
  const { state, setGuestInfo, setPaymentStatus } = useBooking();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    requests: ''
  });

  if (!state.selectedCottage) {
    return (
       <div className="pt-32 text-center">
          <p>Please select a cottage first.</p>
          <Button onClick={() => router.push('/book')}>Back to Selection</Button>
       </div>
    );
  }

  const handlePayment = async (provider: 'stripe' | 'razorpay') => {
    if (!formData.firstName || !formData.email || !formData.phone) {
      alert("Please fill in your contact details first.");
      return;
    }

    setLoading(true);
    
    // 1. Save guest info to context
    setGuestInfo({
      firstName: formData.firstName,
      lastName: formData.lastName,
      email: formData.email,
      phone: formData.phone,
      specialRequests: formData.requests
    });

    try {
      // 2. Call API to create payment intent
      const res = await fetch('/api/create-payment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          amount: state.selectedCottage?.price || 0,
          currency: 'INR',
          cottageSlug: state.selectedCottage?.slug,
          checkin: state.checkinDate,
          checkout: state.checkoutDate,
          guestEmail: formData.email
        }),
      });
      const data = await res.json();
      
      if (data.success) {
        // In a real app, we would mount Stripe/Razorpay UI here.
        // For this demo, we simulate a successful authorization.
        const mockId = `pi_mock_${Math.random().toString(36).substring(7)}`;
        console.log(`Initialized ${provider} with`, data[provider]);
        
        setTimeout(() => {
           setPaymentStatus(provider, mockId);
           // 3. Submit Booking (passing the ID directly to avoid stale state issues)
           submitBooking(mockId, provider);
        }, 1500);
      } else {
        throw new Error(data.error || "Payment failed");
      }
    } catch (err) {
      console.error(err);
      alert("Payment failed: " + (err instanceof Error ? err.message : "Unknown error"));
      setLoading(false);
    }
  };

  const submitBooking = async (paymentId: string, provider: string) => {
     try {
        const res = await fetch('/api/submit-booking', {
           method: 'POST',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify({
              checkin: state.checkinDate,
              checkout: state.checkoutDate,
              cottageSlug: state.selectedCottage?.slug,
              guests: state.guestCount,
              guestInfo: {
                 firstName: formData.firstName,
                 lastName: formData.lastName,
                 email: formData.email,
                 phone: formData.phone,
                 specialRequests: formData.requests
              },
              paymentIntentId: paymentId,
              paymentProvider: provider,
              paymentStatus: 'authorized'
           })
        });
        const data = await res.json();
        if (data.success) {
           router.push(`/confirmation?ref=${data.booking_ref}`);
        } else {
           throw new Error(data.error || "Submission failed");
        }
     } catch (err) {
        console.error(err);
        alert("Booking submission failed. Please try again.");
     } finally {
        setLoading(false);
     }
  };

  return (
    <div className="pt-24 min-h-screen bg-brand-primary-bg/20">
      <Section background="white" className="py-12">
        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-12">
          
          {/* Form Side */}
          <div className="lg:col-span-2 flex flex-col gap-12">
             <div className="flex items-center gap-4">
                <button onClick={() => router.back()} className="p-2 rounded-full hover:bg-brand-forest-green/5 text-brand-forest-green">
                   <ArrowLeft size={24} />
                </button>
                <div className="flex flex-col gap-1">
                   <div className="flex items-center gap-2 text-brand-forest-green font-bold text-xs uppercase tracking-widest">
                      <span className="w-6 h-6 rounded-full bg-brand-forest-green text-white flex items-center justify-center">2</span>
                      Guest Details & Payment
                   </div>
                   <h1 className="text-4xl font-heading italic">Complete Your Booking</h1>
                </div>
             </div>

             <div className="flex flex-col gap-8">
                <h3 className="text-xl font-heading border-b border-brand-forest-green/10 pb-4">1. Guest Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                   <Input 
                      label="First Name" 
                      placeholder="Enter first name" 
                      value={formData.firstName}
                      onChange={(e) => setFormData({...formData, firstName: e.target.value})}
                      required 
                   />
                   <Input 
                      label="Last Name" 
                      placeholder="Enter last name" 
                      value={formData.lastName}
                      onChange={(e) => setFormData({...formData, lastName: e.target.value})}
                      required 
                   />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                   <Input 
                      label="Email Address" 
                      type="email" 
                      placeholder="your@email.com" 
                      value={formData.email}
                      onChange={(e) => setFormData({...formData, email: e.target.value})}
                      required 
                   />
                   <Input 
                      label="Phone Number" 
                      placeholder="+91 00000 00000" 
                      value={formData.phone}
                      onChange={(e) => setFormData({...formData, phone: e.target.value})}
                      required 
                   />
                </div>
                <div className="flex flex-col gap-1.5">
                   <label className="text-sm font-medium text-brand-charcoal">Special Requests (Optional)</label>
                   <textarea 
                      className="flex min-h-[100px] w-full rounded-md border border-brand-warm-gray/30 bg-transparent px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-forest-green outline-none"
                      placeholder="Honeymoon setup, early check-in, dietary needs..."
                      value={formData.requests}
                      onChange={(e) => setFormData({...formData, requests: e.target.value})}
                   />
                </div>
             </div>

             <div className="flex flex-col gap-8">
                <h3 className="text-xl font-heading border-b border-brand-forest-green/10 pb-4">2. Secure Payment</h3>
                <p className="text-sm text-brand-charcoal/80 leading-relaxed font-light">
                   Raw card data is never stored on our servers. Your payment is securely held (authorized) and only captured upon confirmation of availability by our resort team.
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                   <div 
                      className={`cursor-pointer transition-all ${loading ? 'opacity-50 pointer-events-none' : 'hover:scale-[1.02] active:scale-95'}`}
                      onClick={() => handlePayment('stripe')}
                   >
                      <Card className="p-6 h-full border-2 hover:border-brand-forest-green">
                         <div className="flex flex-col gap-4 items-center text-center">
                            <div className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center text-blue-600">
                               <CreditCard size={24} />
                            </div>
                            <div className="flex flex-col">
                               <span className="font-bold text-brand-charcoal">International Card</span>
                               <span className="text-[10px] text-brand-warm-gray uppercase tracking-widest font-bold">Secure by Stripe</span>
                            </div>
                         </div>
                      </Card>
                   </div>
                   <div 
                      className={`cursor-pointer transition-all ${loading ? 'opacity-50 pointer-events-none' : 'hover:scale-[1.02] active:scale-95'}`}
                      onClick={() => handlePayment('razorpay')}
                   >
                      <Card className="p-6 h-full border-2 hover:border-brand-gold">
                         <div className="flex flex-col gap-4 items-center text-center">
                            <div className="w-12 h-12 rounded-full bg-orange-50 flex items-center justify-center text-orange-600">
                               <ShieldCheck size={24} />
                            </div>
                            <div className="flex flex-col">
                               <span className="font-bold text-brand-charcoal">Indian Card / UPI / Netbanking</span>
                               <span className="text-[10px] text-brand-warm-gray uppercase tracking-widest font-bold">Secure by Razorpay</span>
                            </div>
                         </div>
                      </Card>
                   </div>
                </div>
             </div>
          </div>

          {/* Sticky Summary Side */}
          <div className="lg:sticky lg:top-32 flex flex-col gap-8">
             <Card className="bg-brand-forest-green text-white border-none shadow-2xl">
                <CardContent className="p-8 flex flex-col gap-8">
                   <h3 className="text-2xl font-heading italic border-b border-white/10 pb-4">Reservation Summary</h3>
                   
                   <div className="flex flex-col gap-6">
                      <div className="flex flex-col gap-1">
                         <span className="text-[10px] uppercase tracking-widest text-white/40 font-bold">Cottage</span>
                         <span className="text-lg font-medium">{state.selectedCottage.name}</span>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                         <div className="flex flex-col gap-1">
                            <span className="text-[10px] uppercase tracking-widest text-white/40 font-bold">Check-in</span>
                            <span className="font-medium">{state.checkinDate}</span>
                         </div>
                         <div className="flex flex-col gap-1">
                            <span className="text-[10px] uppercase tracking-widest text-white/40 font-bold">Check-out</span>
                            <span className="font-medium">{state.checkoutDate}</span>
                         </div>
                      </div>
                      <div className="flex justify-between items-center bg-white/5 p-4 rounded-lg">
                         <span className="text-sm">Total Amount</span>
                         <span className="text-2xl font-bold text-brand-gold italic">₹{state.selectedCottage.price.toLocaleString()}</span>
                      </div>
                   </div>

                   <div className="flex items-center gap-3 text-xs text-white/60 font-medium">
                      <Lock size={14} className="shrink-0" />
                      <span>Authorized payment only. Your card is verified but not charged until the resort confirms.</span>
                   </div>
                </CardContent>
             </Card>

             {loading && (
                <div className="flex items-center gap-3 text-brand-forest-green font-bold animate-pulse justify-center">
                   <Loader2 size={24} className="animate-spin" />
                   <span>Authorizing payment securely...</span>
                </div>
             )}
          </div>
        </div>
      </Section>
    </div>
  );
}
