import React from 'react';
import Image from 'next/image';
import { Section } from '@/components/ui/Section';

export const metadata = {
  title: 'Gallery | Le Vagas Resort',
  description: 'A visual journey through the mist, luxury, and serenity of Le Vagas.',
};

const GALLERY_IMAGES = [
  {
    src: 'https://images.unsplash.com/photo-1542314831-c6a4d14d8373?q=80&w=1200',
    alt: 'Mist Valley Cottage — sunrise view from private balcony',
  },
  {
    src: 'https://images.unsplash.com/photo-1566073771259-6a8506099945?q=80&w=1200',
    alt: 'Celeste Honeymoon Villa — panoramic 270° hill views',
  },
  {
    src: 'https://images.unsplash.com/photo-1501785888041-af3ef285b470?q=80&w=1200',
    alt: 'Emerald Hills Cottage — lush tea garden landscape',
  },
  {
    src: 'https://images.unsplash.com/photo-1493809842364-78817add7ffb?q=80&w=1200',
    alt: 'Golden Peak Cottage — golden-hour sunset over the western hills',
  },
  {
    src: 'https://images.unsplash.com/photo-1440186347098-386b7459ad6b?q=80&w=1200',
    alt: 'Cloud Breeze Cottage — open valley with morning cloud cover',
  },
  {
    src: 'https://images.unsplash.com/photo-1512918728675-ed5a9ecdebfd?q=80&w=1200',
    alt: 'Cottage interior — king bed with valley-view window',
  },
  {
    src: 'https://images.unsplash.com/photo-1584622650111-993a426fbf0a?q=80&w=1200',
    alt: 'Private balcony — morning tea with misty hill backdrop',
  },
  {
    src: 'https://images.unsplash.com/photo-1578683010236-d716f9a3f461?q=80&w=1200',
    alt: 'Celeste Villa — private jacuzzi with valley views',
  },
];

export default function GalleryPage() {
  return (
    <div className="pt-24 min-h-screen bg-brand-primary-bg/20">
      <Section background="white">
        <div className="max-w-6xl mx-auto flex flex-col gap-12 text-center">
          <h1 className="text-5xl font-heading text-brand-forest-green italic">Gallery</h1>
          <p className="text-xl text-brand-charcoal/70 font-light max-w-2xl mx-auto">
            A visual journey through the mist, luxury, and serenity of Le Vagas.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-8">
            {GALLERY_IMAGES.map((image, i) => (
              <div
                key={i}
                className="relative aspect-square rounded-xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-500 group"
              >
                <Image
                  src={image.src}
                  alt={image.alt}
                  fill
                  className="object-cover group-hover:scale-110 transition-transform duration-700"
                  sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                />
              </div>
            ))}
          </div>
        </div>
      </Section>
    </div>
  );
}
