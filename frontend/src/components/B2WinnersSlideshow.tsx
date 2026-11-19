/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { ChevronLeft, ChevronRight, Trophy } from 'lucide-react';
import { getB2Winners } from '@/lib/storage';

const INTERVAL_MS = 5000;
const WINNERS_PER_PAGE = 5; // show 5 winners per certificate (2 top + 3 bottom like the template)

/** Gold laurel wreath around a portrait */
function Wreath({ size = 100, children }: { size?: number; children: React.ReactNode }) {
  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg
        viewBox="0 0 200 200"
        style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}
        aria-hidden
      >
        <defs>
          <linearGradient id="wg" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#c8960c" />
            <stop offset="45%" stopColor="#f5d060" />
            <stop offset="100%" stopColor="#c8960c" />
          </linearGradient>
        </defs>
        {/* left leaf cluster */}
        {[...Array(9)].map((_, i) => {
          const a = -70 + i * 16, r = a * (Math.PI / 180);
          const cx = 100 + 85 * Math.cos(r), cy = 100 + 85 * Math.sin(r);
          return <ellipse key={`l${i}`} cx={cx} cy={cy} rx="10" ry="4.5"
            fill="url(#wg)" transform={`rotate(${a + 90},${cx},${cy})`} opacity="0.92" />;
        })}
        {/* right leaf cluster */}
        {[...Array(9)].map((_, i) => {
          const a = -110 - i * 16, r = a * (Math.PI / 180);
          const cx = 100 + 85 * Math.cos(r), cy = 100 + 85 * Math.sin(r);
          return <ellipse key={`r${i}`} cx={cx} cy={cy} rx="10" ry="4.5"
            fill="url(#wg)" transform={`rotate(${a - 90},${cx},${cy})`} opacity="0.92" />;
        })}
        {/* bottom ribbon */}
        <path d="M 68 180 Q 100 192 132 180" fill="none"
          stroke="url(#wg)" strokeWidth="6" strokeLinecap="round" />
      </svg>
      {children}
    </div>
  );
}

/** Gold shield with order number */
function OrderBadge({ number, badgeSize = 32 }: { number: number; badgeSize?: number }) {
  return (
    <div style={{
      position: 'absolute', bottom: -badgeSize * 0.3,
      left: '50%', transform: 'translateX(-50%)',
      width: badgeSize, height: badgeSize * 1.1, zIndex: 20,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}>
      <svg viewBox="0 0 40 44" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }} aria-hidden>
        <defs>
          <linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f5d060" />
            <stop offset="100%" stopColor="#c8960c" />
          </linearGradient>
        </defs>
        <path d="M20 2 L38 10 L38 24 Q38 38 20 42 Q2 38 2 24 L2 10 Z"
          fill="url(#sg)" stroke="#8B6914" strokeWidth="1.5" />
      </svg>
      <span style={{
        position: 'relative', zIndex: 10,
        fontSize: number >= 100 ? 8 : 10,
        fontWeight: 900, color: '#3d1f00', lineHeight: 1, userSelect: 'none',
      }}>
        {number}
      </span>
    </div>
  );
}

/** One winner portrait: wreath + circle photo + badge + name */
function WinnerPortrait({
  winner, orderNumber, photoSize, badgeSize, nameSize,
}: {
  winner: any; orderNumber: number; photoSize: number; badgeSize?: number; nameSize?: number;
}) {
  const bs = badgeSize ?? Math.round(photoSize * 0.32);
  const ns = nameSize ?? Math.max(10, Math.round(photoSize * 0.14));
  const wreathSize = photoSize * 1.38;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0 }}>
      <div style={{ position: 'relative', width: wreathSize, height: wreathSize }}>
        <Wreath size={wreathSize}>
          {/* portrait circle — sits inside the wreath, NOT on top of cert details */}
          <div style={{
            width: photoSize, height: photoSize, borderRadius: '50%',
            overflow: 'hidden', border: '3px solid #f5d060',
            boxShadow: '0 3px 14px rgba(0,0,0,0.55)',
            position: 'absolute', top: '50%', left: '50%',
            transform: 'translate(-50%,-54%)',   // pull up slightly inside wreath
          }}>
            <img src={winner.media_url} alt={winner.title}
              style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'top' }} />
          </div>
          <OrderBadge number={orderNumber} badgeSize={bs} />
        </Wreath>
      </div>
      {/* name below wreath — outside certificate detail areas */}
      <div style={{
        color: 'white', fontWeight: 700,
        fontSize: ns, textAlign: 'center',
        textShadow: '0 1px 6px rgba(0,0,0,0.7)',
        marginTop: bs * 0.15,
        lineHeight: 1.2, maxWidth: wreathSize + 10,
      }}>
        {winner.title}
      </div>
    </div>
  );
}

