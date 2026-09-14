import React from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, Users, ShieldAlert, ArrowRight, Activity, Calendar, Film, Globe, ChevronRight, Building, Sun, Moon } from 'lucide-react';
import { motion } from 'framer-motion';
import { useTheme } from '@/contexts/ThemeContext';

const fadeInUp = { hidden: { opacity: 0, y: 30 }, visible: { opacity: 1, y: 0, transition: { duration: 0.6 } } };
const staggerContainer = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.1 } } };

export default function VisitorLanding() {
  const { theme, setTheme } = useTheme();

  const toggleTheme = () => {
    setTheme(theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches) ? 'light' : 'dark');
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#0A0D14] text-slate-900 dark:text-white font-sans selection:bg-indigo-500 selection:text-white overflow-hidden transition-colors duration-300">
      
      {/* 1. HERO SECTION */}
      <section className="relative min-h-screen flex flex-col items-center justify-center pt-24 pb-20 px-6">
        {/* Background glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-slate-300 dark:bg-[#2E3C58] rounded-full blur-[120px] opacity-40 dark:opacity-30 pointer-events-none transition-colors duration-500" />
        
        {/* Pill Navbar */}
        <nav className="absolute top-8 left-1/2 -translate-x-1/2 w-[90%] max-w-4xl bg-white/70 dark:bg-white/5 backdrop-blur-xl border border-slate-200 dark:border-white/10 rounded-full px-6 py-4 flex items-center justify-between z-50 shadow-xl dark:shadow-2xl transition-colors duration-300">
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="group-hover:scale-105 transition-transform">
              <img src="/logo.png" alt="ASSISI Logo" className="h-20 w-auto object-contain drop-shadow-md" />
            </div>
          </Link>
          <div className="hidden md:flex items-center space-x-6 text-sm font-medium text-slate-600 dark:text-slate-300">
            <Link to="/reels" className="hover:text-blue-600 dark:hover:text-white transition-colors flex items-center gap-1">
               Campus Video Reels
            </Link>
            <Link to="/notes" className="hover:text-emerald-600 dark:hover:text-white transition-colors flex items-center gap-1">
               Student Notes
            </Link>
            <Link to="/public-feed" className="hover:text-slate-900 dark:hover:text-white transition-colors">Public Notices</Link>
            <a href="tel:+919961246648" className="hover:text-amber-600 dark:hover:text-amber-400 transition-colors font-semibold">Contact</a>
            <a href="https://maps.google.com/?q=Assisi+Institute+of+Foreign+Languages" target="_blank" rel="noreferrer" className="hover:text-amber-600 dark:hover:text-amber-400 transition-colors font-semibold">Location</a>
          </div>
          
          <div className="flex items-center gap-2">
            <Link to="/admin-login" className="px-4 py-2 rounded-full bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-sm font-semibold hover:bg-slate-800 dark:hover:bg-slate-200 transition-colors shadow-sm whitespace-nowrap">
              Admin Login
            </Link>
            <button 
              onClick={toggleTheme}
              className="p-2 rounded-full bg-slate-100 dark:bg-white/10 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-white/20 transition-all border border-slate-200 dark:border-white/10"
              title="Toggle theme"
            >
              {theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches) ? (
                <Sun className="h-4 w-4" />
              ) : (
                <Moon className="h-4 w-4" />
              )}
            </button>
          </div>
        </nav>

        {/* Hero Content */}
        <motion.div className="relative z-10 text-center max-w-4xl mx-auto mt-16" initial="hidden" animate="visible" variants={staggerContainer}>
          <motion.div variants={fadeInUp} className="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 text-xs font-medium text-slate-600 dark:text-slate-300 mb-8 shadow-sm backdrop-blur-md">
            <span className="w-2 h-2 rounded-full bg-blue-500 dark:bg-blue-400 animate-pulse" />
            <span>Assisi Social Platform • Multi-Campus Network</span>
          </motion.div>
          
          <motion.h1 variants={fadeInUp} className="text-5xl md:text-7xl font-semibold tracking-tight mb-6 leading-[1.1] text-slate-900 dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-b dark:from-white dark:to-slate-400">
            Connecting Minds,<br/>
            Empowering Education
          </motion.h1>
          
          <motion.p variants={fadeInUp} className="text-lg md:text-xl text-slate-600 dark:text-slate-400 max-w-2xl mx-auto mb-12 leading-relaxed font-light">
            Welcome to the Assisi Social portal. A multi-campus educational social space connecting students, educators, and administrators.
          </motion.p>

          <motion.div variants={fadeInUp} className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/reels" className="w-full sm:w-auto px-8 py-3.5 rounded-full bg-blue-600 text-white font-medium hover:bg-blue-700 dark:hover:bg-blue-500 transition-colors shadow-lg shadow-blue-500/20 flex items-center justify-center gap-2">
              <Film className="h-4 w-4" /> Watch Campus Reels
            </Link>
            <Link to="/notes" className="w-full sm:w-auto px-8 py-3.5 rounded-full bg-white dark:bg-white/10 border border-slate-200 dark:border-white/10 text-slate-700 dark:text-white font-medium hover:bg-slate-50 dark:hover:bg-white/20 transition-all shadow-sm backdrop-blur-md flex items-center justify-center gap-2">
              Free Student Notes <ArrowRight className="h-4 w-4" />
            </Link>
          </motion.div>
        </motion.div>
      </section>

      {/* 2. AIFL Language Institute Section */}
      <section className="px-6 py-32 relative bg-gradient-to-b from-slate-50 to-emerald-50/30 dark:from-[#0A0D14] dark:to-[#050B0A] overflow-hidden transition-colors duration-300">
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-emerald-200/50 dark:bg-[#0E352A] rounded-full blur-[150px] opacity-60 dark:opacity-50 pointer-events-none transition-colors duration-500" />
        
        <div className="max-w-7xl mx-auto relative z-10 grid lg:grid-cols-2 gap-16 items-center">
          <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }} viewport={{ once: true }} className="space-y-8">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-white dark:bg-white/5 rounded-lg border border-slate-200 dark:border-white/10 shadow-sm">
                <Globe className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
              </div>
              <span className="text-sm font-bold text-slate-700 dark:text-slate-300 tracking-widest uppercase">Assisi IFL</span>
            </div>
            
            <h2 className="text-4xl md:text-5xl font-semibold tracking-tight leading-tight text-slate-900 dark:text-white">
              Assisi Institute of <br />
              <span className="text-emerald-600 dark:text-transparent dark:bg-clip-text dark:bg-gradient-to-r dark:from-emerald-200 dark:to-emerald-500">
                Foreign Languages
              </span>
            </h2>
            
            <p className="text-slate-600 dark:text-slate-400 text-lg leading-relaxed font-light">
              Empowering students to conquer global opportunities. Our distinguished institute provides world-class language training, cultural immersion, and communication mastery to help you excel internationally.
            </p>

            <div className="pt-4">
              <h3 className="text-sm font-semibold text-slate-800 dark:text-white mb-4">Language Offerings</h3>
              <div className="grid grid-cols-3 gap-4">
                {/* Language Cards */}
                <div className="p-4 rounded-2xl bg-white dark:bg-white/[0.03] border border-slate-200 dark:border-white/10 hover:border-emerald-500/50 hover:bg-emerald-50 dark:hover:bg-emerald-500/10 transition-all cursor-pointer group shadow-sm">
                  <span className="text-2xl mb-3 block">🇩🇪</span>
                  <h4 className="text-slate-900 dark:text-white font-medium text-sm mb-1">German</h4>
                  <p className="text-xs text-slate-500 group-hover:text-emerald-700 dark:group-hover:text-emerald-200/70 transition-colors">Beginner and advanced levels.</p>
                </div>
                <div className="p-4 rounded-2xl bg-white dark:bg-white/[0.03] border border-slate-200 dark:border-white/10 hover:border-emerald-500/50 hover:bg-emerald-50 dark:hover:bg-emerald-500/10 transition-all cursor-pointer group shadow-sm">
                  <span className="text-2xl mb-3 block">🇫🇷</span>
                  <h4 className="text-slate-900 dark:text-white font-medium text-sm mb-1">French</h4>
                  <p className="text-xs text-slate-500 group-hover:text-emerald-700 dark:group-hover:text-emerald-200/70 transition-colors">Immersive cultural program.</p>
                </div>
                <div className="p-4 rounded-2xl bg-white dark:bg-white/[0.03] border border-slate-200 dark:border-white/10 hover:border-emerald-500/50 hover:bg-emerald-50 dark:hover:bg-emerald-500/10 transition-all cursor-pointer group shadow-sm">
                  <span className="text-2xl mb-3 block">🇬🇧</span>
                  <h4 className="text-slate-900 dark:text-white font-medium text-sm mb-1">English</h4>
                  <p className="text-xs text-slate-500 group-hover:text-emerald-700 dark:group-hover:text-emerald-200/70 transition-colors">Business and conversational.</p>
                </div>
              </div>
            </div>
          </motion.div>
          
          <motion.div initial={{ opacity: 0, scale: 0.95 }} whileInView={{ opacity: 1, scale: 1 }} transition={{ duration: 0.8 }} viewport={{ once: true }} className="relative">
            <div className="absolute -inset-4 bg-gradient-to-tr from-emerald-200 dark:from-emerald-500/20 to-transparent rounded-[2rem] blur-2xl opacity-50" />
            <div className="relative rounded-3xl overflow-hidden border border-slate-200 dark:border-white/10 shadow-2xl shadow-emerald-900/10 dark:shadow-emerald-900/20">
              <img src="https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&q=80&w=1000" alt="Students learning" className="w-full h-[500px] object-cover" />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-900/80 dark:from-black/80 via-transparent to-transparent" />
              <div className="absolute bottom-6 left-6">
                <button className="px-6 py-2.5 rounded-full bg-white text-slate-900 font-semibold text-sm hover:bg-slate-100 transition-colors shadow-lg">
                  Schedule a Visit
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* 3. Gurukula Branches Section */}
      <section id="branches" className="px-6 py-32 relative bg-gradient-to-b from-emerald-50/30 to-indigo-50/30 dark:from-[#050B0A] dark:to-[#090A15] transition-colors duration-300">
        <div className="absolute top-0 left-0 w-full h-[800px] bg-gradient-to-br from-blue-100/50 to-indigo-100/50 dark:from-[#1E2565]/40 dark:to-[#371958]/20 blur-3xl pointer-events-none transition-colors duration-500" />
        
        <div className="max-w-7xl mx-auto relative z-10">
          <motion.div className="mb-12" initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeInUp}>
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 dark:bg-blue-500/20 rounded-lg border border-blue-200 dark:border-blue-500/30">
                  <BookOpen className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
                <h2 className="text-2xl font-semibold text-slate-900 dark:text-white">Our 11 Gurukula Institution Branches</h2>
              </div>
              <div className="hidden md:flex gap-4">
                <button className="p-2 rounded-full border border-slate-200 dark:border-white/10 bg-white dark:bg-white/5 hover:bg-slate-50 dark:hover:bg-white/10 transition-colors text-slate-600 dark:text-white">
                  <ArrowRight className="h-4 w-4 rotate-180" />
                </button>
                <button className="p-2 rounded-full border border-slate-200 dark:border-white/10 bg-white dark:bg-white/5 hover:bg-slate-50 dark:hover:bg-white/10 transition-colors text-slate-600 dark:text-white">
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          </motion.div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {[
              { name: "Liebhaus Gurukula", location: "Kidangoor", code: "liebhaus", tag: "Design & Mentoring" },
              { name: "Bethsleeha Gurukula", location: "Kaduthuruthy", code: "bethsleeha", tag: "Value Education" },
              { name: "Pala Gurukula", location: "Pala", code: "pala_gurukula", tag: "Science & Discipline" },
              { name: "Greccio Gurukula", location: "Kizhaparayar", code: "greccio", tag: "Eco & Spiritual" },
              { name: "St.Alphonsa Gurukula", location: "Bharanaganam", code: "stalphonsa", tag: "Scholarship & Service" },
              { name: "Traumhaus Gurukula", location: "Bharanaganam", code: "traumhaus", tag: "Creative Arts" },
              { name: "Ashramam Gurukula", location: "Bharanaganam", code: "ashramam", tag: "Focus & Mindfulness" },
              { name: "St.Clare Gurukula", location: "Poovathodu", code: "stclare", tag: "Social Outreach" },
              { name: "Assisi Mount Gurukula", location: "Melampara", code: "assisimount", tag: "Sports & Excellence" },
              { name: "Mitraniketan Boys", location: "Vagamon", code: "assisivagamon", tag: "Residential Campus" },
              { name: "Thopramkudy Gurukula", location: "Thopramkudy", code: "thopramkudy", tag: "Digital & Technical" },
            ].map((branch, idx) => (
              <motion.div key={idx} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.05 }} viewport={{ once: true }} className="group p-5 rounded-2xl bg-white dark:bg-white/[0.04] border border-slate-200 dark:border-white/[0.08] hover:border-blue-400 dark:hover:border-blue-500/50 hover:bg-blue-50 dark:hover:bg-blue-500/10 transition-all backdrop-blur-sm cursor-pointer flex flex-col justify-between min-h-[160px] shadow-sm hover:shadow-md">
                <div>
                  <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-1 group-hover:text-blue-700 dark:group-hover:text-blue-300 transition-colors">{branch.name}</h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 font-medium mb-3">{branch.location}</p>
                  <span className="inline-block text-[10px] font-medium px-2 py-1 rounded bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-white/10 group-hover:bg-blue-100 dark:group-hover:bg-blue-500/20 group-hover:text-blue-700 dark:group-hover:text-blue-200 transition-colors">
                    {branch.tag}
                  </span>
                </div>
                <div className="flex justify-between items-center mt-4 pt-4 border-t border-slate-100 dark:border-white/5">
                   <Link to="/public-feed" className="text-xs font-medium text-slate-500 hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">View Updates</Link>
                   <Link to={`/branch-login/${branch.code}`} className="text-xs font-medium text-slate-500 hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors flex items-center gap-1">Login <ChevronRight className="h-3 w-3" /></Link>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* 4. Overview Statistics Section */}
      <section id="about" className="px-6 py-32 relative bg-gradient-to-b from-indigo-50/30 to-amber-50/30 dark:from-[#090A15] dark:to-[#120F0D] transition-colors duration-300">
        <div className="absolute top-1/2 right-0 -translate-y-1/2 w-[700px] h-[700px] bg-amber-100/60 dark:bg-[#423321] rounded-full blur-[150px] opacity-60 dark:opacity-40 pointer-events-none transition-colors duration-500" />
        
        <div className="max-w-7xl mx-auto relative z-10 grid lg:grid-cols-2 gap-16 items-center">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeInUp} className="space-y-10">
            <div>
              <span className="text-xs font-bold text-amber-600 dark:text-[#D4AF37] tracking-widest uppercase mb-3 block">Integrated Platform</span>
              <h2 className="text-4xl md:text-5xl font-semibold mb-6 tracking-tight text-slate-900 dark:text-white">The Modern Campus Network</h2>
              <p className="text-slate-600 dark:text-slate-400 text-lg leading-relaxed font-light">
                Assisi Social unites fragmented campus systems under one cohesive environment. From social relations to institutional notices across all 11 Gurukula branches, we offer clean interfaces and robust administration tools.
              </p>
            </div>

            <div className="space-y-6">
              <div className="flex items-start space-x-4 p-4 rounded-2xl bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 backdrop-blur-md shadow-sm">
                <div className="bg-amber-100 dark:bg-[#D4AF37]/20 p-2.5 rounded-xl border border-amber-200 dark:border-[#D4AF37]/30 text-amber-600 dark:text-[#D4AF37]">
                  <Calendar className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="font-semibold text-slate-900 dark:text-white mb-1">Organized Events & Calendar</h4>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Keep students in the loop with events and classroom tasks.</p>
                </div>
              </div>
              <div className="flex items-start space-x-4 p-4 rounded-2xl bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 backdrop-blur-md shadow-sm">
                <div className="bg-amber-100 dark:bg-[#D4AF37]/20 p-2.5 rounded-xl border border-amber-200 dark:border-[#D4AF37]/30 text-amber-600 dark:text-[#D4AF37]">
                  <Activity className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="font-semibold text-slate-900 dark:text-white mb-1">Real-Time Performance Indicators</h4>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Provide administrators and institutions with dynamic analytical charts.</p>
                </div>
              </div>
            </div>

            {/* Abstract SVG charts underneath to mimic the mockup */}
            <div className="flex gap-4 pt-4">
              <div className="flex-1 h-24 rounded-2xl bg-gradient-to-t from-slate-200 dark:from-white/5 to-transparent border border-slate-200 dark:border-white/10 relative overflow-hidden flex items-end">
                <svg viewBox="0 0 100 40" preserveAspectRatio="none" className="w-full h-full opacity-50 stroke-amber-500 dark:stroke-[#D4AF37] fill-none" strokeWidth="2">
                  <path d="M0,30 Q10,10 20,25 T40,15 T60,20 T80,5 T100,20" />
                </svg>
              </div>
              <div className="flex-1 h-24 rounded-2xl bg-gradient-to-t from-slate-200 dark:from-white/5 to-transparent border border-slate-200 dark:border-white/10 relative overflow-hidden flex items-end">
                <svg viewBox="0 0 100 40" preserveAspectRatio="none" className="w-full h-full opacity-50 stroke-amber-500 dark:stroke-[#D4AF37] fill-none" strokeWidth="2">
                  <path d="M0,20 Q15,35 30,15 T60,25 T80,10 T100,15" />
                </svg>
              </div>
            </div>
          </motion.div>

          <motion.div className="relative lg:ml-12" initial={{ opacity: 0, scale: 0.95 }} whileInView={{ opacity: 1, scale: 1 }} transition={{ duration: 0.8 }} viewport={{ once: true }}>
            <div className="absolute -inset-8 bg-gradient-to-tr from-amber-200 dark:from-[#D4AF37]/20 to-transparent rounded-[3rem] blur-2xl opacity-50 dark:opacity-40 transition-colors duration-500" />
            {/* Thick glass border container */}
            <div className="p-4 rounded-[2.5rem] bg-white/60 dark:bg-white/5 border border-slate-200 dark:border-white/20 backdrop-blur-xl relative z-10 shadow-2xl">
              <img
                src="https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&q=80&w=800"
                alt="Campus Teamwork"
                className="rounded-[2rem] border border-slate-200 dark:border-white/10 w-full h-[500px] object-cover"
              />
              
              {/* Floating element on image */}
              <div className="absolute -bottom-6 -left-6 p-6 rounded-3xl bg-white dark:bg-[#120F0D] border border-slate-200 dark:border-white/10 shadow-2xl flex items-center gap-4 transition-colors duration-300">
                <div className="p-3 bg-amber-100 dark:bg-[#D4AF37]/20 rounded-full">
                  <Users className="h-6 w-6 text-amber-600 dark:text-[#D4AF37]" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-slate-900 dark:text-white">4.2k+</p>
                  <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">Active Students</p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Portals Section */}
      <section className="px-6 py-12 bg-gradient-to-b from-amber-50/30 to-slate-50 dark:from-[#120F0D] dark:to-[#0A0D14] flex flex-wrap justify-center items-center gap-6 text-sm text-slate-500 transition-colors duration-300">
        <Link to="/admin-login" className="hover:text-slate-900 dark:hover:text-white transition-colors flex items-center gap-1"><ShieldAlert className="h-4 w-4" /> Super Admin Portal</Link>
        <span className="hidden md:inline">•</span>
        <Link to="/branch-login" className="hover:text-slate-900 dark:hover:text-white transition-colors flex items-center gap-1"><Building className="h-4 w-4" /> Institution Portal</Link>
      </section>

      {/* Footer */}
      <footer className="px-6 py-8 text-center text-slate-500 dark:text-slate-600 text-xs bg-slate-50 dark:bg-[#0A0D14] transition-colors duration-300 space-y-2">
        <p>Contact Us: <a href="tel:+919961246648" className="hover:text-amber-600 dark:hover:text-amber-400 transition-colors">9961246648</a>, <a href="tel:+917994376648" className="hover:text-amber-600 dark:hover:text-amber-400 transition-colors">7994376648</a></p>
        <p>&copy; {new Date().getFullYear()} Assisi Social Platform. All rights reserved.</p>
      </footer>
    </div>
  );
}
