import React from 'react';
import Image from 'next/image';
import { Section } from '@/components/ui/Section';
import { Card, CardContent } from '@/components/ui/Card';

export const metadata = {
  title: 'Dining - The Hill Table',
  description: 'Savor exquisite authentic Kerala cuisine with breathtaking hill views at The Hill Table restaurant.',
};

export default function DiningPage() {
  return (
    <div className="pt-20">
      <section className="relative h-[60vh] w-full overflow-hidden">
        <Image src="https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?q=80&w=1200" alt="The Hill Table Dining" fill priority className="object-cover" />
        <div className="absolute inset-0 bg-brand-charcoal/40 flex flex-col justify-center items-center text-center px-6">
           <h1 className="text-5xl md:text-7xl font-heading text-white italic drop-shadow-lg mb-4">The Hill Table</h1>
           <p className="text-xl text-white/90 font-light tracking-wide">Gastronomy above the clouds</p>
        </div>
      </section>

      <Section background="white">
        <div className="max-w-4xl mx-auto flex flex-col gap-12 text-center">
           <p className="text-lg text-brand-charcoal/80 leading-relaxed">
             Our signature restaurant offers a delightful dining experience with scenic hill views. Guests can enjoy authentic Kerala cuisine, fresh local flavors, and a selection of international dishes.
           </p>
           <p className="text-lg text-brand-charcoal/80 leading-relaxed">
             We focus on farm-to-table dining, sourcing the freshest organic produce from local Vagamon farmers.
           </p>
        </div>
      </Section>

      <Section background="primary" className="py-24">
        <div className="text-center max-w-3xl mx-auto mb-16 flex flex-col gap-4">
           <span className="tagline text-brand-forest-green uppercase tracking-[0.3em] text-sm font-bold block">Culinary Journeys</span>
           <h2 className="text-4xl md:text-5xl font-heading italic">Beyond the Table</h2>
           <p className="text-brand-charcoal/70">Unique dining experiences tailored to your mood and the moment.</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            <Card className="bg-transparent border-none shadow-none text-center group">
              <div className="relative w-full aspect-square mx-auto mb-6 rounded-3xl overflow-hidden shadow-xl group-hover:shadow-2xl transition-all duration-500">
                 <Image src="https://images.unsplash.com/photo-1551183053-bf91a1d81141?q=80&w=1200" alt="In-Cottage Dining" fill className="object-cover group-hover:scale-110 transition-transform duration-700" />
              </div>
              <CardContent>
                 <h3 className="text-2xl font-heading text-brand-charcoal mb-4">Private Balcony Breakfast</h3>
                 <p className="text-brand-charcoal/70 text-sm leading-relaxed">Enjoy your complimentary morning spread from the comfort of your private cottage balcony, veiled by the morning mist.</p>
              </CardContent>
            </Card>

            <Card className="bg-transparent border-none shadow-none text-center group">
              <div className="relative w-full aspect-square mx-auto mb-6 rounded-3xl overflow-hidden shadow-xl group-hover:shadow-2xl transition-all duration-500">
                 <Image src="https://images.unsplash.com/photo-1601050690597-df0568f70950?q=80&w=1200" alt="Traditional Kerala Sadhya" fill className="object-cover group-hover:scale-110 transition-transform duration-700" />
              </div>
              <CardContent>
                 <h3 className="text-2xl font-heading text-brand-charcoal mb-4">Authentic Sadhya</h3>
                 <p className="text-brand-charcoal/70 text-sm leading-relaxed">Experience a traditional Kerala feast served on a banana leaf, showcasing the vibrant spices and organic vegetables from the region.</p>
              </CardContent>
            </Card>

            <Card className="bg-transparent border-none shadow-none text-center group">
              <div className="relative w-full aspect-square mx-auto mb-6 rounded-3xl overflow-hidden shadow-xl group-hover:shadow-2xl transition-all duration-500">
                 <Image src="https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?q=80&w=1200" alt="Sunset High Tea" fill className="object-cover group-hover:scale-110 transition-transform duration-700" />
              </div>
              <CardContent>
                 <h3 className="text-2xl font-heading text-brand-charcoal mb-4">Sunset High Tea</h3>
                 <p className="text-brand-charcoal/70 text-sm leading-relaxed">Indulge in locally harvested artisanal tea and baked treats while watching the golden hour bathe the Western Ghats.</p>
              </CardContent>
            </Card>
        </div>
      </Section>
    </div>
  );
}
