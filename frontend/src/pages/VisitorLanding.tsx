import React from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, Users, ShieldAlert, Newspaper, ArrowRight, Activity, Calendar, Film, Play } from 'lucide-react';
import { motion } from 'framer-motion';

const fadeInUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6 } }
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

export default function VisitorLanding() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-white font-sans selection:bg-indigo-500 selection:text-white">
      {/* Header / Navbar */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-slate-900/60 border-b border-white/5 px-6 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center space-x-3 group">
          <div className="bg-white p-1 rounded-xl shadow-lg shadow-rose-500/20 group-hover:scale-105 transition-transform">
            <img src="/logo.png" alt="ASSISI IFL Logo" className="h-9 w-auto object-contain" />
          </div>
          <span className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-white via-rose-100 to-rose-400 bg-clip-text text-transparent">
            ASSISI IFL
          </span>
        </Link>
        <nav className="hidden md:flex items-center space-x-8 text-sm font-medium text-slate-300">
          <Link to="/reels" className="text-rose-400 font-extrabold hover:text-rose-300 transition-colors flex items-center gap-1.5 animate-pulse">
            <Film className="h-4 w-4" /> <span>Campus Video Reels</span>
          </Link>
          <Link to="/notes" className="text-emerald-400 font-bold hover:text-emerald-300 transition-colors flex items-center gap-1">
            <span>📚</span> Student Notes & Downloads (Free)
          </Link>
          <Link to="/public-feed" className="hover:text-indigo-400 transition-colors">Public Notices</Link>
          <a href="#portals" className="hover:text-indigo-400 transition-colors">Portals</a>
        </nav>
        <div className="flex items-center space-x-4">
          <Link
            to="/reels"
            className="px-4 py-2 text-xs font-extrabold text-white bg-gradient-to-r from-rose-500 to-indigo-600 hover:from-rose-600 hover:to-indigo-700 rounded-xl transition-all shadow-md flex items-center gap-1"
          >
            <Play className="h-3.5 w-3.5 fill-white" />
            <span>Watch Campus Reels</span>
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative px-6 pt-24 pb-20 max-w-7xl mx-auto text-center">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        
        <motion.div 
          className="relative z-10"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeInUp}
        >
          <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-xs font-semibold text-indigo-300 mb-8 backdrop-blur-md">
            <Activity className="h-3.5 w-3.5 text-indigo-400" />
            <span>Assisi Social Platform • Multi-Campus Network</span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-8 leading-tight">
            Connecting Minds,<br/>
            <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              Empowering Education
            </span>
          </h1>
          
          <p className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
            Welcome to the Assisi Social portal. A multi-campus educational social space connecting students, educators, and administrators.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/reels"
              className="w-full sm:w-auto px-8 py-4 rounded-xl bg-gradient-to-r from-rose-500 via-purple-600 to-indigo-600 text-white font-extrabold hover:from-rose-600 hover:to-indigo-700 transition-all hover:scale-105 shadow-xl shadow-rose-500/25 flex items-center justify-center space-x-2"
            >
              <Film className="h-5 w-5" />
              <span>🎥 Watch Campus Reels</span>
            </Link>
            <Link
              to="/notes"
              className="w-full sm:w-auto px-8 py-4 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-extrabold hover:from-emerald-600 hover:to-teal-700 transition-all hover:scale-105 shadow-xl shadow-emerald-500/20 flex items-center justify-center space-x-2"
            >
              <span>📚 Free Student Notes</span>
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Portals Grid Section */}
      <section id="portals" className="px-6 py-20 bg-slate-950/40 relative border-y border-white/5">
        <div className="max-w-7xl mx-auto">
          <motion.div 
            className="text-center mb-16"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={fadeInUp}
          >
            <h2 className="text-3xl md:text-4xl font-extrabold mb-4 tracking-tight">Dedicated System Portals</h2>
            <p className="text-slate-400 max-w-md mx-auto text-sm md:text-base">
              Choose your dedicated workspace and access specialized workflows.
            </p>
          </motion.div>

          <motion.div 
            className="grid md:grid-cols-3 gap-8"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={staggerContainer}
          >
            {/* Student Notes Card (100% Free & No Login) */}
            <motion.div variants={fadeInUp} className="group relative rounded-2xl bg-gradient-to-b from-slate-900 to-slate-950 border border-white/5 p-8 hover:border-emerald-500/40 transition-all hover:-translate-y-1 hover:shadow-2xl hover:shadow-emerald-500/5 duration-300">
              <div className="bg-emerald-500/10 p-4 rounded-2xl w-14 h-14 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Users className="h-7 w-7 text-emerald-400" />
              </div>
              <h3 className="text-xl font-bold mb-3 group-hover:text-emerald-400 transition-colors">Free Student Notes & Feeds</h3>
              <p className="text-slate-400 text-sm leading-relaxed mb-8">
                100% free, login-free access to all campus notes, official circulars, exam schedules, and department announcements across all Gurukula branches.
              </p>
              <Link
                to="/notes"
                className="inline-flex items-center space-x-2 text-sm font-semibold text-emerald-400 group-hover:text-emerald-300"
              >
                <span>Browse Student Notes</span>
                <ArrowRight className="h-4 w-4 transform group-hover:translate-x-1 transition-transform" />
              </Link>
            </motion.div>

            {/* Institution Space Card */}
            <motion.div variants={fadeInUp} className="group relative rounded-2xl bg-gradient-to-b from-slate-900 to-slate-950 border border-white/5 p-8 hover:border-indigo-500/40 transition-all hover:-translate-y-1 hover:shadow-2xl hover:shadow-indigo-500/5 duration-300">
              <div className="bg-emerald-500/10 p-4 rounded-2xl w-14 h-14 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <BookOpen className="h-7 w-7 text-emerald-400" />
              </div>
              <h3 className="text-xl font-bold mb-3 group-hover:text-emerald-400 transition-colors">Institution Space</h3>
              <p className="text-slate-400 text-sm leading-relaxed mb-8">
                Manage your campus profile, publish notifications, share official updates, organize events, approve student registrations, and view performance charts.
              </p>
              <a
                href="http://localhost:3002"
                className="inline-flex items-center space-x-2 text-sm font-semibold text-emerald-400 group-hover:text-emerald-300"
              >
                <span>Go to Institution Space</span>
                <ArrowRight className="h-4 w-4 transform group-hover:translate-x-1 transition-transform" />
              </a>
            </motion.div>

            {/* Admin Center Card */}
            <motion.div variants={fadeInUp} className="group relative rounded-2xl bg-gradient-to-b from-slate-900 to-slate-950 border border-white/5 p-8 hover:border-indigo-500/40 transition-all hover:-translate-y-1 hover:shadow-2xl hover:shadow-indigo-500/5 duration-300">
              <div className="bg-rose-500/10 p-4 rounded-2xl w-14 h-14 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <ShieldAlert className="h-7 w-7 text-rose-400" />
              </div>
              <h3 className="text-xl font-bold mb-3 group-hover:text-rose-400 transition-colors">Super Admin Center</h3>
              <p className="text-slate-400 text-sm leading-relaxed mb-8">
                Platform-wide control panel. Create new educational institutions, manage tenant databases, audit system activities, and review system-wide analytics.
              </p>
              <a
                href="http://localhost:3001"
                className="inline-flex items-center space-x-2 text-sm font-semibold text-rose-400 group-hover:text-rose-300"
              >
                <span>Enter Super Admin Panel</span>
                <ArrowRight className="h-4 w-4 transform group-hover:translate-x-1 transition-transform" />
              </a>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Gurukula Branches Section */}
      <section id="branches" className="px-6 py-20 bg-slate-900/60 relative border-t border-white/5">
        <div className="max-w-7xl mx-auto">
          <motion.div 
            className="text-center mb-16"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={fadeInUp}
          >
            <span className="text-xs font-bold text-emerald-400 tracking-wider uppercase mb-3 block">Multi-Campus Network</span>
            <h2 className="text-3xl md:text-5xl font-extrabold mb-4 tracking-tight">Our 11 Gurukula Institution Branches</h2>
            <p className="text-slate-400 max-w-xl mx-auto text-sm md:text-base">
              Empowering students across 11 premier Gurukula branches with holistic education, discipline, and modern facilities.
            </p>
          </motion.div>

          <motion.div 
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={staggerContainer}
          >
            {[
              { name: "Liebhaus Gurukula", location: "Kidangoor", code: "liebhaus", tag: "Design & Mentoring" },
              { name: "Bethsleeha Gurukula", location: "Kaduthuruthy", code: "bethsleeha", tag: "Value Education" },
              { name: "Pala Gurukula", location: "Pala", code: "pala_gurukula", tag: "Science & Discipline" },
              { name: "Greccio Gurukula", location: "Kizhaparayar", code: "greccio", tag: "Eco & Spiritual" },
              { name: "St.Alphonsa Gurukula", location: "Bharanaganam", code: "stalphonsa", tag: "Scholarship & Service" },
              { name: "Traumhaus Gurukula", location: "Bharanaganam", code: "traumhaus", tag: "Creative Arts" },
              { name: "Ashramam Gurukula", location: "Bharanaganam", code: "ashramam", tag: "Focus & Mindfulness" },
              { name: "St.Clare Gurukula", location: "Poovathodu, Bharanaganam", code: "stclare", tag: "Social Outreach" },
              { name: "Assisi Mount Gurukula", location: "Melampara, Bharanaganam", code: "assisimount", tag: "Sports & Excellence" },
              { name: "Mitraniketan Boys Gurukula", location: "Vagamon", code: "assisivagamon", tag: "Residential Campus" },
              { name: "Thopramkudy Gurukula", location: "Thopramkudy", code: "thopramkudy", tag: "Digital & Technical" },
            ].map((branch, idx) => (
              <motion.div
                variants={fadeInUp}
                key={idx}
                className="group p-6 rounded-2xl bg-slate-900/90 border border-white/5 hover:border-emerald-500/40 transition-all hover:-translate-y-1 hover:shadow-xl hover:shadow-emerald-500/5"
              >
                <div className="flex items-center justify-between mb-4">
                  <span className="text-[10px] font-extrabold uppercase tracking-wider px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    {branch.tag}
                  </span>
                  <BookOpen className="h-4.5 w-4.5 text-slate-500 group-hover:text-emerald-400 transition-colors" />
                </div>
                <h3 className="text-lg font-bold text-white mb-1 group-hover:text-emerald-300 transition-colors">
                  {branch.name}
                </h3>
                <p className="text-xs text-slate-400 font-medium mb-4 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
                  {branch.location}
                </p>
                <Link
                  to="/public-feed"
                  className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                >
                  <span>View Branch Updates</span>
                  <ArrowRight className="h-3.5 w-3.5 transform group-hover:translate-x-1 transition-transform" />
                </Link>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Overview Statistics Section */}
      <section id="about" className="px-6 py-20 max-w-7xl mx-auto">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={fadeInUp}
          >
            <span className="text-xs font-bold text-indigo-400 tracking-wider uppercase mb-3 block">Integrated Platform</span>
            <h2 className="text-3xl md:text-4xl font-extrabold mb-6 tracking-tight">The Modern Campus Network</h2>
            <p className="text-slate-400 text-base mb-6 leading-relaxed">
              Assisi Social unites fragmented campus systems under one cohesive environment. From social relations to institutional notices across all 11 Gurukula branches, we offer clean interfaces and robust administration tools.
            </p>
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <div className="bg-indigo-500/15 p-1.5 rounded-lg text-indigo-400 mt-1">
                  <Calendar className="h-4 w-4" />
                </div>
                <div>
                  <h4 className="font-bold text-sm">Organized Events & Calendar</h4>
                  <p className="text-xs text-slate-500">Keep students in the loop with events and classroom tasks.</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="bg-indigo-500/15 p-1.5 rounded-lg text-indigo-400 mt-1">
                  <Activity className="h-4 w-4" />
                </div>
                <div>
                  <h4 className="font-bold text-sm">Real-Time Performance Indicators</h4>
                  <p className="text-xs text-slate-500">Provide administrators and institutions with dynamic analytical charts.</p>
                </div>
              </div>
            </div>
          </motion.div>
          <motion.div 
            className="relative"
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.7 }}
            viewport={{ once: true, margin: "-100px" }}
          >
            <div className="absolute inset-0 bg-gradient-to-tr from-indigo-500 to-purple-500 rounded-3xl blur-[40px] opacity-25" />
            <img
              src="https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&q=80&w=800"
              alt="Campus Teamwork"
              className="rounded-3xl border border-white/10 relative z-10 shadow-2xl"
            />
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 px-6 py-8 text-center text-slate-500 text-xs bg-slate-950">
        <p>&copy; {new Date().getFullYear()} Assisi Social Platform. All rights reserved.</p>
      </footer>
    </div>
  );
}
