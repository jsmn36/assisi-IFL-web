import React from 'react';
import Image from 'next/image';
import { Section } from '@/components/ui/Section';
import { PROPERTY_INFO } from '@/lib/constants';
import { team } from '@/data/team';
import { Card, CardContent } from '@/components/ui/Card';

export const metadata = {
  title: 'About Le Vagas - Our Story',
  description: 'Learn about the vision behind Le Vagas and the dedicated team that makes your stay unforgettable.',
};

export default function AboutPage() {
  return (
    <div className="pt-20">
      {/* Our Story */}
      <Section background="white">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
           <div className="flex flex-col gap-8">
              <span className="tagline text-brand-forest-green uppercase tracking-[0.3em] text-sm font-bold block">Our Story</span>
              <h1 className="text-5xl font-heading italic leading-tight">Born from a love for the hills</h1>
              <div className="text-lg text-brand-charcoal/80 leading-relaxed font-light flex flex-col gap-4">
                 <p>Le Vagas was founded on a simple vision: to create a sanctuary where the modern traveler could disconnect from the chaos of the world and reconnect with the quiet rhythms of nature.</p>
                 <p>Located in a secluded pocket of Vagamon, the resort is more than just a place to stay—it&apos;s a tribute to the misty tea gardens, the emerald hills, and the warm hospitality of Kerala. We spent years searching for the perfect hillside, ensuring it offered 180-degree panoramas of the Western Ghats without compromising the lush local flora.</p>
                 <p>Our commitment to sustainability and authentic experiences ensures that every guest leaves with a piece of the hills in their heart. From the pine woods to the sweeping meadows, every stone and beam of Le Vagas is designed to honor the natural beauty around it.</p>
              </div>
           </div>
           <div className="relative aspect-[4/5] rounded-3xl overflow-hidden shadow-2xl">
              <Image src="https://images.unsplash.com/photo-1540331547168-8b6310f62424?q=80&w=1400" alt="Le Vagas Resort Context" fill className="object-cover" />
           </div>
        </div>
      </Section>

      {/* Philosophy & Sustainability */}
      <Section background="primary" className="py-24">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
           <div className="order-2 lg:order-1 relative aspect-square md:aspect-[4/3] rounded-3xl overflow-hidden shadow-2xl">
              <Image src="https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?q=80&w=1200" alt="Eco Friendly Kerala" fill className="object-cover" />
           </div>
           <div className="order-1 lg:order-2 flex flex-col gap-8">
              <span className="tagline text-brand-forest-green uppercase tracking-[0.3em] text-sm font-bold block">Our Philosophy</span>
              <h2 className="text-4xl md:text-5xl font-heading italic leading-tight">Rooted in Sustainable Luxury</h2>
              <div className="text-lg text-brand-charcoal/80 leading-relaxed font-light flex flex-col gap-4">
                 <p>We believe true luxury doesn&apos;t cost the earth. Every element of Le Vagas is carefully curated to minimize our footprint.</p>
                 <p>We source 80% of our ingredients from our own organic farms or local artisans, and our cottages are built with indigenous materials using traditional Kerala architecture combined with modern aesthetics.</p>
                 <p>Rainwater harvesting, solar heating, and a zero-plastic policy are not just initiatives—they are the core of the Le Vagas experience.</p>
              </div>
           </div>
        </div>
      </Section>

      {/* The Team */}
      <Section background="primary">
        <div className="text-center max-w-3xl mx-auto mb-16 flex flex-col gap-4">
           <h2 className="text-4xl font-heading italic">Meet the Team</h2>
           <p className="text-brand-charcoal/70">The dedicated professionals who make the magic happen.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
           {team.map((member, i) => (
             <Card key={i} className="bg-transparent border-none shadow-none text-center group">
               <div className="relative w-48 h-48 mx-auto mb-6 rounded-full overflow-hidden border-4 border-white shadow-xl group-hover:shadow-2xl transition-all duration-500">
                  <Image src={member.image} alt={member.name} fill className="object-cover group-hover:scale-110 transition-transform duration-700" />
               </div>
               <CardContent>
                  <h3 className="text-2xl font-heading text-brand-charcoal mb-1">{member.name}</h3>
                  <span className="text-xs font-bold uppercase tracking-widest text-brand-forest-green mb-4 block">{member.role}</span>
                  <p className="text-brand-charcoal/70 text-sm leading-relaxed">{member.bio}</p>
               </CardContent>
             </Card>
           ))}
        </div>
      </Section>
    </div>
  );
}
