import React from 'react';
import Image from 'next/image';
import { notFound } from 'next/navigation';
import { Check, Info, Phone, Calendar, Users, MapPin, Wind, Sun, MessageCircle } from 'lucide-react';
import Link from 'next/link';
import { Section } from '@/components/ui/Section';
import { Button } from '@/components/ui/Button';
import { BookingWidget } from '@/components/booking/BookingWidget';
import { Card, CardContent } from '@/components/ui/Card';
import { cottages } from '@/data/cottages';
import { PROPERTY_INFO } from '@/lib/constants';

interface PageProps {
  params: { slug: string };
}

export async function generateStaticParams() {
  return cottages.map((cottage) => ({
    slug: cottage.slug,
  }));
}

export async function generateMetadata({ params }: PageProps) {
  const cottage = cottages.find((c) => c.slug === params.slug);
  if (!cottage) return {};

  return {
    title: cottage.name,
    description: cottage.description,
  };
}

export default function CottageDetailPage({ params }: PageProps) {
  const cottage = cottages.find((c) => c.slug === params.slug);

  if (!cottage) {
    notFound();
  }

  const otherCottages = cottages.filter(c => c.slug !== params.slug).slice(0, 2);

  return (
    <div className="pt-20">
      {/* Hero Gallery */}
      <section className="relative h-[60vh] md:h-[80vh] w-full overflow-hidden">
        <Image
          src={cottage.images.hero}
          alt={cottage.name}
          fill
          priority
          className="object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-brand-charcoal/60 via-transparent to-transparent flex flex-col justify-end p-6 md:p-12">
          <div className="max-w-7xl mx-auto w-full">
            <h1 className="text-5xl md:text-7xl font-heading text-white mb-4 tracking-tight">{cottage.name}</h1>
            <div className="flex flex-wrap gap-4 text-white/90 font-medium">
              <span className="flex items-center gap-2 bg-brand-forest-green/30 backdrop-blur-md px-4 py-2 rounded-full border border-white/20">
                <Users size={18} /> Max {cottage.maxGuests} Guests
              </span>
              <span className="flex items-center gap-2 bg-brand-forest-green/30 backdrop-blur-md px-4 py-2 rounded-full border border-white/20">
                <MapPin size={18} /> {cottage.view}
              </span>
              <span className="flex items-center gap-2 bg-brand-forest-green/30 backdrop-blur-md px-4 py-2 rounded-full border border-white/20">
                <Wind size={18} /> {cottage.size}
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Content Grid */}
      <Section background="white">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-16 items-start">
          {/* Main Info */}
          <div className="lg:col-span-2 flex flex-col gap-12">
            <div className="flex flex-col gap-6">
              <h2 className="text-3xl font-heading border-b border-brand-forest-green/10 pb-4">About the {cottage.name}</h2>
              <div className="text-lg text-brand-charcoal/80 leading-relaxed flex flex-col gap-4">
                <p>{cottage.description}</p>
                <p>Designed with natural materials and warm lighting, this cottage is a true mountain sanctuary. Enjoy the panoramic views from your private balcony or relax in the cozy seating area as the mist rolls in.</p>
              </div>
            </div>

            {/* Gallery Grid */}
            <div className="grid grid-cols-2 gap-4">
              {cottage.images.gallery.map((img, i) => (
                <div key={i} className="relative aspect-video rounded-xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-500">
                  <Image src={img} alt={`${cottage.name} gallery ${i}`} fill className="object-cover hover:scale-105 transition-transform duration-700" />
                </div>
              ))}
            </div>

            {/* Amenities Grid */}
            <div className="flex flex-col gap-8">
              <h2 className="text-3xl font-heading border-b border-brand-forest-green/10 pb-4">Amenities & Comforts</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-6">
                {cottage.amenities.map((amenity, i) => (
                  <div key={i} className="flex items-center gap-3 text-brand-charcoal/80 group">
                    <div className="w-8 h-8 rounded-full bg-brand-forest-green/5 flex items-center justify-center text-brand-forest-green group-hover:bg-brand-forest-green group-hover:text-white transition-colors duration-300">
                      <Check size={16} strokeWidth={3} />
                    </div>
                    <span className="font-medium">{amenity}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Policies */}
            <div className="bg-brand-primary-bg/30 p-8 rounded-2xl border border-brand-forest-green/10 flex flex-col gap-8">
              <h3 className="text-2xl font-heading flex items-center gap-3">
                <Info className="text-brand-forest-green" /> Stay Policies
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="flex flex-col gap-2">
                  <h4 className="font-bold uppercase tracking-widest text-xs text-brand-forest-green">Check-in / Check-out</h4>
                  <p className="text-sm text-brand-charcoal/70 leading-relaxed">Check-in: 2:00 PM | Check-out: 11:00 AM. Early check-in or late check-out is subject to availability.</p>
                </div>
                <div className="flex flex-col gap-2">
                  <h4 className="font-bold uppercase tracking-widest text-xs text-brand-forest-green">Cancellation</h4>
                  <p className="text-sm text-brand-charcoal/70 leading-relaxed">Free cancellation up to 7 days before check-in. Non-refundable if cancelled within 3 days of arrival.</p>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar Booking Widget */}
          <div className="lg:sticky lg:top-32 flex flex-col gap-8">
            <Card className="border-none shadow-2xl bg-brand-primary-bg ring-1 ring-brand-forest-green/5">
              <div className="p-8 flex flex-col gap-8">
                <div className="flex justify-between items-end border-b border-brand-forest-green/10 pb-6">
                  <div className="flex flex-col">
                    <span className="text-2xl font-bold text-brand-forest-green italic font-heading">₹{cottage.priceFrom.toLocaleString()}</span>
                    <span className="text-[10px] font-bold uppercase tracking-widest text-brand-warm-gray">Per Night</span>
                  </div>
                  <div className="flex items-center gap-1 text-brand-gold">
                    {[...Array(5)].map((_, i) => <Check key={i} size={12} fill="currentColor" /> )}
                  </div>
                </div>

                <div className="flex flex-col gap-6">
                  <div className="flex flex-col gap-2">
                    <label className="text-[10px] font-bold uppercase tracking-widest text-brand-forest-green">Select Dates</label>
                    <div className="flex items-center gap-2 text-brand-charcoal font-medium bg-white p-3 rounded-lg border border-brand-forest-green/10 shadow-sm">
                      <Calendar size={18} className="text-brand-forest-green" />
                      <span>Check Availability Below</span>
                    </div>
                  </div>
                  <div className="flex flex-col gap-2">
                    <label className="text-[10px] font-bold uppercase tracking-widest text-brand-forest-green">Occupancy</label>
                    <div className="flex items-center gap-2 text-brand-charcoal font-medium bg-white p-3 rounded-lg border border-brand-forest-green/10 shadow-sm">
                       <Users size={18} className="text-brand-forest-green" />
                       <span>{cottage.maxGuests} Guests Max</span>
                    </div>
                  </div>
                </div>

                <Link href="/book">
                  <Button variant="cta-large" className="w-full h-14 bg-brand-gold border-brand-gold text-brand-charcoal hover:bg-brand-gold/90 scale-100 hover:scale-[1.02] transition-transform">
                    Check Availability
                  </Button>
                </Link>

                <p className="text-[11px] text-center text-brand-warm-gray leading-relaxed">
                  🔒 Secure Direct Booking with Le Vagas<br /> No hidden fees or OTA commissions.
                </p>
              </div>
            </Card>

            <div className="flex flex-col gap-4">
              <h3 className="font-heading text-xl">Need Help?</h3>
              <div className="flex flex-col gap-3">
                <Link href={`tel:${PROPERTY_INFO.phone.replace(/\s/g, '')}`} className="flex items-center gap-3 p-4 rounded-xl bg-white border border-brand-forest-green/5 hover:border-brand-forest-green/30 transition-all group">
                   <div className="w-10 h-10 rounded-full bg-brand-forest-green/10 flex items-center justify-center text-brand-forest-green group-hover:bg-brand-forest-green group-hover:text-white transition-all">
                     <Phone size={20} />
                   </div>
                   <div className="flex flex-col">
                      <span className="text-xs text-brand-warm-gray uppercase tracking-widest font-bold">Call Us</span>
                      <span className="font-medium">{PROPERTY_INFO.phone}</span>
                   </div>
                </Link>
                <Link href={`https://wa.me/${PROPERTY_INFO.phone.replace(/[^0-9]/g, '')}`} className="flex items-center gap-3 p-4 rounded-xl bg-white border border-brand-forest-green/5 hover:border-brand-forest-green/30 transition-all group">
                   <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center text-green-600 group-hover:bg-green-600 group-hover:text-white transition-all">
                     <MessageCircle size={20} />
                   </div>
                   <div className="flex flex-col">
                      <span className="text-xs text-brand-warm-gray uppercase tracking-widest font-bold">WhatsApp</span>
                      <span className="font-medium">Chat With Us</span>
                   </div>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </Section>

      {/* Check Availability */}
      <Section background="primary">
        <div className="flex flex-col gap-8">
          <h2 className="text-3xl font-heading text-center">Check Availability</h2>
          <BookingWidget className="max-w-4xl mx-auto w-full" />
        </div>
      </Section>

      {/* Similar Cottages */}
      <Section background="primary">
        <div className="flex flex-col gap-12">
          <div className="flex flex-col md:flex-row justify-between items-end gap-6 pb-6 border-b border-brand-forest-green/10">
            <h2 className="text-4xl font-heading">Other Beautiful Cottages</h2>
            <Link href="/cottages" className="text-brand-forest-green font-bold">Explore All →</Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {otherCottages.map((c) => (
              <Link key={c.slug} href={`/cottages/${c.slug}`} className="group relative aspect-[16/9] rounded-2xl overflow-hidden shadow-xl">
                 <Image src={c.images.hero} alt={c.name} fill className="object-cover group-hover:scale-110 transition-transform duration-700" />
                 <div className="absolute inset-0 bg-gradient-to-t from-brand-charcoal/80 via-transparent to-transparent opacity-90" />
                 <div className="absolute bottom-6 left-6 right-6">
                    <h3 className="text-2xl font-heading text-white mb-2">{c.name}</h3>
                    <div className="flex justify-between items-center">
                       <span className="text-white/90 text-sm font-medium">{c.view}</span>
                       <span className="text-brand-gold font-bold">₹{c.priceFrom.toLocaleString()} →</span>
                    </div>
                 </div>
              </Link>
            ))}
          </div>
        </div>
      </Section>
    </div>
  );
}
