/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { ChevronLeft, ChevronRight, Trophy } from 'lucide-react';
import { getB2Winners } from '@/lib/storage';

const INTERVAL_MS = 5000;
const PER_PAGE = 4; // winners shown per slide

/** Gold laurel wreath around portrait */
function Wreath({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative flex items-center justify-center w-full">
      <svg
        viewBox="0 0 200 200"
        className="absolute inset-0 w-full h-full pointer-events-none z-10"
        aria-hidden
      >
        <defs>
          <linearGradient id="wg" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#c8960c" />
            <stop offset="45%" stopColor="#f5d060" />
            <stop offset="100%" stopColor="#c8960c" />
          </linearGradient>
        </defs>
        {/* Left side leaves */}
        {[...Array(8)].map((_, i) => {
          const a = -65 + i * 18;
          const r = (a * Math.PI) / 180;
          const cx = 100 + 90 * Math.cos(r);
          const cy = 100 + 90 * Math.sin(r);
          return (
            <ellipse key={`l${i}`} cx={cx} cy={cy} rx="11" ry="5"
              fill="url(#wg)" transform={`rotate(${a + 90},${cx},${cy})`} opacity="0.9" />
          );
        })}
        {/* Right side leaves */}
        {[...Array(8)].map((_, i) => {
          const a = -115 - i * 18;
          const r = (a * Math.PI) / 180;
          const cx = 100 + 90 * Math.cos(r);
          const cy = 100 + 90 * Math.sin(r);
          return (
            <ellipse key={`r${i}`} cx={cx} cy={cy} rx="11" ry="5"
              fill="url(#wg)" transform={`rotate(${a - 90},${cx},${cy})`} opacity="0.9" />
          );
        })}
        {/* Bottom ribbon knot */}
        <path d="M74 182 Q100 194 126 182" fill="none"
          stroke="url(#wg)" strokeWidth="6" strokeLinecap="round" />
      </svg>

      {/* Inner portrait circle */}
      <div className="relative z-20 w-[72%] aspect-square">
        {children}
      </div>
    </div>
  );
}

/** Gold shield with order number */
function Badge({ number }: { number: number }) {
  return (
    <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 z-30">
      <div className="relative flex items-center justify-center" style={{ width: 28, height: 32 }}>
        <svg viewBox="0 0 40 44" className="absolute inset-0 w-full h-full" aria-hidden>
          <defs>
            <linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f5d060" />
              <stop offset="100%" stopColor="#c8960c" />
            </linearGradient>
          </defs>
          <path d="M20 2 L38 10 L38 24 Q38 38 20 42 Q2 38 2 24 L2 10 Z"
            fill="url(#sg)" stroke="#8B6914" strokeWidth="1.5" />
        </svg>
        <span className="relative z-10 font-black text-[#3d1f00] leading-none select-none"
          style={{ fontSize: 10 }}>
          {number}
        </span>
      </div>
    </div>
  );
}

/** One winner portrait slot (wreath + photo + badge + name) */
function WinnerSlot({ winner, orderNumber }: { winner: any; orderNumber: number }) {
  return (
    <div className="flex flex-col items-center gap-1" style={{ width: '44%' }}>
      {/* Wreath + photo */}
      <div className="relative w-full">
        <Wreath>
          <div className="w-full h-full rounded-full overflow-hidden border-2 border-yellow-300 shadow-lg">
            <img
              src={winner.media_url}
              alt={winner.title}
              style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'top' }}
            />
          </div>
          <Badge number={orderNumber} />
        </Wreath>
      </div>
      {/* Name */}
      <p style={{
        color: 'white',
        fontWeight: 700,
        fontSize: 'clamp(8px, 1.3vw, 13px)',
        textAlign: 'center',
        textShadow: '0 1px 4px rgba(0,0,0,0.7)',
        marginTop: 6,
        lineHeight: 1.2,
        maxWidth: '90%',
      }}>
        {winner.title}
      </p>
    </div>
  );
}

