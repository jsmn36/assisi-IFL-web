import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { BookOpen, ChevronLeft, ChevronRight, Download, X } from 'lucide-react';

const PAGES = [
  { src: '/brochure/page-1.jpg', title: '916 German – A1 Batch' },
  { src: '/brochure/page-2.jpg', title: 'New Batches 2026-27 · A1–B2' },
  { src: '/brochure/page-3.jpg', title: 'Bridge Course B2+' },
  { src: '/brochure/page-4.jpg', title: 'A1 New Batch – Admission Open' },
];
const PDF_URL = '/brochure/Assisi-IFL-Brochure.pdf';

function DownloadButton({ className = '' }: { className?: string }) {
  return (
    <a
      id="brochure-download"
      href={PDF_URL}
      download="Assisi-IFL-Brochure.pdf"
      className={`inline-flex items-center gap-2 px-6 py-3 rounded-full bg-gradient-to-r from-red-600 to-amber-500 text-white font-semibold text-sm shadow-lg shadow-red-500/20 hover:shadow-red-500/40 hover:scale-[1.03] transition-all ${className}`}
    >
      <Download className="h-4 w-4" /> Download PDF
    </a>
  );
}

export default function BrochureSection() {
  const [open, setOpen] = useState<number | null>(null);

  useEffect(() => {
    if (open === null) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(null);
      if (e.key === 'ArrowRight') setOpen((i) => ((i ?? 0) + 1) % PAGES.length);
      if (e.key === 'ArrowLeft') setOpen((i) => ((i ?? 0) - 1 + PAGES.length) % PAGES.length);
    };
    window.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => { window.removeEventListener('keydown', onKey); document.body.style.overflow = ''; };
  }, [open]);

  return (
    <motion.div
      id="brochure"
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8 }}
      viewport={{ once: true }}
      className="max-w-7xl mx-auto relative z-10 mt-20"
    >
      <div className="relative overflow-hidden rounded-[2rem] border border-slate-200 dark:border-white/10 bg-white dark:bg-white/[0.04] shadow-xl p-8 md:p-12">
        <div className="absolute -top-24 -right-24 w-80 h-80 bg-amber-200/50 dark:bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-80 h-80 bg-red-200/40 dark:bg-red-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative grid lg:grid-cols-[1fr_2fr] gap-10 items-center">
          <div>
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 text-xs font-semibold text-red-700 dark:text-red-300 mb-5">
              <BookOpen className="h-3.5 w-3.5" /> Course Brochure
            </div>
            <h3 className="text-4xl md:text-5xl font-semibold tracking-tight text-slate-900 dark:text-white mb-4">
              Our <span className="text-transparent bg-clip-text bg-gradient-to-r from-red-600 to-amber-500">Brochure</span>
            </h3>
            <p className="text-slate-500 dark:text-slate-400 font-light mb-8">
              New batches, A1–B2 courses, the B2+ bridge course and more. Tap a page to view it, or download the full brochure as a PDF.
            </p>
            <div className="flex flex-wrap gap-3">
              <button
                id="brochure-view"
                onClick={() => setOpen(0)}
                className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-semibold text-sm hover:scale-[1.03] transition-all"
              >
                <BookOpen className="h-4 w-4" /> View Brochure
              </button>
              <DownloadButton />
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {PAGES.map((p, i) => (
              <motion.button
                key={p.src}
                id={`brochure-page-${i + 1}`}
                onClick={() => setOpen(i)}
                whileHover={{ y: -8, rotate: i % 2 ? 1.5 : -1.5 }}
                className="group relative rounded-2xl overflow-hidden shadow-lg ring-1 ring-black/5 dark:ring-white/10 bg-slate-100 aspect-[9/14]"
              >
                <img src={p.src} alt={p.title} loading="lazy" className="w-full h-full object-cover object-top" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-3">
                  <span className="text-white text-xs font-medium text-left">{p.title}</span>
                </div>
              </motion.button>
            ))}
          </div>
        </div>
      </div>

      <AnimatePresence>
        {open !== null && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] bg-black/90 backdrop-blur-xl flex flex-col items-center justify-center p-4"
            onClick={() => setOpen(null)}
          >
            <div className="absolute top-4 right-4 flex items-center gap-3" onClick={(e) => e.stopPropagation()}>
              <DownloadButton />
              <button id="brochure-close" onClick={() => setOpen(null)} className="p-3 rounded-full bg-white/10 hover:bg-white/20 text-white">
                <X className="h-5 w-5" />
              </button>
            </div>
            <button onClick={(e) => { e.stopPropagation(); setOpen((open - 1 + PAGES.length) % PAGES.length); }} className="absolute left-4 p-3 rounded-full bg-white/10 hover:bg-white/20 text-white">
              <ChevronLeft className="h-6 w-6" />
            </button>
            <button onClick={(e) => { e.stopPropagation(); setOpen((open + 1) % PAGES.length); }} className="absolute right-4 p-3 rounded-full bg-white/10 hover:bg-white/20 text-white">
              <ChevronRight className="h-6 w-6" />
            </button>
            <motion.img
              key={open}
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              src={PAGES[open].src}
              alt={PAGES[open].title}
              onClick={(e) => e.stopPropagation()}
              className="max-h-[82vh] w-auto rounded-xl shadow-2xl"
            />
            <div className="mt-4 flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
              {PAGES.map((_, i) => (
                <button key={i} onClick={() => setOpen(i)} className={`h-2 rounded-full transition-all ${i === open ? 'w-8 bg-white' : 'w-2 bg-white/40'}`} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
