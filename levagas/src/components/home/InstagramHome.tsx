import React from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { Camera } from 'lucide-react';
import { Section } from '@/components/ui/Section';
import { PROPERTY_INFO } from '@/lib/constants';

const INSTAGRAM_POSTS = [
  'https://images.unsplash.com/photo-1501785888041-af3ef285b470?q=80&w=400',
  'https://images.unsplash.com/photo-1449844908441-8829872d2607?q=80&w=400',
  'https://images.unsplash.com/photo-1493809842364-78817add7ffb?q=80&w=400',
  'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?q=80&w=400',
  'https://images.unsplash.com/photo-1544161515-4ab6ce6db874?q=80&w=400',
  'https://images.unsplash.com/photo-1576402121774-709de7db76ca?q=80&w=400',
];

export const InstagramHome = () => {
  return (
    <Section background="white">
      <div className="flex flex-col md:flex-row justify-between items-end gap-8 mb-12">
        <div className="flex flex-col gap-4">
          <h2 className="text-4xl md:text-5xl font-heading">Moments at Le Vagas</h2>
          <p className="text-brand-charcoal/70 text-lg max-w-xl">
            Follow our journey and discover the beauty of Vagamon through the eyes of our guests.
          </p>
        </div>
        <Link 
          href={`https://instagram.com/${PROPERTY_INFO.instagram.replace('@', '')}`}
          target="_blank"
          className="flex items-center gap-3 text-brand-forest-green font-bold text-lg hover:text-brand-deep-green transition-colors"
        >
          <Camera size={24} />
          {PROPERTY_INFO.instagram}
        </Link>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {INSTAGRAM_POSTS.map((post, i) => (
          <div key={i} className="group relative aspect-square rounded-xl overflow-hidden cursor-pointer shadow-sm hover:shadow-xl transition-all duration-500">
            <Image
              src={post}
              alt={`Instagram post ${i + 1}`}
              fill
              className="object-cover group-hover:scale-110 transition-transform duration-700"
            />
            <div className="absolute inset-0 bg-brand-forest-green/20 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
              <Camera className="text-white" size={32} />
            </div>
          </div>
        ))}
      </div>
    </Section>
  );
};
