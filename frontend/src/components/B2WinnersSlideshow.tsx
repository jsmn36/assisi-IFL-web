/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { ChevronLeft, ChevronRight, Trophy } from 'lucide-react';
import { getB2Winners } from '@/lib/storage';

const INTERVAL_MS = 5000;

/** Gold laurel wreath around a portrait */
function Wreath({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative flex items-center justify-center">
      <svg
        viewBox="0 0 200 200"
        className="absolute inset-0 w-full h-full pointer-events-none"
        aria-hidden
      >
        <defs>
          <linearGradient id="wreathGold" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#c8960c" />
            <stop offset="40%" stopColor="#f5d060" />
            <stop offset="100%" stopColor="#c8960c" />
          </linearGradient>
        </defs>
        {[...Array(9)].map((_, i) => {
          const angle = -70 + i * 16;
          const r = angle * (Math.PI / 180);
          const cx = 100 + 88 * Math.cos(r);
          const cy = 100 + 88 * Math.sin(r);
          return (
            <ellipse key={`l${i}`} cx={cx} cy={cy} rx="10" ry="5"
              fill="url(#wreathGold)"
              transform={`rotate(${angle + 90}, ${cx}, ${cy})`} opacity="0.9" />
          );
        })}
        {[...Array(9)].map((_, i) => {
          const angle = -110 - i * 16;
          const r = angle * (Math.PI / 180);
          const cx = 100 + 88 * Math.cos(r);
          const cy = 100 + 88 * Math.sin(r);
          return (
            <ellipse key={`r${i}`} cx={cx} cy={cy} rx="10" ry="5"
              fill="url(#wreathGold)"
              transform={`rotate(${angle - 90}, ${cx}, ${cy})`} opacity="0.9" />
          );
        })}
        <path d="M 72 178 Q 100 190 128 178" fill="none"
          stroke="url(#wreathGold)" strokeWidth="6" strokeLinecap="round" />
      </svg>
      {children}
    </div>
  );
}

/** Gold shield order-number badge */
function OrderBadge({ number }: { number: number }) {
  return (
    <div className="absolute -bottom-3 left-1/2 -translate-x-1/2 z-20">
      <div className="relative flex items-center justify-center w-10 h-10">
        <svg viewBox="0 0 40 44" className="absolute inset-0 w-full h-full" aria-hidden>
          <defs>
            <linearGradient id="shieldGold" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f5d060" />
              <stop offset="100%" stopColor="#c8960c" />
            </linearGradient>
          </defs>
          <path d="M20 2 L38 10 L38 24 Q38 38 20 42 Q2 38 2 24 L2 10 Z"
            fill="url(#shieldGold)" stroke="#8B6914" strokeWidth="1.5" />
        </svg>
        <span className="relative z-10 text-[11px] font-black text-[#3d1f00] leading-none select-none">
          {number}
        </span>
      </div>
    </div>
  );
}

