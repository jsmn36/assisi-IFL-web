import React from 'react';
import Image from 'next/image';
import { Section } from '@/components/ui/Section';

export default function WellnessPage() {
  return (
    <div className="pt-20">
      <section className="relative h-[60vh] w-full overflow-hidden">
        <Image src="https://images.unsplash.com/photo-1544161515-4ab6ce6db874?q=80&w=1200" alt="Le Vagas Wellness Spa" fill priority className="object-cover" />
        <div className="absolute inset-0 bg-brand-charcoal/40 flex flex-col justify-center items-center text-center px-6">
           <h1 className="text-5xl md:text-7xl font-heading text-white italic drop-shadow-lg mb-4">Wellness Spa</h1>
           <p className="text-xl text-white/90 font-light tracking-wide">Rejuvenate your body and mind</p>
        </div>
      </section>

      <Section background="white">
        <div className="max-w-4xl mx-auto flex flex-col gap-12">
           <p className="text-lg text-brand-charcoal/80 leading-relaxed text-center">
             Rejuvenate your body and mind at our tranquil wellness spa. Our spa therapies combine ancient healing techniques of Ayurveda with modern relaxation methods, designed to restore your natural balance.
           </p>

           <div className="grid grid-cols-1 md:grid-cols-2 gap-12 mt-8">
              <div className="flex flex-col gap-6">
                 <div className="relative aspect-[4/3] rounded-2xl overflow-hidden shadow-lg">
                    <Image src="https://images.unsplash.com/photo-1544161515-4ab6ce6db874?q=80&w=1200" alt="Shirodhara Treatment" fill className="object-cover" />
                 </div>
                 <div>
                    <h3 className="text-2xl font-heading mb-2 text-brand-forest-green">Traditional Ayurveda</h3>
                    <p className="text-brand-charcoal/70 mb-4">Experience therapeutic treatments like Shirodhara and Abhyanga massage using customized herbal oils to detoxify your system.</p>
                 </div>
              </div>

              <div className="flex flex-col gap-6">
                 <div className="relative aspect-[4/3] rounded-2xl overflow-hidden shadow-lg">
                    <Image src="https://images.unsplash.com/photo-1506126613408-eca07ce68773?q=80&w=1200" alt="Guided Morning Yoga" fill className="object-cover" />
                 </div>
                 <div>
                    <h3 className="text-2xl font-heading mb-2 text-brand-forest-green">Guided Morning Yoga</h3>
                    <p className="text-brand-charcoal/70 mb-4">Start your day finding inner peace with our expert instructor on the panoramic hilltop yoga deck amidst the clouds.</p>
                 </div>
              </div>

              <div className="flex flex-col gap-6">
                 <div className="relative aspect-[4/3] rounded-2xl overflow-hidden shadow-lg">
                    <Image src="https://images.unsplash.com/photo-1519823551278-64ac92734fb1?q=80&w=1200" alt="Deep Tissue Relaxation" fill className="object-cover" />
                 </div>
                 <div>
                    <h3 className="text-2xl font-heading mb-2 text-brand-forest-green">Deep Tissue Relaxation</h3>
                    <p className="text-brand-charcoal/70 mb-4">A focused massage therapy designed to release chronic tension, ease muscle stiffness, and calm the nervous system.</p>
                 </div>
              </div>

              <div className="flex flex-col gap-6">
                 <div className="relative aspect-[4/3] rounded-2xl overflow-hidden shadow-lg">
                    <Image src="https://images.unsplash.com/photo-1554244933-d87676a10d8a?q=80&w=1200" alt="Steam Baths & Sauna" fill className="object-cover" />
                 </div>
                 <div>
                    <h3 className="text-2xl font-heading mb-2 text-brand-forest-green">Steam Baths & Sauna</h3>
                    <p className="text-brand-charcoal/70 mb-4">Complement your therapy sessions with our cedar wood saunas and aromatic steam baths for complete rejuvenation.</p>
                 </div>
              </div>
           </div>
        </div>
      </Section>
    </div>
  );
}
