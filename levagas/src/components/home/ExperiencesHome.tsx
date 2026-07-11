import React from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { Section } from '@/components/ui/Section';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { experiences } from '@/data/experiences';

export const ExperiencesHome = () => {
  return (
    <Section background="white">
      <div className="text-center max-w-3xl mx-auto mb-16 flex flex-col gap-4">
        <h2 className="text-4xl md:text-5xl font-heading">Signature Experiences</h2>
        <p className="text-brand-charcoal/70 text-lg">
          Unique hill experiences designed to connect you with nature.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
        {experiences.map((experience, i) => (
          <Card key={i} className="group overflow-hidden flex flex-col h-full border-none shadow-none hover:shadow-xl transition-all duration-500">
            <div className="relative aspect-[4/5] overflow-hidden rounded-xl">
              <Image
                src={experience.image}
                alt={experience.title}
                fill
                className="object-cover group-hover:scale-105 transition-transform duration-700"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-brand-charcoal/80 via-transparent to-transparent opacity-80" />
              <div className="absolute bottom-6 left-6 right-6">
                <span className="text-4xl mb-4 block" role="img" aria-label={experience.title}>
                  {experience.icon}
                </span>
                <h3 className="text-2xl font-heading text-white mb-2">{experience.title}</h3>
              </div>
            </div>
            <CardContent className="px-2 pt-4">
              <p className="text-brand-charcoal/70 text-sm leading-relaxed">
                {experience.description}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-16 text-center">
        <Link href="/experiences">
          <Button variant="secondary" className="px-8 py-3">Explore All Experiences</Button>
        </Link>
      </div>
    </Section>
  );
};
