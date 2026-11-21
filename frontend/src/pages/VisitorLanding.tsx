import BrochureSection from '@/components/BrochureSection';
import GalleryPreview from '@/components/GalleryPreview';
import NotifyButton from '@/components/NotifyButton';
import RegistrationModal from '@/components/RegistrationModal';
import React, { useState } from 'react';
import { AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import { BookOpen, ShieldAlert, ArrowRight, Film, Globe, ChevronRight, Building, Sun, Moon, MapPin, Phone, Mail, ExternalLink, GraduationCap, Quote } from 'lucide-react';
import { motion } from 'framer-motion';
import { useTheme } from '@/contexts/ThemeContext';
import B2WinnersSlideshow from '@/components/B2WinnersSlideshow';

const fadeInUp = { hidden: { opacity: 0, y: 30 }, visible: { opacity: 1, y: 0, transition: { duration: 0.6 } } };
const staggerContainer = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.1 } } };

export default function VisitorLanding() {
  const { theme, setTheme } = useTheme();
  const [showRegister, setShowRegister] = useState(false);

  const toggleTheme = () => {
    setTheme(theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches) ? 'light' : 'dark');
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#0A0D14] text-slate-900 dark:text-white font-sans selection:bg-indigo-500 selection:text-white overflow-hidden transition-colors duration-300">
      
      {/* 1. HERO SECTION */}
      <section className="relative min-h-screen flex flex-col items-center justify-center pt-24 pb-20 px-6 overflow-hidden">
        {/* Background video */}
        <video
          className="absolute inset-0 w-full h-full object-cover pointer-events-none"
          src="/hero-bg.mp4"
          autoPlay
          muted
          loop
          playsInline
          preload="auto"
        />
        {/* Overlay for text readability */}
        <div className="absolute inset-0 bg-white/60 dark:bg-[#0A0D14]/70 pointer-events-none transition-colors duration-300" />
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
            <Link to="/gallery" className="hover:text-emerald-600 dark:hover:text-white transition-colors">Gallery</Link>
            <a href="#instructors" className="hover:text-violet-600 dark:hover:text-white transition-colors flex items-center gap-1">Our Instructors</a>
            <a href="#contact" className="hover:text-emerald-600 dark:hover:text-white transition-colors font-semibold">Contact Us</a>
          </div>
          
          <div className="flex items-center gap-2">
            <NotifyButton />
            <button
              id="open-register"
              onClick={() => setShowRegister(true)}
              className="px-4 py-2 rounded-full bg-gradient-to-r from-emerald-600 to-teal-500 text-white text-sm font-bold shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/40 hover:scale-[1.03] transition-all whitespace-nowrap"
            >
              Register
            </button>
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
              <div className="p-4 rounded-2xl bg-white dark:bg-white/[0.03] border border-slate-200 dark:border-white/10 hover:border-emerald-500/50 hover:bg-emerald-50 dark:hover:bg-emerald-500/10 transition-all cursor-pointer group shadow-sm flex items-center gap-4">
                <span className="text-3xl">🇩🇪</span>
                <div>
                  <h4 className="text-slate-900 dark:text-white font-medium text-sm mb-1">German</h4>
                  <p className="text-xs text-slate-500 group-hover:text-emerald-700 dark:group-hover:text-emerald-200/70 transition-colors">Beginner and advanced levels.</p>
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

        <GalleryPreview />

        {/* B2 Winners panel — full width */}
        <motion.div id="b2winners" initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }} viewport={{ once: true }} className="max-w-7xl mx-auto relative z-10 mt-20">
          <div className="text-center mb-10">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white dark:bg-white/5 border border-amber-200 dark:border-amber-500/30 text-xs font-semibold text-amber-700 dark:text-amber-300 mb-5 shadow-sm">
              <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
              <span>Celebrating Excellence</span>
            </div>
            <h3 className="text-4xl md:text-5xl font-semibold tracking-tight text-slate-900 dark:text-white">
              Our <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-500 to-orange-400">B2 Winners</span>
            </h3>
          </div>
          <div className="relative">
            <div className="absolute -inset-4 bg-gradient-to-tr from-amber-300/30 dark:from-amber-500/10 to-blue-300/20 dark:to-blue-900/10 rounded-[2.5rem] blur-2xl opacity-70" />
            <div className="relative rounded-3xl overflow-hidden shadow-2xl ring-1 ring-amber-200/50 dark:ring-amber-500/20">
              <B2WinnersSlideshow />
            </div>
          </div>
        </motion.div>

        <BrochureSection />
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

      {/* 5. OUR INSTRUCTORS SECTION */}
      <section id="instructors" className="px-6 py-32 relative bg-gradient-to-b from-indigo-50/30 to-violet-50/20 dark:from-[#090A15] dark:to-[#0D0A18] overflow-hidden transition-colors duration-300">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-violet-200/40 dark:bg-violet-900/20 rounded-full blur-[150px] opacity-60 pointer-events-none" />

        <div className="max-w-7xl mx-auto relative z-10">
          {/* Section Header */}
          <motion.div className="text-center mb-20" initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeInUp}>
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 text-xs font-semibold text-violet-700 dark:text-violet-300 mb-6 shadow-sm backdrop-blur-md">
              <GraduationCap className="h-4 w-4" />
              <span>Our Skilled &amp; Highly Qualified Faculty</span>
            </div>
            <h2 className="text-4xl md:text-5xl font-semibold tracking-tight text-slate-900 dark:text-white mb-4">
              Our <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-600 to-indigo-500 dark:from-violet-300 dark:to-indigo-400">Instructors</span>
            </h2>
            <p className="text-slate-500 dark:text-slate-400 text-lg font-light max-w-xl mx-auto">
              Meet the passionate educators who ignite curiosity and shape the future of our students.
            </p>
          </motion.div>

          {/* Instructor Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
            {[
              {
                name: 'Dr. Annie Kurian',
                role: 'Dean of Studies',
                badge: 'Dean',
                badgeColor: 'bg-violet-100 dark:bg-violet-500/20 text-violet-700 dark:text-violet-300 border-violet-200 dark:border-violet-500/30',
                photo: '/instructors/dr-annie-kurian.jpg',
                quote: 'It is the supreme art of the instructor to awaken joy in creative expression and knowledge.',
                accentFrom: 'from-violet-500',
                accentTo: 'to-indigo-500',
              },
              {
                name: 'Fr. Jacob Chamakkalayil',
                role: 'Instructor',
                badge: 'Instructor',
                badgeColor: 'bg-blue-100 dark:bg-blue-500/20 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-500/30',
                photo: '/instructors/fr-jacob-chamakkalayil.jpg',
                quote: 'Education is not the filling of a pail, but the lighting of a fire.',
                accentFrom: 'from-blue-500',
                accentTo: 'to-cyan-500',
              },
              {
                name: 'KJ Thomas',
                role: 'Instructor',
                badge: 'Instructor',
                badgeColor: 'bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-500/30',
                photo: '/instructors/kj-thomas.png',
                quote: 'The greatest good you can do for another is not just share your riches, but reveal to them their own.',
                accentFrom: 'from-emerald-500',
                accentTo: 'to-teal-500',
              },
              {
                name: 'Angelika Bochmann',
                role: 'Guest Faculty',
                badge: 'Guest Faculty',
                badgeColor: 'bg-rose-100 dark:bg-rose-500/20 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-500/30',
                photo: '/instructors/angelika-bochmann.jpg',
                quote: 'Without God I can do nothing, with God everything. (Blessed Fr. Karl Leisner)',
                accentFrom: 'from-rose-500',
                accentTo: 'to-pink-500',
              },
              {
                name: 'Br. Paulus Terwitte',
                role: 'Guest Faculty',
                badge: 'Guest Faculty',
                badgeColor: 'bg-amber-100 dark:bg-amber-500/20 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-500/30',
                photo: '/instructors/br-paulus-terwitte.jpg',
                quote: 'Teaching is the greatest act of optimism.',
                accentFrom: 'from-amber-500',
                accentTo: 'to-orange-500',
              },
            ].map((instructor, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: idx * 0.1 }}
                viewport={{ once: true }}
                className="group relative flex flex-col rounded-3xl bg-white dark:bg-white/[0.04] border border-slate-200 dark:border-white/[0.08] shadow-sm hover:shadow-xl dark:hover:shadow-violet-900/20 overflow-hidden transition-all duration-500 hover:-translate-y-1"
              >
                {/* Gradient top bar */}
                <div className={`h-1.5 w-full bg-gradient-to-r ${instructor.accentFrom} ${instructor.accentTo} opacity-80 group-hover:opacity-100 transition-opacity`} />

                {/* Photo */}
                <div className="relative mx-6 mt-8 mb-4">
                  <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${instructor.accentFrom} ${instructor.accentTo} opacity-0 group-hover:opacity-20 blur-xl transition-opacity duration-500`} />
                  <div className="relative w-full aspect-square rounded-2xl overflow-hidden border-2 border-slate-100 dark:border-white/10 shadow-md">
                    <img
                      src={instructor.photo}
                      alt={instructor.name}
                      className="w-full h-full object-cover object-top transition-transform duration-700 group-hover:scale-105"
                    />
                  </div>
                </div>

                {/* Info */}
                <div className="px-6 pb-6 flex flex-col flex-1">
                  <span className={`inline-block self-start text-[10px] font-semibold px-2.5 py-1 rounded-full border mb-3 ${instructor.badgeColor}`}>
                    {instructor.badge}
                  </span>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white mb-0.5 leading-snug">{instructor.name}</h3>
                  <p className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-4">{instructor.role}</p>

                  {/* Quote */}
                  <div className="mt-auto relative">
                    <Quote className="h-4 w-4 text-slate-300 dark:text-white/20 mb-2" />
                    <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed italic line-clamp-4">
                      {instructor.quote}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* 6. CONTACT US SECTION */}
      <section id="contact" className="px-6 py-32 relative bg-gradient-to-b from-violet-50/20 to-slate-50 dark:from-[#0D0A18] dark:to-[#0A0D14] overflow-hidden transition-colors duration-300">
        <div className="absolute bottom-0 left-0 w-[600px] h-[500px] bg-indigo-200/40 dark:bg-indigo-900/20 rounded-full blur-[150px] opacity-50 pointer-events-none" />
        <div className="absolute top-0 right-0 w-[400px] h-[400px] bg-emerald-200/30 dark:bg-emerald-900/15 rounded-full blur-[120px] opacity-50 pointer-events-none" />

        <div className="max-w-5xl mx-auto relative z-10">
          {/* Header */}
          <motion.div className="text-center mb-16" initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeInUp}>
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 text-xs font-semibold text-emerald-700 dark:text-emerald-300 mb-6 shadow-sm backdrop-blur-md">
              <MapPin className="h-4 w-4" />
              <span>Find Us</span>
            </div>
            <h2 className="text-4xl md:text-5xl font-semibold tracking-tight text-slate-900 dark:text-white mb-4">
              Contact <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-500 to-teal-400">Us</span>
            </h2>
            <p className="text-slate-500 dark:text-slate-400 text-lg font-light max-w-lg mx-auto">
              We'd love to hear from you. Reach out to us at the Assisi Institute of Foreign Languages.
            </p>
          </motion.div>

          {/* Contact Card */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
            viewport={{ once: true }}
            className="grid md:grid-cols-2 gap-8"
          >
            {/* Info Panel */}
            <div className="space-y-5">
              {/* Address */}
              <div className="flex items-start gap-4 p-5 rounded-2xl bg-white dark:bg-white/[0.04] border border-slate-200 dark:border-white/10 shadow-sm hover:shadow-md hover:border-emerald-300 dark:hover:border-emerald-500/40 transition-all group">
                <div className="p-3 rounded-xl bg-emerald-100 dark:bg-emerald-500/20 border border-emerald-200 dark:border-emerald-500/30 text-emerald-600 dark:text-emerald-400 shrink-0">
                  <MapPin className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest mb-1">Address</p>
                  <p className="text-sm font-semibold text-slate-900 dark:text-white leading-relaxed">
                    Assisi Institute of Foreign Languages<br />
                    Opp: St. Alphonsa Shrine,<br />
                    Bharanaganam – 686578<br />
                    Kottayam Dt, Kerala.
                  </p>
                </div>
              </div>

              {/* Phone */}
              <div className="flex items-start gap-4 p-5 rounded-2xl bg-white dark:bg-white/[0.04] border border-slate-200 dark:border-white/10 shadow-sm hover:shadow-md hover:border-blue-300 dark:hover:border-blue-500/40 transition-all group">
                <div className="p-3 rounded-xl bg-blue-100 dark:bg-blue-500/20 border border-blue-200 dark:border-blue-500/30 text-blue-600 dark:text-blue-400 shrink-0">
                  <Phone className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest mb-1">Phone</p>
                  <div className="space-y-1">
                    {['+91 04822 236457', '+91 9961 246648', '+91 7994 376648'].map((num) => (
                      <a key={num} href={`tel:${num.replace(/\s/g, '')}`} className="block text-sm font-semibold text-slate-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                        {num}
                      </a>
                    ))}
                  </div>
                </div>
              </div>

              {/* Email */}
              <div className="flex items-start gap-4 p-5 rounded-2xl bg-white dark:bg-white/[0.04] border border-slate-200 dark:border-white/10 shadow-sm hover:shadow-md hover:border-violet-300 dark:hover:border-violet-500/40 transition-all group">
                <div className="p-3 rounded-xl bg-violet-100 dark:bg-violet-500/20 border border-violet-200 dark:border-violet-500/30 text-violet-600 dark:text-violet-400 shrink-0">
                  <Mail className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest mb-1">Email</p>
                  <a href="mailto:assisiifl@gmail.com" className="text-sm font-semibold text-slate-900 dark:text-white hover:text-violet-600 dark:hover:text-violet-400 transition-colors">
                    assisiifl@gmail.com
                  </a>
                </div>
              </div>

              {/* Website */}
              <div className="flex items-start gap-4 p-5 rounded-2xl bg-white dark:bg-white/[0.04] border border-slate-200 dark:border-white/10 shadow-sm hover:shadow-md hover:border-amber-300 dark:hover:border-amber-500/40 transition-all group">
                <div className="p-3 rounded-xl bg-amber-100 dark:bg-amber-500/20 border border-amber-200 dark:border-amber-500/30 text-amber-600 dark:text-amber-400 shrink-0">
                  <Globe className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest mb-1">Website</p>
                  <a href="https://assisiinstitute.org" target="_blank" rel="noreferrer" className="text-sm font-semibold text-slate-900 dark:text-white hover:text-amber-600 dark:hover:text-amber-400 transition-colors flex items-center gap-1">
                    assisiinstitute.org <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                </div>
              </div>
            </div>

            {/* Map Panel */}
            <div className="rounded-3xl overflow-hidden border border-slate-200 dark:border-white/10 shadow-xl relative min-h-[380px]">
              <iframe
                title="Assisi Institute of Foreign Languages Map"
                src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3932.547!2d76.654!3d9.639!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3b07cad8abf4c7c3%3A0x7c4f70f71c9f9b3f!2sAssisi%20Institute%20of%20Foreign%20Languages!5e0!3m2!1sen!2sin!4v1700000000000!5m2!1sen!2sin"
                className="w-full h-full min-h-[380px] border-0"
                allowFullScreen
                loading="lazy"
                referrerPolicy="no-referrer-when-downgrade"
              />
              {/* Map overlay CTA */}
              <div className="absolute bottom-4 left-4">
                <a
                  href="https://maps.google.com/?q=Assisi+Institute+of+Foreign+Languages,+Bharanaganam,+Kerala"
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2.5 rounded-full bg-white text-slate-900 font-semibold text-xs hover:bg-slate-100 transition-colors shadow-lg"
                >
                  <MapPin className="h-3.5 w-3.5 text-emerald-600" />
                  Open in Google Maps
                  <ExternalLink className="h-3 w-3 text-slate-400" />
                </a>
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

      {/* Floating Register Button */}
      <motion.button
        id="floating-register"
        onClick={() => setShowRegister(true)}
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 2 }}
        className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-5 py-3 rounded-full bg-gradient-to-r from-emerald-600 to-teal-500 text-white font-bold text-sm shadow-2xl shadow-emerald-500/30 hover:shadow-emerald-500/50 hover:scale-105 transition-all"
      >
        <ShieldAlert className="h-4 w-4" /> Register Now
      </motion.button>

      {/* Registration Modal */}
      <AnimatePresence>
        {showRegister && <RegistrationModal onClose={() => setShowRegister(false)} />}
      </AnimatePresence>
    </div>
  );
}