/** Left fixed panel — Assisi branding + B2 banner (never changes between slides) */
function LeftPanel({ year }: { year?: string }) {
  return (
    <>
      {/* Cyan diagonal accent */}
      <div style={{
        position: 'absolute', left: 0, top: 0, bottom: 0, width: '38%',
        background: 'linear-gradient(170deg,#0097a7 0%,#00bcd4 55%,#4dd0e1 100%)',
        clipPath: 'polygon(0 0,100% 0,75% 100%,0 100%)',
        zIndex: 1,
      }} />
      {/* Dark navy stripe */}
      <div style={{
        position: 'absolute', left: 0, top: 0, bottom: 0, width: '25%',
        background: 'linear-gradient(170deg,#0d1b5e 0%,#1a2980 100%)',
        clipPath: 'polygon(0 0,100% 0,72% 100%,0 100%)',
        zIndex: 2,
      }} />
      {/* Top-right subtle accent */}
      <div style={{
        position: 'absolute', right: 0, top: 0, width: '20%', height: '28%',
        background: 'rgba(100,220,235,0.10)',
        clipPath: 'polygon(30% 0,100% 0,100% 100%)',
        zIndex: 1,
      }} />

      {/* Assisi logo block */}
      <div style={{
        position: 'absolute', left: '3%', top: '7%',
        width: '32%', zIndex: 10,
        display: 'flex', flexDirection: 'column', alignItems: 'center',
      }}>
        <div style={{
          width: 'clamp(26px,4.5%,42px)', height: 'clamp(26px,4.5%,42px)',
          border: '2px solid rgba(255,255,255,0.8)', borderRadius: 4,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          marginBottom: 4, background: 'rgba(255,255,255,0.1)',
        }}>
          <Trophy style={{ color: 'white', width: '60%', height: '60%' }} />
        </div>
        <div style={{ color: 'white', textAlign: 'center', lineHeight: 1.3 }}>
          <div style={{ fontSize: 'clamp(5px,0.85vw,8px)', fontWeight: 600, opacity: 0.85, letterSpacing: 1, textTransform: 'uppercase' }}>
            Dr. K. Luke Memorial
          </div>
          <div style={{ fontSize: 'clamp(10px,1.9vw,20px)', fontWeight: 900, letterSpacing: 1 }}>
            ASSISI
          </div>
          <div style={{ fontSize: 'clamp(4px,0.75vw,7px)', fontWeight: 500, opacity: 0.85, textTransform: 'uppercase', letterSpacing: 0.5 }}>
            Institute of Foreign Languages
          </div>
        </div>
      </div>

      {/* Orange B2 WINNER chevron banner */}
      <div style={{
        position: 'absolute', left: 0, bottom: '24%', width: '48%',
        background: 'linear-gradient(90deg,#e65100 0%,#ff6d00 65%,#ff8f00 100%)',
        clipPath: 'polygon(0 0,86% 0,100% 50%,86% 100%,0 100%)',
        padding: 'clamp(6px,1.3vh,12px) clamp(14px,3vw,28px)',
        zIndex: 10,
      }}>
        <div style={{
          color: 'white', fontWeight: 900,
          fontSize: 'clamp(13px,2.6vw,26px)', letterSpacing: '0.08em', lineHeight: 1,
        }}>
          B2 WINNER
          {year && (
            <span style={{ fontSize: '0.5em', display: 'block', fontWeight: 600, opacity: 0.9, marginTop: 2 }}>
              of {year}
            </span>
          )}
        </div>
      </div>

      {/* Bottom contact bar */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0,
        display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end',
        padding: 'clamp(5px,1.1vh,10px) clamp(10px,2.5%,20px)',
        zIndex: 10,
      }}>
        <div style={{ color: 'rgba(255,255,255,0.72)', fontSize: 'clamp(5px,0.75vw,8px)', lineHeight: 1.6 }}>
          <div style={{ fontWeight: 700 }}>Call: 099 612 466 48, 079 943 766 48</div>
          <div>BHARANANGANAM, KOTTAYAM DISTRICT</div>
          <div>assisiifl@gmail.com &nbsp; www.assisiinstitute.org</div>
        </div>
        <div style={{ color: '#ff7043', fontSize: 'clamp(5px,0.7vw,7.5px)', fontWeight: 600, textAlign: 'right' }}>
          Follow us on: 📧 📘 📸
        </div>
      </div>
    </>
  );
}

/** Sliding right panel — 4 winners in 2×2 grid */
function WinnersGrid({ group, startIndex }: { group: any[]; startIndex: number }) {
  // Always render 4 slots (empty if group has fewer)
  const slots = [...group, ...Array(4 - group.length).fill(null)];

  return (
    <div style={{
      position: 'absolute',
      left: '36%',
      top: '8%',
      right: '2%',
      bottom: '12%',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-evenly',
      zIndex: 20,
    }}>
      {/* Row 1 */}
      <div style={{ display: 'flex', justifyContent: 'space-evenly', alignItems: 'flex-end' }}>
        {slots.slice(0, 2).map((winner, i) =>
          winner ? (
            <WinnerSlot key={winner.id} winner={winner} orderNumber={startIndex + i + 1} />
          ) : (
            <div key={i} style={{ width: '44%' }} />
          )
        )}
      </div>
      {/* Row 2 */}
      <div style={{ display: 'flex', justifyContent: 'space-evenly', alignItems: 'flex-end' }}>
        {slots.slice(2, 4).map((winner, i) =>
          winner ? (
            <WinnerSlot key={winner.id} winner={winner} orderNumber={startIndex + i + 3} />
          ) : (
            <div key={i} style={{ width: '44%' }} />
          )
        )}
      </div>
    </div>
  );
}

