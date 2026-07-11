"use client";

import React, { useState, FormEvent } from 'react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { MessageSquare, CheckCircle } from 'lucide-react';

export function ContactForm() {
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <div className="bg-white p-8 md:p-12 rounded-3xl shadow-2xl border border-brand-forest-green/5 flex flex-col gap-8 items-center text-center">
        <div className="w-16 h-16 rounded-full bg-brand-forest-green flex items-center justify-center text-white">
          <CheckCircle size={32} />
        </div>
        <div className="flex flex-col gap-2">
          <h2 className="text-3xl font-heading italic text-brand-forest-green">Message Received!</h2>
          <p className="text-brand-charcoal/80 text-sm leading-relaxed">
            Thank you for reaching out. Our team typically responds within 2 hours during property hours (8 AM – 10 PM IST).
          </p>
        </div>
        <Button variant="secondary" onClick={() => setSubmitted(false)}>
          Send Another Message
        </Button>
      </div>
    );
  }

  return (
    <div className="bg-white p-8 md:p-12 rounded-3xl shadow-2xl border border-brand-forest-green/5 flex flex-col gap-8">
      <div className="flex flex-col gap-2">
        <h2 className="text-3xl font-heading flex items-center gap-3 italic">
          <MessageSquare className="text-brand-forest-green" /> Send a Message
        </h2>
        <p className="text-brand-charcoal/80 text-sm">
          Have a special request or a group booking enquiry? Drop us a note below.
        </p>
      </div>

      <form className="flex flex-col gap-6" onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Input label="Full Name" placeholder="Your name" required />
          <Input label="Email Address" type="email" placeholder="your@email.com" required />
        </div>
        <Input label="Phone Number" type="tel" placeholder="+91 00000 00000" />
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-brand-charcoal">How can we help?</label>
          <textarea
            className="flex min-h-[120px] w-full rounded-md border border-brand-warm-gray/30 bg-transparent px-3 py-2 text-sm placeholder:text-brand-warm-gray focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-forest-green focus-visible:ring-offset-2 outline-none"
            placeholder="Tell us about your plans..."
          />
        </div>
        <Button type="submit" variant="cta-large" className="w-full py-4 text-base">
          Send Enquiry
        </Button>
      </form>
    </div>
  );
}
