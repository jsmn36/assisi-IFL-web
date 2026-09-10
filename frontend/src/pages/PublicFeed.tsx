import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api, { getMediaUrl, isVideoMedia } from '@/lib/api';
import Loading from '@/components/Loading';

export default function PublicFeed() {
  const [posts, setPosts] = useState<any[]>([]);
  const [institutions, setInstitutions] = useState<any[]>([]);
  const [selectedInst, setSelectedInst] = useState<number | null>(null);
  const [selectedType, setSelectedType] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  // Note Reader Modal State
  const [activeNote, setActiveNote] = useState<any | null>(null);
  const [copySuccess, setCopySuccess] = useState<boolean>(false);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [postsData, instsData] = await Promise.all([
          api.getPosts(),
          api.getInstitutions(),
        ]);
        setPosts(postsData || []);
        setInstitutions(instsData || []);
      } catch (err) {
        console.error('Error loading public feed data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleFilterChange = async (instId: number | null, type: string, search: string) => {
    try {
      setLoading(true);
      const params: any = {};
      if (instId !== null) params.institution_id = instId;
      if (type) params.type = type;
      if (search) params.search = search;

      const filteredPosts = await api.getPosts(params);
      setPosts(filteredPosts || []);
    } catch (err) {
      console.error('Error filtering posts:', err);
    } finally {
      setLoading(false);
    }
  };



  // Helper to download note as text file
  const downloadTextNote = (post: any) => {
    const textContent = `================================================
ASSISI SOCIAL GURUKULA NETWORK - OFFICIAL NOTE
================================================
Title: ${post.title}
Branch: ${post.institution_name || 'Gurukula Campus'}
Date: ${new Date(post.created_at).toLocaleDateString()}
Category: ${post.type ? post.type.toUpperCase() : 'GENERAL NOTE'}
------------------------------------------------

${post.content || 'No text content available.'}

------------------------------------------------
Attached Media: ${post.media_url ? getMediaUrl(post.media_url) : 'None'}
Hashtags: ${post.hashtags || 'None'}
================================================
Downloaded from Assisi Social Public Student Portal (Login-Free Access)
`;

    const blob = new Blob([textContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const sanitizedTitle = (post.title || 'Note').replace(/[^a-zA-Z0-9]/g, '_').toLowerCase();
    link.download = `${sanitizedTitle}_note.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const copyNoteToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2500);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans">
      {/* Top Navbar */}
      <header className="sticky top-0 z-40 backdrop-blur-md bg-slate-900/90 border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="bg-white p-1 rounded-xl shadow-lg shadow-rose-500/20 group-hover:scale-105 transition-transform">
              <img src="/logo.png" alt="ASSISI IFL Logo" className="h-9 w-auto object-contain" />
            </div>
            <div>
              <h1 className="text-lg font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-200 to-rose-300 bg-clip-text text-transparent">
                ASSISI IFL
              </h1>
              <p className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider">
                🔓 Free Student Notes & Feed Portal
              </p>
            </div>
          </Link>

          <div className="flex items-center gap-3">
            <Link
              to="/reels"
              className="px-3.5 py-1.5 bg-gradient-to-r from-rose-500 to-indigo-600 hover:from-rose-600 hover:to-indigo-700 text-white rounded-xl text-xs font-extrabold uppercase tracking-wider flex items-center gap-1.5 transition-all shadow-md"
            >
              <span>🎥 Watch Campus Reels</span>
            </Link>
            <span className="px-3.5 py-1.5 bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 rounded-xl text-xs font-bold uppercase tracking-wider hidden sm:flex items-center gap-1.5 shadow-sm">
              ✨ 100% Login-Free Access
            </span>
            <a
              href="http://localhost:3001"
              className="px-3.5 py-1.5 bg-rose-500/10 border border-rose-500/30 text-rose-300 hover:bg-rose-500/20 rounded-xl text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 transition-all shadow-sm"
              title="Super Admin Center Panel"
            >
              <span>🛡️ Super Admin Center</span>
            </a>
          </div>
        </div>
      </header>

      {/* Hero Banner */}
      <div className="bg-gradient-to-b from-indigo-950/40 via-slate-900/50 to-slate-950 border-b border-slate-800/80 py-10 px-4">
        <div className="max-w-7xl mx-auto text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-bold uppercase tracking-widest">
            <span>📚</span> Open Academic Resource & Notice Board
          </div>
          <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight text-white">
            View & Download Branch Notes, Announcements & Circulars
          </h2>
          <p className="text-sm text-slate-400 max-w-2xl mx-auto">
            Free access for all students and visitors across all 11 Gurukula branches. No login required. Read, search, and download official notes instantly.
          </p>
        </div>
      </div>

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col lg:flex-row gap-8">
        
        {/* Left Sidebar: Gurukula Branch Filters */}
        <aside className="w-full lg:w-80 shrink-0">
          <div className="sticky top-24 bg-slate-900/80 border border-slate-800 rounded-3xl p-5 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-extrabold text-sm text-white flex items-center gap-2">
                <span>🏫</span> Gurukula Branches
              </h3>
              <span className="text-[10px] bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded-md font-bold">
                {institutions.length} Branches
              </span>
            </div>

            <div className="space-y-1.5 max-h-[55vh] overflow-y-auto pr-1">
              <button
                onClick={() => {
                  setSelectedInst(null);
                  handleFilterChange(null, selectedType, searchQuery);
                }}
                className={`w-full text-left px-3.5 py-2.5 rounded-xl text-xs font-bold transition flex items-center justify-between ${
                  selectedInst === null
                    ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md'
                    : 'bg-slate-950/60 hover:bg-slate-800 text-slate-300 border border-slate-800'
                }`}
              >
                <span>🎓 All Gurukula Branches</span>
                <span className="text-[10px] opacity-75">All</span>
              </button>

              {institutions.map((inst) => (
                <button
                  key={inst.id}
                  onClick={() => {
                    setSelectedInst(inst.user_id);
                    handleFilterChange(inst.user_id, selectedType, searchQuery);
                  }}
                  className={`w-full text-left px-3.5 py-2.5 rounded-xl text-xs font-semibold transition flex items-center justify-between ${
                    selectedInst === inst.user_id
                      ? 'bg-indigo-600 text-white shadow-md'
                      : 'bg-slate-950/60 hover:bg-slate-800 text-slate-300 border border-slate-800'
                  }`}
                >
                  <span className="truncate pr-2">{inst.name}</span>
                  <span className="text-[9px] text-slate-400 shrink-0 bg-slate-900 px-1.5 py-0.5 rounded">
                    {inst.location || 'Branch'}
                  </span>
                </button>
              ))}
            </div>

            {/* Super Admin Center Access */}
            <div className="pt-3 border-t border-slate-800">
              <a
                href="http://localhost:3001"
                className="w-full text-center py-2.5 px-3 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-300 rounded-xl text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2 transition-all shadow-sm"
              >
                <span>🛡️</span> Super Admin Center Login
              </a>
            </div>
          </div>
        </aside>

        {/* Feed Content Middle */}
        <main className="flex-1 space-y-6">
          {/* Search Bar & Category Tabs */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-5 space-y-4 shadow-xl">
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-400">🔍</span>
              <input
                type="text"
                placeholder="Search notes, subjects, exam schedules, or circular titles..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  handleFilterChange(selectedInst, selectedType, e.target.value);
                }}
                className="w-full bg-slate-950 border border-slate-800 rounded-2xl pl-10 pr-4 py-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
            </div>

            {/* Category Filter Chips */}
            <div className="flex flex-wrap gap-2 pt-1">
              {[
                { id: '', label: '🌐 All Feed' },
                { id: 'notice', label: '📌 Official Notes & Circulars' },
                { id: 'news', label: '📰 News Updates' },
                { id: 'event', label: '🎉 Events' },
                { id: 'pdf', label: '📄 PDF Circulars' },
              ].map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => {
                    setSelectedType(cat.id);
                    handleFilterChange(selectedInst, cat.id, searchQuery);
                  }}
                  className={`px-3.5 py-2 rounded-xl text-xs font-bold transition uppercase tracking-wider ${
                    selectedType === cat.id
                      ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-md'
                      : 'bg-slate-950 text-slate-400 hover:bg-slate-800 hover:text-white border border-slate-800'
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>
          </div>

          {/* Feed Posts & Notes Grid */}
          {loading ? (
            <div className="py-24 flex justify-center"><Loading /></div>
          ) : posts.length === 0 ? (
            <div className="bg-slate-900/30 border border-dashed border-slate-800 rounded-3xl py-20 text-center text-slate-500">
              <span className="text-4xl">📭</span>
              <p className="mt-4 font-bold text-sm text-slate-300">No published notes or updates matching your search filters.</p>
              <p className="text-xs text-slate-500 mt-1">Try clearing the search box or selecting another Gurukula branch.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {posts.map((post) => (
                <article
                  key={post.id}
                  className="bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden flex flex-col justify-between hover:border-slate-700 transition duration-300 shadow-xl group"
                >
                  <div>
                    {/* Media Header */}
                    {post.media_url ? (
                      <div className="aspect-video w-full relative overflow-hidden bg-slate-950">
                        {isVideoMedia(post.type, post.media_url) ? (
                          <video src={getMediaUrl(post.media_url)} controls className="w-full h-full object-cover" />
                        ) : post.type === 'pdf' ? (
                          <div className="w-full h-full flex flex-col items-center justify-center bg-slate-950 p-6 text-center space-y-2">
                            <span className="text-4xl">📄</span>
                            <p className="text-xs font-bold text-indigo-400">PDF Circular / Document Note</p>
                            <a
                              href={getMediaUrl(post.media_url)}
                              download
                              target="_blank"
                              rel="noreferrer"
                              className="px-3.5 py-1.5 rounded-xl text-[10px] font-bold uppercase bg-indigo-600 hover:bg-indigo-500 text-white transition shadow-md"
                            >
                              📥 Download PDF Asset
                            </a>
                          </div>
                        ) : (
                          <img
                            src={getMediaUrl(post.media_url)}
                            alt={post.title}
                            className="w-full h-full object-cover group-hover:scale-105 transition duration-500"
                          />
                        )}
                      </div>
                    ) : (
                      <div className="h-2 w-full bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-400"></div>
                    )}

                    <div className="p-6 space-y-3">
                      <div className="flex justify-between items-center text-[10px] text-slate-400 uppercase tracking-widest font-bold">
                        <span className={`px-2.5 py-1 rounded-lg ${
                          post.type === 'notice' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                          post.type === 'event' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' :
                          'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                        }`}>
                          {post.type === 'notice' ? '📌 Official Note' : post.type}
                        </span>
                        <span>{new Date(post.created_at).toLocaleDateString()}</span>
                      </div>

                      <div>
                        <p className="text-[10px] text-emerald-400 font-extrabold uppercase tracking-wider">
                          🏫 {post.institution_name || 'Gurukula Campus'}
                        </p>
                        <h3 className="font-extrabold text-base text-white mt-0.5 line-clamp-2">
                          {post.title}
                        </h3>
                      </div>

                      <p className="text-xs text-slate-300 line-clamp-3 leading-relaxed whitespace-pre-line">
                        {post.content}
                      </p>

                      {post.hashtags && (
                        <div className="flex flex-wrap gap-1 pt-1">
                          {post.hashtags.split(',').map((tag: string, idx: number) => (
                            <span key={idx} className="text-[10px] text-indigo-400 bg-indigo-950/80 px-2 py-0.5 rounded-md font-semibold">
                              #{tag.trim()}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Actions: View & Download Note */}
                  <div className="p-4 bg-slate-950/80 border-t border-slate-800 flex gap-2">
                    <button
                      type="button"
                      onClick={() => setActiveNote(post)}
                      className="flex-1 py-2.5 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 font-bold text-xs uppercase rounded-xl border border-indigo-500/30 transition flex items-center justify-center gap-1.5 cursor-pointer"
                    >
                      👁️ Read Note
                    </button>

                    <button
                      type="button"
                      onClick={() => downloadTextNote(post)}
                      className="flex-1 py-2.5 bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-300 font-bold text-xs uppercase rounded-xl border border-emerald-500/30 transition flex items-center justify-center gap-1.5 cursor-pointer"
                    >
                      📥 Download Note
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </main>
      </div>

      {/* Note Reader & Downloader Modal */}
      {activeNote && (
        <div className="fixed inset-0 z-50 bg-slate-950/85 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-indigo-500/30 rounded-3xl max-w-2xl w-full p-6 md:p-8 space-y-6 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start border-b border-slate-800 pb-4">
              <div>
                <span className="text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-3 py-1 rounded-full font-bold uppercase">
                  🏫 {activeNote.institution_name || 'Gurukula Campus'}
                </span>
                <h3 className="font-extrabold text-xl text-white mt-2 leading-tight">
                  {activeNote.title}
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Published: {new Date(activeNote.created_at).toLocaleString()}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setActiveNote(null)}
                className="text-slate-400 hover:text-white text-xl font-bold p-1 cursor-pointer"
              >
                ✕
              </button>
            </div>

            {/* Note Content Body */}
            <div className="bg-slate-950 border border-slate-800 p-6 rounded-2xl space-y-4">
              <div className="flex justify-between items-center text-[10px] text-slate-500 font-bold uppercase tracking-widest">
                <span>Note Contents</span>
                <button
                  type="button"
                  onClick={() => copyNoteToClipboard(activeNote.content || '')}
                  className="text-indigo-400 hover:text-indigo-300 font-bold uppercase flex items-center gap-1 cursor-pointer"
                >
                  {copySuccess ? '✅ Copied!' : '📋 Copy Text'}
                </button>
              </div>

              <div className="text-sm text-slate-200 leading-relaxed whitespace-pre-line font-sans">
                {activeNote.content || 'No text description provided for this update.'}
              </div>

              {activeNote.media_url && (
                <div className="pt-4 border-t border-slate-850 space-y-2">
                  <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Attached File / Circular</p>
                  <a
                    href={getMediaUrl(activeNote.media_url)}
                    target="_blank"
                    rel="noreferrer"
                    download
                    className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold uppercase tracking-wider transition"
                  >
                    📥 Download Attached File / PDF
                  </a>
                </div>
              )}
            </div>

            {/* Modal Actions */}
            <div className="flex flex-col sm:flex-row gap-3 justify-end border-t border-slate-800 pt-4">
              <button
                type="button"
                onClick={() => setActiveNote(null)}
                className="px-5 py-2.5 bg-slate-950 border border-slate-800 hover:bg-slate-800 text-slate-300 rounded-xl text-xs font-bold uppercase transition cursor-pointer"
              >
                Close Reader
              </button>

              <button
                type="button"
                onClick={() => downloadTextNote(activeNote)}
                className="px-6 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white rounded-xl text-xs font-bold uppercase tracking-wider shadow-lg shadow-emerald-500/20 transition cursor-pointer flex items-center justify-center gap-2"
              >
                📥 Download Complete Note (.txt)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