export default function B2WinnersSlideshow() {
  const [winners, setWinners] = useState<any[]>([]);
  const [pageIndex, setPageIndex] = useState(0);
  const [paused, setPaused] = useState(false);

  useEffect(() => { getB2Winners().then(setWinners); }, []);

  const totalPages = Math.max(1, Math.ceil(winners.length / PER_PAGE));

  useEffect(() => {
    if (totalPages < 2 || paused) return;
    const t = setInterval(() => setPageIndex((p) => (p + 1) % totalPages), INTERVAL_MS);
    return () => clearInterval(t);
  }, [totalPages, paused]);

  const go = (d: number) => setPageIndex((p) => (p + d + totalPages) % totalPages);

  const currentGroup = winners.slice(pageIndex * PER_PAGE, pageIndex * PER_PAGE + PER_PAGE);
  const year = currentGroup[0]?.content || '';

  return (
    <div className="w-full space-y-4">
      <div
        className="relative"
        onMouseEnter={() => setPaused(true)}
        onMouseLeave={() => setPaused(false)}
      >
        {/* Certificate shell — always visible, never slides */}
        <div
          className="relative w-full overflow-hidden rounded-2xl shadow-2xl select-none"
          style={{
            aspectRatio: '16/9',
            background: 'linear-gradient(135deg,#1a237e 0%,#283593 40%,#1565c0 100%)',
          }}
        >
          {/* "Congratulations" — fixed top right */}
          <div style={{
            position: 'absolute', top: '4%', right: '3%', zIndex: 15,
            fontFamily: 'Georgia,"Times New Roman",serif', fontStyle: 'italic',
            fontSize: 'clamp(16px,3.2vw,32px)', color: 'white',
            textShadow: '0 2px 8px rgba(0,0,0,0.5)', lineHeight: 1,
          }}>
            <span style={{ fontWeight: 300 }}>Congratulations</span>
            <svg viewBox="0 0 200 16" style={{ width: '100%', height: 10, display: 'block', marginTop: 2 }}>
              <path d="M 0 8 Q 25 2 50 8 T 100 8 T 150 8 T 200 8"
                fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </div>

          {/* Fixed left panel — always stays put */}
          <LeftPanel year={year} />

          {/* RIGHT PANEL: animated winner grid slides in/out */}
          {winners.length > 0 ? (
            <AnimatePresence mode="wait">
              <motion.div
                key={pageIndex}
                initial={{ opacity: 0, x: 80 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -80 }}
                transition={{ duration: 0.55, ease: 'easeInOut' }}
                style={{ position: 'absolute', inset: 0, zIndex: 20, pointerEvents: 'none' }}
              >
                <WinnersGrid group={currentGroup} startIndex={pageIndex * PER_PAGE} />
              </motion.div>
            </AnimatePresence>
          ) : (
            /* Empty state — 4 placeholder circles */
            <div style={{
              position: 'absolute', left: '36%', top: '8%', right: '2%', bottom: '12%',
              display: 'flex', flexDirection: 'column', justifyContent: 'space-evenly', zIndex: 20,
            }}>
              {[[0,1],[2,3]].map((row, ri) => (
                <div key={ri} style={{ display: 'flex', justifyContent: 'space-evenly', alignItems: 'center' }}>
                  {row.map((i) => (
                    <div key={i} style={{
                      width: '44%', aspectRatio: '1',
                      borderRadius: '50%',
                      border: '3px solid rgba(255,255,255,0.25)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      <Trophy style={{ color: 'rgba(255,255,255,0.3)', width: '35%', height: '35%' }} />
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}

          {/* Prev / Next arrows */}
          {totalPages > 1 && (
            <>
              <button id="b2-prev" aria-label="Previous group" onClick={() => go(-1)}
                className="absolute left-[37%] top-1/2 -translate-y-1/2 z-30 p-2 rounded-full bg-black/40 hover:bg-black/70 text-white transition-all border border-white/20 backdrop-blur-sm">
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button id="b2-next" aria-label="Next group" onClick={() => go(1)}
                className="absolute right-2 top-1/2 -translate-y-1/2 z-30 p-2 rounded-full bg-black/40 hover:bg-black/70 text-white transition-all border border-white/20 backdrop-blur-sm">
                <ChevronRight className="h-4 w-4" />
              </button>
            </>
          )}
        </div>
      </div>

      {/* Page dots */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          {Array.from({ length: totalPages }).map((_, i) => (
            <button
              key={i}
              id={`b2-dot-${i}`}
              aria-label={`Page ${i + 1}`}
              onClick={() => setPageIndex(i)}
              className={`h-2 rounded-full transition-all duration-300 ${
                i === pageIndex ? 'w-8 bg-amber-400' : 'w-2 bg-white/30 hover:bg-amber-300'
              }`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