/** Full certificate card styled after the Assisi B2 Winner template */
function CertificateCard({ winner, orderNumber }: { winner: any; orderNumber: number }) {
  return (
    <div
      className="relative w-full overflow-hidden rounded-2xl shadow-2xl select-none"
      style={{
        aspectRatio: '16/9',
        background: 'linear-gradient(135deg, #1a237e 0%, #283593 40%, #1565c0 100%)',
      }}
    >
      {/* ── Diagonal accent panels ── */}
      <div className="absolute inset-0 pointer-events-none" aria-hidden>
        <div style={{
          position:'absolute', left:0, top:0, bottom:0, width:'30%',
          background:'linear-gradient(170deg,#0097a7 0%,#00bcd4 60%,#4dd0e1 100%)',
          clipPath:'polygon(0 0,100% 0,72% 100%,0 100%)',
        }} />
        <div style={{
          position:'absolute', left:0, top:0, bottom:0, width:'20%',
          background:'linear-gradient(170deg,#0d1b5e 0%,#1a2980 100%)',
          clipPath:'polygon(0 0,100% 0,72% 100%,0 100%)',
        }} />
        <div style={{
          position:'absolute', right:0, top:0, width:'25%', height:'30%',
          background:'rgba(100,220,235,0.12)',
          clipPath:'polygon(30% 0,100% 0,100% 100%)',
        }} />
      </div>

      {/* ── Congratulations script ── */}
      <div className="absolute top-[4%] right-[3%] z-10" style={{
        fontFamily:'Georgia,"Times New Roman",serif', fontStyle:'italic',
        fontSize:'clamp(16px,3.5vw,34px)', color:'white',
        textShadow:'0 2px 8px rgba(0,0,0,0.5)', lineHeight:1,
      }}>
        <span style={{ fontWeight:300 }}>Congratulations</span>
        <svg viewBox="0 0 200 16" style={{ width:'100%', height:'10px', display:'block', marginTop:2 }}>
          <path d="M 0 8 Q 25 2 50 8 T 100 8 T 150 8 T 200 8"
            fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" />
        </svg>
      </div>

      {/* ── Assisi branding (inside left panel) ── */}
      <div className="absolute left-[3%] top-[6%] z-20 flex flex-col items-center w-[22%]">
        <div style={{
          width:'clamp(28px,5%,46px)', height:'clamp(28px,5%,46px)',
          border:'2px solid rgba(255,255,255,0.8)', borderRadius:4,
          display:'flex', alignItems:'center', justifyContent:'center',
          marginBottom:4, background:'rgba(255,255,255,0.1)',
        }}>
          <Trophy style={{ color:'white', width:'60%', height:'60%' }} />
        </div>
        <div style={{ color:'white', textAlign:'center', lineHeight:1.25 }}>
          <div style={{ fontSize:'clamp(5px,0.9vw,8px)', fontWeight:600, opacity:0.85, letterSpacing:1, textTransform:'uppercase' }}>
            Dr. K. Luke Memorial
          </div>
          <div style={{ fontSize:'clamp(10px,2vw,20px)', fontWeight:900, letterSpacing:1 }}>
            ASSISI
          </div>
          <div style={{ fontSize:'clamp(5px,0.8vw,7px)', fontWeight:500, opacity:0.85, textTransform:'uppercase', letterSpacing:0.5 }}>
            Institute of Foreign Languages
          </div>
        </div>
      </div>

      {/* ── Orange B2 WINNER chevron banner ── */}
      <div className="absolute z-20" style={{
        left:0, bottom:'26%', width:'46%',
        background:'linear-gradient(90deg,#e65100 0%,#ff6d00 60%,#ff8f00 100%)',
        clipPath:'polygon(0 0,88% 0,100% 50%,88% 100%,0 100%)',
        padding:'clamp(6px,1.4vh,13px) clamp(14px,3vw,30px)',
      }}>
        <div style={{
          color:'white', fontWeight:900,
          fontSize:'clamp(13px,2.8vw,28px)', letterSpacing:'0.08em', lineHeight:1,
        }}>
          B2 WINNER
          {winner.content && (
            <span style={{ fontSize:'0.52em', display:'block', fontWeight:600, opacity:0.9, marginTop:2 }}>
              of {winner.content}
            </span>
          )}
        </div>
      </div>

      {/* ── Winner portrait with wreath + badge ── */}
      <div className="absolute z-20" style={{
        right:'5%', top:'8%', width:'clamp(110px,26%,220px)',
      }}>
        <Wreath>
          <div style={{
            width:'76%', aspectRatio:'1', borderRadius:'50%',
            overflow:'hidden', border:'3px solid #f5d060',
            boxShadow:'0 4px 24px rgba(0,0,0,0.5)',
            margin:'0 auto', position:'relative',
          }}>
            <img src={winner.media_url} alt={winner.title}
              style={{ width:'100%', height:'100%', objectFit:'cover', objectPosition:'top' }} />
          </div>
          <OrderBadge number={orderNumber} />
        </Wreath>
        <div style={{
          textAlign:'center', marginTop:'clamp(14px,3%,22px)',
          color:'white', fontWeight:700,
          fontSize:'clamp(11px,1.8vw,17px)',
          textShadow:'0 1px 6px rgba(0,0,0,0.6)',
        }}>
          {winner.title}
        </div>
      </div>

      {/* ── Bottom contact bar ── */}
      <div className="absolute bottom-0 left-0 right-0 z-20 flex items-end justify-between"
        style={{ padding:'clamp(5px,1.2vh,10px) clamp(10px,3%,22px)' }}>
        <div style={{ color:'rgba(255,255,255,0.72)', fontSize:'clamp(5px,0.8vw,8.5px)', lineHeight:1.6 }}>
          <div style={{ fontWeight:700 }}>Call: 099 612 466 48, 079 943 766 48</div>
          <div>BHARANANGANAM, KOTTAYAM DISTRICT</div>
          <div>assisiifl@gmail.com &nbsp; www.assisiinstitute.org</div>
        </div>
        <div style={{ color:'#ff7043', fontSize:'clamp(5px,0.75vw,8px)', fontWeight:600, textAlign:'right' }}>
          Follow us on: 📧 📘 📸
        </div>
      </div>
    </div>
  );
}

export default function B2WinnersSlideshow() {
  const [winners, setWinners] = useState<any[]>([]);
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);

  useEffect(() => { getB2Winners().then(setWinners); }, []);

  useEffect(() => {
    if (winners.length < 2 || paused) return;
    const t = setInterval(() => setIndex((i) => (i + 1) % winners.length), INTERVAL_MS);
    return () => clearInterval(t);
  }, [winners.length, paused]);

  const go = (d: number) => setIndex((i) => (i + d + winners.length) % winners.length);
  const current = winners[index];
  const getOrderNumber = (w: any, idx: number) => w.order_number ?? (idx + 1);

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
          <motion.div key={current?.id ?? index}
            initial={{ opacity: 0, scale: 0.98, x: 60 }}
            animate={{ opacity: 1, scale: 1, x: 0 }}
            exit={{ opacity: 0, scale: 0.98, x: -60 }}
            transition={{ duration: 0.6, ease: 'easeInOut' }}>
            <CertificateCard winner={current} orderNumber={getOrderNumber(current, index)} />
          </motion.div>
        </AnimatePresence>

        {winners.length > 1 && (
          <>
            <button id="b2-prev" aria-label="Previous winner" onClick={() => go(-1)}
              className="absolute left-3 top-1/2 -translate-y-1/2 z-30 p-2.5 rounded-full bg-black/40 hover:bg-black/70 text-white transition-all backdrop-blur-sm border border-white/20">
              <ChevronLeft className="h-5 w-5" />
            </button>
            <button id="b2-next" aria-label="Next winner" onClick={() => go(1)}
              className="absolute right-3 top-1/2 -translate-y-1/2 z-30 p-2.5 rounded-full bg-black/40 hover:bg-black/70 text-white transition-all backdrop-blur-sm border border-white/20">
              <ChevronRight className="h-5 w-5" />
            </button>
          </>
        )}
      </div>

      {winners.length > 1 && (
        <div className="flex justify-center gap-2">
          {winners.map((w, i) => (
            <button key={w.id} id={`b2-dot-${i}`} aria-label={`Show winner ${i + 1}`}
              onClick={() => setIndex(i)}
              className={`h-2 rounded-full transition-all duration-300 ${
                i === index ? 'w-8 bg-amber-400' : 'w-2 bg-white/30 hover:bg-amber-300'
              }`} />
          ))}
        </div>
      )}
    </div>
  );
}