/** Full certificate page showing up to 5 winners */
function CertificatePage({
  winners, startIndex,
}: {
  winners: any[]; startIndex: number;
}) {
  // Layout: up to 2 on row 1, rest on row 2 (matches the template)
  const topRow = winners.slice(0, 2);
  const botRow = winners.slice(2, 5);

  // certificate aspect 16:9; we size portraits relative to container
  // Top row portraits sit at ~55-70% right, vertically 10-45%
  // Bot row portraits sit at ~40-85% right, vertically 50-88%
  // We use % positioning so it scales with font/container

  return (
    <div
      className="relative w-full overflow-hidden rounded-2xl shadow-2xl select-none"
      style={{
        aspectRatio: '16/9',
        background: 'linear-gradient(135deg,#1a237e 0%,#283593 40%,#1565c0 100%)',
      }}
    >
      {/* ── Background decorative panels ── */}
      <div style={{ position:'absolute', inset:0, pointerEvents:'none' }}>
        {/* cyan left panel */}
        <div style={{
          position:'absolute', left:0, top:0, bottom:0, width:'30%',
          background:'linear-gradient(170deg,#0097a7 0%,#00bcd4 60%,#4dd0e1 100%)',
          clipPath:'polygon(0 0,100% 0,72% 100%,0 100%)',
        }} />
        {/* darker blue overlay */}
        <div style={{
          position:'absolute', left:0, top:0, bottom:0, width:'20%',
          background:'linear-gradient(170deg,#0d1b5e 0%,#1a2980 100%)',
          clipPath:'polygon(0 0,100% 0,72% 100%,0 100%)',
        }} />
        {/* subtle top-right accent */}
        <div style={{
          position:'absolute', right:0, top:0, width:'28%', height:'32%',
          background:'rgba(100,220,235,0.10)',
          clipPath:'polygon(28% 0,100% 0,100% 100%)',
        }} />
      </div>

      {/* ── Congratulations script ── */}
      <div style={{
        position:'absolute', top:'4%', right:'3%', zIndex:10,
        fontFamily:'Georgia,"Times New Roman",serif', fontStyle:'italic',
        fontSize:'clamp(14px,3.2vw,30px)', color:'white',
        textShadow:'0 2px 10px rgba(0,0,0,0.6)', lineHeight:1,
      }}>
        <span style={{ fontWeight:300 }}>Congratulations</span>
        <svg viewBox="0 0 200 16" style={{ width:'100%', height:'9px', display:'block', marginTop:2 }}>
          <path d="M 0 8 Q 25 2 50 8 T 100 8 T 150 8 T 200 8"
            fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" />
        </svg>
      </div>

      {/* ── Assisi branding ── */}
      <div style={{
        position:'absolute', left:'3%', top:'6%', zIndex:20,
        display:'flex', flexDirection:'column', alignItems:'center', width:'21%',
      }}>
        <div style={{
          width:'clamp(26px,4.5vw,44px)', height:'clamp(26px,4.5vw,44px)',
          border:'2px solid rgba(255,255,255,0.8)', borderRadius:4,
          display:'flex', alignItems:'center', justifyContent:'center',
          marginBottom:4, background:'rgba(255,255,255,0.1)',
        }}>
          <Trophy style={{ color:'white', width:'60%', height:'60%' }} />
        </div>
        <div style={{ color:'white', textAlign:'center', lineHeight:1.25 }}>
          <div style={{ fontSize:'clamp(4px,0.85vw,8px)', fontWeight:600, opacity:0.85, letterSpacing:1, textTransform:'uppercase' }}>
            Dr. K. Luke Memorial
          </div>
          <div style={{ fontSize:'clamp(10px,2vw,20px)', fontWeight:900, letterSpacing:1 }}>
            ASSISI
          </div>
          <div style={{ fontSize:'clamp(4px,0.75vw,7px)', fontWeight:500, opacity:0.85, textTransform:'uppercase', letterSpacing:0.5 }}>
            Institute of Foreign Languages
          </div>
        </div>
      </div>

      {/* ── Orange B2 WINNER chevron banner ── */}
      <div style={{
        position:'absolute', zIndex:20, left:0, bottom:'24%', width:'46%',
        background:'linear-gradient(90deg,#e65100 0%,#ff6d00 65%,#ff8f00 100%)',
        clipPath:'polygon(0 0,88% 0,100% 50%,88% 100%,0 100%)',
        padding:'clamp(5px,1.3vh,13px) clamp(14px,3vw,30px)',
      }}>
        <div style={{
          color:'white', fontWeight:900,
          fontSize:'clamp(13px,2.8vw,28px)', letterSpacing:'0.08em', lineHeight:1,
        }}>
          B2 WINNER
          {winners[0]?.content && (
            <span style={{ fontSize:'0.52em', display:'block', fontWeight:600, opacity:0.9, marginTop:2 }}>
              of {winners[0].content}
            </span>
          )}
        </div>
      </div>

      {/* ── Winners portraits area (right 65%) ── */}
      {/* Positioned so they don't overlap the left panel or banner */}
      <div style={{
        position:'absolute', zIndex:15,
        left:'30%', right:'2%', top:'4%', bottom:'14%',
        display:'flex', flexDirection:'column',
        alignItems:'center', justifyContent:'space-evenly',
        gap: 0,
      }}>
        {/* Top row */}
        {topRow.length > 0 && (
          <div style={{
            display:'flex', justifyContent:'center',
            gap:'clamp(8px,3vw,32px)', alignItems:'flex-end',
            width:'100%',
          }}>
            {topRow.map((w, i) => (
              <WinnerPortrait
                key={w.id}
                winner={w}
                orderNumber={startIndex + i + 1}
                photoSize={Math.round(Math.min(window.innerWidth, 1200) * 0.098)}
                badgeSize={Math.round(Math.min(window.innerWidth, 1200) * 0.032)}
                nameSize={Math.round(Math.min(window.innerWidth, 1200) * 0.013)}
              />
            ))}
          </div>
        )}
        {/* Bottom row */}
        {botRow.length > 0 && (
          <div style={{
            display:'flex', justifyContent:'center',
            gap:'clamp(6px,2.5vw,24px)', alignItems:'flex-end',
            width:'100%',
          }}>
            {botRow.map((w, i) => (
              <WinnerPortrait
                key={w.id}
                winner={w}
                orderNumber={startIndex + topRow.length + i + 1}
                photoSize={Math.round(Math.min(window.innerWidth, 1200) * 0.09)}
                badgeSize={Math.round(Math.min(window.innerWidth, 1200) * 0.030)}
                nameSize={Math.round(Math.min(window.innerWidth, 1200) * 0.012)}
              />
            ))}
          </div>
        )}
      </div>

      {/* ── Bottom contact info ── */}
      <div style={{
        position:'absolute', bottom:0, left:0, right:0, zIndex:20,
        display:'flex', alignItems:'flex-end', justifyContent:'space-between',
        padding:'clamp(4px,1vh,9px) clamp(10px,2.5%,22px)',
      }}>
        <div style={{ color:'rgba(255,255,255,0.72)', fontSize:'clamp(5px,0.78vw,8.5px)', lineHeight:1.6 }}>
          <div style={{ fontWeight:700 }}>Call: 099 612 466 48, 079 943 766 48</div>
          <div>BHARANANGANAM, KOTTAYAM DISTRICT</div>
          <div>assisiifl@gmail.com &nbsp; www.assisiinstitute.org</div>
        </div>
        <div style={{ color:'#ff7043', fontSize:'clamp(5px,0.72vw,8px)', fontWeight:600, textAlign:'right' }}>
          Follow us on: 📧 📘 📸
        </div>
      </div>
    </div>
  );
}

