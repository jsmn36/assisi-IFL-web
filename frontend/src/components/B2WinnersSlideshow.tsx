/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Trophy } from 'lucide-react';
import { getB2Winners } from '@/lib/storage';

const FALLBACK = 'https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&q=80&w=800';
const INTERVAL_MS = 3500;

export default function B2WinnersSlideshow() {
  const [winners, setWinners] = useState<any[]>([]);
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    getB2Winners().then(setWinners);
  }, []);

  useEffect(() => {
    if (winners.length < 2 || paused) return;
    const t = setInterval(() => setIndex((i) => (i + 1) % winners.length), INTERVAL_MS);
    return () => clearInterval(t);
  }, [winners.length, paused]);

  const current = winners[index];

  return (
    <div
      className="relative w-full h-[500px] rounded-[2rem] overflow-hidden border border-slate-200 dark:border-white/10 bg-slate-900"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      <AnimatePresence mode="popLayout">
        <motion.img
          key={current?.id ?? 'fallback'}
          src={current?.media_url || FALLBACK}
          alt={current?.title || 'B2 Winners'}
          initial={{ opacity: 0, scale: 1.08, x: 60 }}
          animate={{ opacity: 1, scale: 1, x: 0 }}
          exit={{ opacity: 0, scale: 0.96, x: -60 }}
          transition={{ duration: 0.8, ease: 'easeInOut' }}
          className="absolute inset-0 w-full h-full object-cover"
        />
      </AnimatePresence>

      {current && (
        <>
          <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/10 to-transparent pointer-events-none" />
          <div className="absolute top-5 left-5 flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-400/90 text-slate-900 text-xs font-bold shadow-lg backdrop-blur">
            <Trophy className="h-3.5 w-3.5" /> B2 Winners
          </div>
          <motion.div
            key={`cap-${current.id}`}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="absolute bottom-16 left-0 right-0 px-6 text-right"
          >
            <p className="text-white text-xl font-semibold drop-shadow">{current.title}</p>
            {current.content && <p className="text-amber-200 text-sm">{current.content}</p>}
          </motion.div>
          {winners.length > 1 && (
            <div className="absolute bottom-5 right-6 flex gap-1.5">
              {winners.map((w, i) => (
                <button
                  key={w.id}
                  id={`b2-dot-${i}`}
                  aria-label={`Show winner ${i + 1}`}
                  onClick={() => setIndex(i)}
                  className={`h-1.5 rounded-full transition-all ${i === index ? 'w-6 bg-amber-400' : 'w-1.5 bg-white/50 hover:bg-white'}`}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
