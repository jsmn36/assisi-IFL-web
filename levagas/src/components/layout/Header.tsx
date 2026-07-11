"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Menu, X, Phone } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { NAVIGATION_LINKS, PROPERTY_INFO } from '@/lib/constants';
import { cn } from '@/lib/utils';

export const Header = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header
      className={cn(
        'fixed top-0 left-0 right-0 z-50 transition-all duration-300 px-6 py-4',
        scrolled ? 'bg-brand-primary-bg/95 backdrop-blur-md shadow-sm py-3' : 'bg-transparent'
      )}
    >
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <span className={cn(
            "text-2xl font-heading tracking-tight",
            scrolled ? "text-brand-forest-green" : "text-brand-charcoal"
          )}>
            LE VAGAS
          </span>
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center gap-8">
          {NAVIGATION_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-brand-charcoal hover:text-brand-forest-green transition-colors"
            >
              {link.name}
            </Link>
          ))}
          <Link href="/book">
            <Button variant="primary" className="ml-4">
              Book Now
            </Button>
          </Link>
        </nav>

        {/* Mobile Toggle */}
        <button
          className="md:hidden p-2 text-brand-charcoal"
          onClick={() => setIsOpen(!isOpen)}
        >
          {isOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Mobile Nav */}
      {isOpen && (
        <div className="md:hidden absolute top-full left-0 right-0 bg-brand-primary-bg border-t border-brand-forest-green/10 p-6 flex flex-col gap-4 shadow-xl animate-in slide-in-from-top duration-300">
          {NAVIGATION_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-lg font-medium text-brand-charcoal"
              onClick={() => setIsOpen(false)}
            >
              {link.name}
            </Link>
          ))}
          <Link href="/book" onClick={() => setIsOpen(false)}>
            <Button variant="primary" className="w-full mt-2">
              Book Now
            </Button>
          </Link>
        </div>
      )}
    </header>
  );
};