export default function B2WinnersSlideshow() {
  const [winners, setWinners] = useState<any[]>([]);
  const [pageIndex, setPageIndex] = useState(0);
  const [paused, setPaused] = useState(false);

  useEffect(() => { getB2Winners().then(setWinners); }, []);

  // Split winners into pages of WINNERS_PER_PAGE
  const pages: any[][] = [];
  for (let i = 0; i < winners.length; i += WINNERS_PER_PAGE) {
    pages.push(winners.slice(i, i + WINNERS_PER_PAGE));
  }

  useEffect(() => {
    if (pages.length < 2 || paused) return;
    const t = setInterval(() => setPageIndex((p) => (p + 1) % pages.length), INTERVAL_MS);
    return () => clearInterval(t);
  }, [pages.length, paused]);

  const go = (d: number) => setPageIndex((p) => (p + d + pages.length) % pages.length);

  if (winners.length === 0) {
    return (
      <div className="relative w-full overflow-hidden rounded-2xl shadow-2xl flex items-center justify-center"
        style={{ aspectRatio:'16/9', background:'linear-gradient(135deg,#1a237e 0%,#283593 40%,#1565c0 100%)' }}>
        <div style={{
          position:'absolute', left:0, top:0, bottom:0, width:'30%',
          background:'linear-gradient(170deg,#0097a7,#00bcd4)',
          clipPath:'polygon(0 0,100% 0,72% 100%,0 100%)',
        }} />
        <div className="relative z-10 text-center text-white/60 space-y-3">
          <Trophy className="h-16 w-16 mx-auto opacity-40" />
          <p className="text-xl font-semibold">B2 Winners will appear here soon</p>
          <p className="text-sm opacity-60">New winners are added by the admin</p>
        </div>
        <div style={{
          position:'absolute', left:0, bottom:'26%', width:'40%',
          background:'linear-gradient(90deg,#e65100,#ff6d00)',
          clipPath:'polygon(0 0,88% 0,100% 50%,88% 100%,0 100%)',
          padding:'10px 24px',
        }}>
          <div style={{ color:'white', fontWeight:900, fontSize:'clamp(14px,3vw,26px)' }}>B2 WINNER</div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full space-y-4">
      <div className="relative"
        onMouseEnter={() => setPaused(true)}
        onMouseLeave={() => setPaused(false)}>
        <AnimatePresence mode="wait">
          <motion.div
            key={pageIndex}
            initial={{ opacity: 0, x: 70 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -70 }}
            transition={{ duration: 0.55, ease: 'easeInOut' }}
          >
            <CertificatePage
              winners={pages[pageIndex] ?? []}
              startIndex={pageIndex * WINNERS_PER_PAGE}
            />
          </motion.div>
        </AnimatePresence>

        {/* Prev / Next — only shown when multiple pages */}
        {pages.length > 1 && (
          <>
            <button id="b2-prev" aria-label="Previous certificate"
              onClick={() => go(-1)}
              className="absolute left-3 top-1/2 -translate-y-1/2 z-30 p-2.5 rounded-full bg-black/40 hover:bg-black/70 text-white transition-all backdrop-blur-sm border border-white/20">
              <ChevronLeft className="h-5 w-5" />
            </button>
            <button id="b2-next" aria-label="Next certificate"
              onClick={() => go(1)}
              className="absolute right-3 top-1/2 -translate-y-1/2 z-30 p-2.5 rounded-full bg-black/40 hover:bg-black/70 text-white transition-all backdrop-blur-sm border border-white/20">
              <ChevronRight className="h-5 w-5" />
            </button>
          </>
        )}
      </div>

      {/* Page dots */}
      {pages.length > 1 && (
        <div className="flex justify-center gap-2">
          {pages.map((_, i) => (
            <button key={i} id={`b2-page-dot-${i}`}
              aria-label={`Certificate page ${i + 1}`}
              onClick={() => setPageIndex(i)}
              className={`h-2 rounded-full transition-all duration-300 ${
                i === pageIndex ? 'w-8 bg-amber-400' : 'w-2 bg-white/30 hover:bg-amber-300'
              }`} />
          ))}
        </div>
      )}
    </div>
  );
}
