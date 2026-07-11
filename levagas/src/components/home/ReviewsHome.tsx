import React from 'react';
import Image from 'next/image';
import { Star } from 'lucide-react';
import { Section } from '@/components/ui/Section';
import { Card, CardContent } from '@/components/ui/Card';
import { reviews } from '@/data/reviews';

export const ReviewsHome = () => {
  return (
    <Section background="primary">
      <div className="text-center max-w-3xl mx-auto mb-16 flex flex-col gap-4">
        <h2 className="text-4xl md:text-5xl font-heading">What Our Guests Say</h2>
        <p className="text-brand-charcoal/70 text-lg">
          Hear from those who have experienced the magic of Le Vagas.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {reviews.map((review, i) => (
          <Card key={i} className="bg-white/50 backdrop-blur-sm border-none shadow-none hover:bg-white transition-colors duration-500">
            <CardContent className="pt-8 flex flex-col gap-6">
              <div className="flex gap-1 text-brand-gold">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} size={16} fill="currentColor" className={i < review.stars ? "text-brand-gold" : "text-brand-warm-gray/30"} />
                ))}
              </div>
              <p className="text-brand-charcoal/80 text-lg leading-relaxed italic mb-8 relative z-10">
                &quot;{review.text}&quot;
              </p>
              <div className="flex items-center gap-4 mt-auto pt-6 border-t border-brand-forest-green/10">
                <div className="relative w-12 h-12 rounded-full overflow-hidden shrink-0 border-2 border-brand-forest-green/20">
                  <Image
                    src={review.avatar}
                    alt={review.author}
                    fill
                    className="object-cover"
                  />
                </div>
                <div className="flex flex-col">
                  <span className="font-bold text-brand-charcoal text-sm">{review.author}</span>
                  <span className="text-xs text-brand-warm-gray">{review.meta}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </Section>
  );
};
