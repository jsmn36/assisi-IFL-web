import React from 'react';
import { Section } from '@/components/ui/Section';
import { PROPERTY_INFO } from '@/lib/constants';
import { Phone, Mail, MapPin, Clock, Globe } from 'lucide-react';
import { ContactForm } from '@/components/contact/ContactForm';

export const metadata = {
  title: 'Contact Us',
  description: 'Pathways to tranquility. Get in touch with Le Vagas for bookings, enquiries, or special requests.',
};

export default function ContactPage() {
  return (
    <div className="pt-20">
      <Section background="white">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-24 items-start">
           <div className="flex flex-col gap-12">
              <div className="flex flex-col gap-4">
                 <h1 className="text-5xl md:text-6xl font-heading italic tracking-tight">Get in Touch</h1>
                 <p className="text-xl text-brand-charcoal/70 font-light">
                   We are here to assist you with your journey to the hills.
                 </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                 <div className="flex flex-col gap-6 p-8 rounded-2xl bg-brand-primary-bg/40 border border-brand-forest-green/5">
                    <div className="w-12 h-12 rounded-full bg-brand-forest-green/10 flex items-center justify-center text-brand-forest-green">
                       <MapPin size={24} />
                    </div>
                    <div className="flex flex-col gap-2">
                       <h3 className="font-bold uppercase tracking-widest text-xs text-brand-forest-green">Location</h3>
                       <p className="text-sm text-brand-charcoal/80 leading-relaxed font-medium">{PROPERTY_INFO.address.full}</p>
                    </div>
                 </div>
                 <div className="flex flex-col gap-6 p-8 rounded-2xl bg-brand-primary-bg/40 border border-brand-forest-green/5">
                    <div className="w-12 h-12 rounded-full bg-brand-gold/10 flex items-center justify-center text-brand-gold">
                       <Phone size={24} />
                    </div>
                    <div className="flex flex-col gap-2">
                       <h3 className="font-bold uppercase tracking-widest text-xs text-brand-forest-green">Call or WhatsApp</h3>
                       <p className="text-sm text-brand-charcoal/80 leading-relaxed font-medium">{PROPERTY_INFO.phone}</p>
                    </div>
                 </div>
                 <div className="flex flex-col gap-6 p-8 rounded-2xl bg-brand-primary-bg/40 border border-brand-forest-green/5">
                    <div className="w-12 h-12 rounded-full bg-brand-forest-green/10 flex items-center justify-center text-brand-forest-green">
                       <Mail size={24} />
                    </div>
                    <div className="flex flex-col gap-2">
                       <h3 className="font-bold uppercase tracking-widest text-xs text-brand-forest-green">Support Email</h3>
                       <p className="text-sm text-brand-charcoal/80 leading-relaxed font-medium">{PROPERTY_INFO.email}</p>
                    </div>
                 </div>
                 <div className="flex flex-col gap-6 p-8 rounded-2xl bg-brand-primary-bg/40 border border-brand-forest-green/5">
                    <div className="w-12 h-12 rounded-full bg-brand-gold/10 flex items-center justify-center text-brand-gold">
                       <Globe size={24} />
                    </div>
                    <div className="flex flex-col gap-2">
                       <h3 className="font-bold uppercase tracking-widest text-xs text-brand-forest-green">Web Presence</h3>
                       <p className="text-sm text-brand-charcoal/80 leading-relaxed font-medium">{PROPERTY_INFO.instagram}</p>
                    </div>
                 </div>
              </div>

              <div className="flex items-center gap-4 p-8 rounded-2xl bg-brand-forest-green text-white">
                 <Clock className="shrink-0 text-brand-gold" size={32} />
                 <div className="flex flex-col">
                    <span className="text-xs font-bold uppercase tracking-[0.2em] text-white/90">Response Time</span>
                    <span className="text-lg font-light italic">Our team typically responds within 2 hours during property hours (8 AM - 10 PM IST).</span>
                 </div>
              </div>
           </div>

           {/* Contact Form */}
           <ContactForm />
        </div>
      </Section>

      {/* Map Segment (Placeholder) */}
      <section className="h-[400px] w-full bg-brand-primary-bg flex items-center justify-center grayscale opacity-80 border-t border-brand-forest-green/10">
         <div className="text-center flex flex-col items-center gap-4">
            <MapPin size={48} className="text-brand-forest-green opacity-30" strokeWidth={1} />
            <span className="text-brand-charcoal uppercase tracking-widest text-xs font-bold font-heading italic">Map Integration Placeholder</span>
            <p className="text-brand-charcoal font-light italic">Vagamon, Kerala</p>
         </div>
      </section>
    </div>
  );
}
