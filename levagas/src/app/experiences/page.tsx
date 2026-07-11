import React from 'react';
import Image from 'next/image';
import { Section } from '@/components/ui/Section';

export default function ExperiencesPage() {
  return (
    <div className="pt-20">
      <section className="relative h-[40vh] bg-brand-forest-green text-center flex flex-col justify-center items-center text-white px-6">
        <h1 className="text-5xl font-heading italic drop-shadow-lg mb-4">Signature Experiences</h1>
        <p className="text-xl font-light tracking-wide">Connect with nature</p>
      </section>

      <Section background="white">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 mt-8">
           <div className="flex flex-col gap-4">
              <div className="relative aspect-video rounded-xl overflow-hidden shadow-lg">
                 <Image src="https://images.unsplash.com/photo-1544883602-5eb305017fd6?q=80&w=1200" alt="Sunrise Tea" fill className="object-cover" />
              </div>
              <h3 className="text-2xl font-heading text-brand-forest-green">Sunrise Tea Experience</h3>
              <p className="text-brand-charcoal/70">Begin your day with fresh-brewed tea as the sun rises over the misty hills. A truly serene start to the morning.</p>
           </div>
           
           <div className="flex flex-col gap-4">
              <div className="relative aspect-video rounded-xl overflow-hidden shadow-lg">
                 <Image src="https://images.unsplash.com/photo-1582490728790-db0e82daeb0b?q=80&w=1200" alt="Plantation Walk" fill className="object-cover" />
              </div>
              <h3 className="text-2xl font-heading text-brand-forest-green">Plantation Walk</h3>
              <p className="text-brand-charcoal/70">Guided walk through emerald tea gardens. Learn about tea cultivation from local experts.</p>
           </div>

           <div className="flex flex-col gap-4">
              <div className="relative aspect-video rounded-xl overflow-hidden shadow-lg">
                 <Image src="https://images.unsplash.com/photo-1473111453215-6ded4e39c4f1?q=80&w=1200" alt="Bonfire Setup" fill className="object-cover" />
              </div>
              <h3 className="text-2xl font-heading text-brand-forest-green">Evening Bonfire & BBQ</h3>
              <p className="text-brand-charcoal/70">Unwind under the starry sky with a crackling bonfire, acoustic music, and freshly grilled local delicacies.</p>
           </div>
           
           <div className="flex flex-col gap-4">
              <div className="relative aspect-video rounded-xl overflow-hidden shadow-lg">
                 <Image src="https://images.unsplash.com/photo-1551632811-561732d1e306?q=80&w=1200" alt="Trekking" fill className="object-cover" />
              </div>
              <h3 className="text-2xl font-heading text-brand-forest-green">Pine Forest Trekking</h3>
              <p className="text-brand-charcoal/70">Embark on an adventurous hike through Vagamon's famous pine forests to discover hidden waterfalls and viewpoints.</p>
           </div>
        </div>
      </Section>
    </div>
  );
}
