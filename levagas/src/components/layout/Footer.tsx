import React from 'react';
import Link from 'next/link';
import { Mail, Phone, MapPin, Globe, Share2 } from 'lucide-react';
import { PROPERTY_INFO, NAVIGATION_LINKS } from '@/lib/constants';

export const Footer = () => {
  return (
    <footer className="bg-brand-forest-green text-white pt-16 pb-8">
      <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12">
        {/* Brand Column */}
        <div className="flex flex-col gap-6">
          <h2 className="text-3xl font-heading tracking-tight italic text-white">LE VAGAS</h2>
          <p className="text-white/90 text-sm leading-relaxed">
            Experience the perfect blend of luxury and nature in the heart of Vagamon.
          </p>
          <div className="flex gap-4">
            <Link href="https://instagram.com" aria-label="Le Vagas on Instagram" className="text-white hover:text-brand-gold transition-colors">
              <Globe size={20} />
            </Link>
            <Link href="https://facebook.com" aria-label="Le Vagas on Facebook" className="text-white hover:text-brand-gold transition-colors">
              <Share2 size={20} />
            </Link>
          </div>
        </div>

        {/* Quick Links */}
        <div className="flex flex-col gap-6">
          <h3 className="text-lg font-semibold uppercase tracking-wider text-white">Quick Links</h3>
          <ul className="flex flex-col gap-3">
            {NAVIGATION_LINKS.map((link) => (
              <li key={link.href}>
                <Link href={link.href} className="text-white/90 hover:text-white transition-colors text-sm">
                  {link.name}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        {/* Contact Info */}
        <div className="flex flex-col gap-6">
          <h3 className="text-lg font-semibold uppercase tracking-wider text-white">Contact Us</h3>
          <ul className="flex flex-col gap-4">
            <li className="flex gap-3 text-sm text-white/90">
              <MapPin size={18} className="shrink-0 text-brand-gold" aria-hidden="true" />
              <span>{PROPERTY_INFO.address.full}</span>
            </li>
            <li className="flex gap-3 text-sm text-white/90">
              <Phone size={18} className="shrink-0 text-brand-gold" aria-hidden="true" />
              <span>{PROPERTY_INFO.phone}</span>
            </li>
            <li className="flex gap-3 text-sm text-white/90">
              <Mail size={18} className="shrink-0 text-brand-gold" aria-hidden="true" />
              <span>{PROPERTY_INFO.email}</span>
            </li>
          </ul>
        </div>

        {/* Legal */}
        <div className="flex flex-col gap-6">
          <h3 className="text-lg font-semibold uppercase tracking-wider text-white">Legal</h3>
          <ul className="flex flex-col gap-3">
            <li>
              <Link href="/privacy-policy" className="text-white/90 hover:text-white transition-colors text-sm">
                Privacy Policy
              </Link>
            </li>
            <li>
              <Link href="/terms-conditions" className="text-white/90 hover:text-white transition-colors text-sm">
                Terms & Conditions
              </Link>
            </li>
            <li>
              <Link href="/cancellation-policy" className="text-white/90 hover:text-white transition-colors text-sm">
                Cancellation Policy
              </Link>
            </li>
          </ul>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 mt-16 pt-8 border-t border-white/10 flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-white/90">
        <p>© {new Date().getFullYear()} Le Vagas Resort. All rights reserved.</p>
        <p>Designed with ❤️ for Serenity &amp; Luxury</p>
      </div>
    </footer>
  );
};
