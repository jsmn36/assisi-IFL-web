import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api, { getMediaUrl, isVideoMedia } from '@/lib/api';
import { mockBranches, mockPosts } from '@/lib/mockData';
import Loading from '@/components/Loading';
import { getUploads } from '@/lib/storage';

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
        // Load initial posts from mock
        let allPosts = [...mockPosts];
        const localContents = await getUploads();
        if (localContents.length > 0) {
          allPosts = [...localContents, ...allPosts];
        }
        setPosts(allPosts);
        
        // Mock institutions from the branch list
        setInstitutions(mockBranches.map(b => ({
          id: b.id,
          user_id: b.id,
          name: b.name,
          location: b.location,
        })));
      } catch (err) {
        console.error('Error loading public feed data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleFilterChange = async (instId: number | null, type: string, search: string) => {
    try {
      setLoading(true);
      
      // Filter the local mockPosts + uploaded contents array
      const localContents = await getUploads();
      let filtered = [...localContents, ...mockPosts];
      
      if (instId !== null) {
        filtered = filtered.filter(p => p.institution_id === instId);
      }
      
      if (type) {
        filtered = filtered.filter(p => p.type === type);
      }
      
      if (search) {
        const query = search.toLowerCase();
        filtered = filtered.filter(p => 
          p.title.toLowerCase().includes(query) || 
          p.content.toLowerCase().includes(query)
        );
      }

      // Simulate network delay
      await new Promise(resolve => setTimeout(resolve, 300));
      setPosts(filtered);
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
    <div className="min-h-screen bg-[#111111] text-slate-100 font-sans">
      {/* Top Navbar */}
      <header className="sticky top-0 z-40 backdrop-blur-md bg-[#111111]/90 border-b border-[#333333]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="group-hover:scale-105 transition-transform">
              <img src="/logo.png" alt="ASSISI IFL Logo" className="h-20 w-auto object-contain drop-shadow-lg" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white">
                Assisi IFL
              </h1>
              <p className="text-[10px] text-emerald-400 font-semibold uppercase tracking-widest mt-0.5">
                🔓 Free Student Notes & Feed Portal
              </p>
            </div>
          </Link>

          <div className="flex items-center gap-3">
            <Link
              to="/reels"
              className="px-4 py-2 bg-white/5 border border-[#333333] hover:bg-white/10 text-slate-300 rounded-full text-[10px] font-bold uppercase tracking-wider flex items-center gap-2 transition-all shadow-sm"
            >
              <span>🎥 Watch Campus Reels</span>
            </Link>
            <span className="px-4 py-2 bg-[#D4AF37]/10 border border-[#D4AF37]/30 text-[#D4AF37] rounded-full text-[10px] font-bold uppercase tracking-wider hidden sm:flex items-center gap-2 shadow-[0_0_15px_rgba(212,175,55,0.15)]">
              ✨ 100% Login-Free Access
            </span>
            <Link
              to="/admin-login"
              className="px-4 py-2 bg-white/5 border border-[#333333] text-slate-300 hover:bg-white/10 rounded-full text-[10px] font-bold uppercase tracking-wider flex items-center gap-2 transition-all shadow-sm"
              title="Super Admin Center Panel"
            >
              <span>🛡️ Super Admin Center</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Banner */}
      <div className="py-12 px-4">
        <div className="max-w-7xl mx-auto text-center space-y-4">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#1A1A1A] border border-[#333333] text-blue-400 text-[10px] font-bold uppercase tracking-widest">
            <span>📚</span> Open Academic Resource & Notice Board
          </div>
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-white">
            View & Download Branch Notes, Announcements & Circulars
          </h2>
          <p className="text-sm text-slate-400 max-w-2xl mx-auto font-light">
            Free access for all students and visitors across all 11 Gurukula branches. No login required. Read, search, and download official notes instantly.
          </p>
        </div>
      </div>

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 flex flex-col lg:flex-row gap-6">
        
        {/* Left Sidebar: Gurukula Branch Filters */}
        <aside className="w-full lg:w-80 shrink-0">
          <div className="sticky top-28 bg-[#1A1A1A] border border-[#333333] rounded-3xl p-5 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-2">
              <h3 className="font-bold text-sm text-slate-200 flex items-center gap-2">
                <span>🏫</span> Gurukula Branches
              </h3>
              <span className="text-[10px] bg-white/5 border border-[#333333] text-slate-400 px-2 py-0.5 rounded-md font-bold">
                11 Branches
              </span>
            </div>

            <div className="space-y-1.5 max-h-[60vh] overflow-y-auto pr-1">
              <button
                onClick={() => {
                  setSelectedInst(null);
                  handleFilterChange(null, selectedType, searchQuery);
                }}
                className={`w-full text-left px-4 py-3 rounded-xl text-xs font-semibold transition flex items-center justify-between ${
                  selectedInst === null
                    ? 'bg-blue-600/20 border border-blue-500/30 text-blue-400'
                    : 'bg-transparent hover:bg-white/5 text-slate-400 border border-transparent'
                }`}
              >
                <span>All Gurukula Branches</span>
              </button>

              {institutions.map((inst) => (
                <button
                  key={inst.id}
                  onClick={() => {
                    setSelectedInst(inst.user_id);
                    handleFilterChange(inst.user_id, selectedType, searchQuery);
                  }}
                  className={`w-full text-left px-4 py-3 rounded-xl text-xs font-medium transition flex items-center justify-between border-b border-[#222222] last:border-0 ${
                    selectedInst === inst.user_id
                      ? 'text-blue-400'
                      : 'bg-transparent hover:bg-white/5 text-slate-400'
                  }`}
                >
                  <span className="truncate pr-2">{inst.name}</span>
                  <span className="text-[9px] text-slate-500 shrink-0">
                    {inst.location || 'Branch'}
                  </span>
                </button>
              ))}
            </div>

            {/* Super Admin Center Access */}
            <div className="pt-4 mt-2 border-t border-[#333333]">
              <Link
                to="/admin-login"
                className="w-full text-center py-2.5 px-3 bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 rounded-full text-[10px] font-bold uppercase tracking-wider flex items-center justify-center gap-2 transition-all shadow-sm"
              >
                <span>🛡️</span> SUPER ADMIN CENTER LOGIN
              </Link>
            </div>
          </div>
        </aside>

        {/* Feed Content Middle */}
        <main className="flex-1 space-y-6">
          {/* Search Bar & Category Tabs */}
          <div className="bg-[#1A1A1A] border border-[#333333] rounded-3xl p-5 space-y-4 shadow-2xl">
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-4 text-slate-500">🔍</span>
              <input
                type="text"
                placeholder="Search notes, subjects, exam schedules, or circular titles..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  handleFilterChange(selectedInst, selectedType, e.target.value);
                }}
                className="w-full bg-[#111111] border border-[#333333] rounded-full pl-11 pr-4 py-3 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500 transition-colors"
              />
              <span className="absolute inset-y-0 right-0 flex items-center pr-4 text-slate-600">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"></path></svg>
              </span>
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
                  className={`px-4 py-2 rounded-full text-[10px] font-bold transition uppercase tracking-wider ${
                    selectedType === cat.id
                      ? 'bg-blue-600 text-white shadow-lg'
                      : 'bg-[#111111] text-slate-400 hover:bg-[#222222] border border-[#333333]'
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
            <div className="bg-[#1A1A1A] border border-dashed border-[#333333] rounded-3xl py-20 text-center text-slate-500">
              <span className="text-4xl">📭</span>
              <p className="mt-4 font-bold text-sm text-slate-300">No published notes or updates matching your search filters.</p>
              <p className="text-xs text-slate-500 mt-1">Try clearing the search box or selecting another Gurukula branch.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {posts.map((post) => (
                <article
                  key={post.id}
                  className={`bg-[#1A1A1A] border rounded-3xl overflow-hidden flex flex-col justify-between hover:border-slate-600 transition duration-300 shadow-2xl group ${
                    post.type === 'notice' 
                      ? 'border-[#D4AF37]/50 shadow-[0_-5px_30px_rgba(212,175,55,0.08)]' 
                      : 'border-[#333333]'
                  }`}
                >
                  <div>
                    {/* Media Header */}
                    {post.media_url ? (
                      <div className="aspect-video w-full relative overflow-hidden bg-[#111111] border-b border-[#333333]">
                        {isVideoMedia(post.type, post.media_url) ? (
                          <video src={getMediaUrl(post.media_url)} controls className="w-full h-full object-cover" />
                        ) : post.type === 'pdf' ? (
                          <div className="w-full h-full flex flex-col items-center justify-center p-6 text-center space-y-2">
                            <span className="text-4xl">📄</span>
                            <p className="text-xs font-bold text-slate-400">PDF Document</p>
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
                      <div className={`h-1.5 w-full ${post.type === 'notice' ? 'bg-gradient-to-r from-[#D4AF37] to-amber-200' : 'bg-[#333333]'}`}></div>
                    )}

                    <div className="p-6 space-y-3">
                      <div className="flex justify-between items-center text-[10px] text-slate-500 uppercase tracking-widest font-bold">
                        <span className={`flex items-center gap-1.5 ${
                          post.type === 'notice' ? 'text-[#D4AF37]' :
                          'text-blue-400'
                        }`}>
                          {post.type === 'notice' ? '📌 OFFICIAL NOTE' : post.type === 'pdf' ? '📄 PDF NOTE' : '📰 UPDATE'}
                        </span>
                        <span>{new Date(post.created_at).toLocaleDateString()}</span>
                      </div>

                      <div>
                        <p className="text-[9px] text-emerald-400 font-bold uppercase tracking-widest flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                          {post.institution_name || 'GURUKULA CAMPUS'}
                        </p>
                        <h3 className="font-semibold text-lg text-slate-100 mt-1 line-clamp-2 leading-snug">
                          {post.title}
                        </h3>
                      </div>

                      <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed whitespace-pre-line font-light">
                        {post.content}
                      </p>

                      {post.hashtags && (
                        <div className="flex flex-wrap gap-1.5 pt-2">
                          {post.hashtags.split(',').map((tag: string, idx: number) => (
                            <span key={idx} className="text-[10px] text-slate-400 bg-white/5 border border-[#333333] px-2 py-0.5 rounded-full font-medium">
                              #{tag.trim()}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Actions: View & Download Note */}
                  <div className="p-5 flex gap-3 border-t border-[#333333]">
                    <button
                      type="button"
                      onClick={() => setActiveNote(post)}
                      className="flex-1 py-2.5 bg-white/5 hover:bg-white/10 text-slate-300 font-bold text-[10px] uppercase rounded-full border border-[#333333] transition flex items-center justify-center gap-2 cursor-pointer"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path></svg>
                      READ NOTE
                    </button>

                    <button
                      type="button"
                      onClick={() => downloadTextNote(post)}
                      className="flex-1 py-2.5 bg-white/5 hover:bg-white/10 text-slate-300 font-bold text-[10px] uppercase rounded-full border border-[#333333] transition flex items-center justify-center gap-2 cursor-pointer"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                      DOWNLOAD NOTE
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
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#1A1A1A] border border-[#333333] rounded-3xl max-w-2xl w-full p-6 md:p-8 space-y-6 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start border-b border-[#333333] pb-4">
              <div>
                <span className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-3 py-1 rounded-full font-bold uppercase tracking-widest">
                  🏫 {activeNote.institution_name || 'Gurukula Campus'}
                </span>
                <h3 className="font-bold text-2xl text-white mt-3 leading-tight">
                  {activeNote.title}
                </h3>
                <p className="text-xs text-slate-400 mt-2 font-medium">
                  Published: {new Date(activeNote.created_at).toLocaleString()}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setActiveNote(null)}
                className="text-slate-400 hover:text-white bg-white/5 hover:bg-white/10 rounded-full w-8 h-8 flex items-center justify-center transition-colors cursor-pointer"
              >
                ✕
              </button>
            </div>

            {/* Note Content Body */}
            <div className="bg-[#111111] border border-[#333333] p-6 rounded-2xl space-y-4">
              <div className="flex justify-between items-center text-[10px] text-slate-500 font-bold uppercase tracking-widest">
                <span>Note Contents</span>
                <button
                  type="button"
                  onClick={() => copyNoteToClipboard(activeNote.content || '')}
                  className="text-blue-400 hover:text-blue-300 font-bold uppercase flex items-center gap-1.5 cursor-pointer bg-blue-500/10 px-3 py-1.5 rounded-full"
                >
                  {copySuccess ? '✅ COPIED!' : '📋 COPY TEXT'}
                </button>
              </div>

              <div className="text-sm text-slate-300 leading-relaxed whitespace-pre-line font-light">
                {activeNote.content || 'No text description provided for this update.'}
              </div>

              {activeNote.media_url && (
                <div className="pt-4 border-t border-[#222222] space-y-3">
                  <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Attached File / Circular</p>
                  <a
                    href={getMediaUrl(activeNote.media_url)}
                    target="_blank"
                    rel="noreferrer"
                    download
                    className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-full text-[10px] font-bold uppercase tracking-wider transition shadow-lg shadow-blue-500/20"
                  >
                    📥 Download Attached File / PDF
                  </a>
                </div>
              )}
            </div>
            
            <div className="pt-2 text-center text-[10px] text-slate-500 uppercase font-medium tracking-wider">
              Assisi Social Platform • Verified Internal Circular
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
