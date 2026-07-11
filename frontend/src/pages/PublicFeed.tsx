import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '@/lib/api';
import Loading from '@/components/Loading';

export default function PublicFeed() {
  const [posts, setPosts] = useState<any[]>([]);
  const [institutions, setInstitutions] = useState<any[]>([]);
  const [selectedInst, setSelectedInst] = useState<number | null>(null);
  const [selectedType, setSelectedType] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [postsData, instsData] = await Promise.all([
          api.getPosts(),
          api.getInstitutions(),
        ]);
        setPosts(postsData);
        setInstitutions(instsData);
      } catch (err) {
        console.error('Error loading feed data:', err);
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
      setPosts(filteredPosts);
    } catch (err) {
      console.error('Error filtering posts:', err);
    } finally {
      setLoading(false);
    }
  };

  const getMediaUrl = (url: string) => {
    if (!url) return '';
    if (url.startsWith('http')) return url;
    return `${import.meta.env.VITE_API_URL || ''}${url}`;
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans">
      {/* Top Premium Navbar */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-slate-900/80 border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <span className="text-xl font-bold tracking-tight text-white">A</span>
            </div>
            <div>
              <h1 className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-200 to-indigo-400 bg-clip-text text-transparent">
                Assisi Social
              </h1>
              <p className="text-[10px] text-slate-500 tracking-wider uppercase font-semibold">Community Engine</p>
            </div>
          </Link>

          <div className="flex items-center gap-4">
            <Link
              to="/login"
              className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white transition"
            >
              Sign In
            </Link>
            <Link
              to="/dashboard"
              className="px-4 py-2 rounded-xl text-sm font-semibold bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white shadow-md shadow-indigo-500/25 transition-all duration-300 hover:-translate-y-0.5"
            >
              Publisher Space
            </Link>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col lg:flex-row gap-8">
        
        {/* Sidebar Left: Institutions List */}
        <aside className="w-full lg:w-80 shrink-0">
          <div className="sticky top-24 bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm">
            <h2 className="text-lg font-bold mb-4 bg-gradient-to-r from-slate-200 to-indigo-300 bg-clip-text text-transparent">
              Registered Institutes
            </h2>
            <div className="space-y-2 max-h-[60vh] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-slate-800">
              <button
                onClick={() => {
                  setSelectedInst(null);
                  handleFilterChange(null, selectedType, searchQuery);
                }}
                className={`w-full text-left px-4 py-3 rounded-xl flex items-center gap-3 transition-all duration-300 ${
                  selectedInst === null
                    ? 'bg-gradient-to-r from-indigo-500/20 to-purple-500/10 border border-indigo-500/30 text-white shadow-md shadow-indigo-500/5'
                    : 'bg-slate-900/30 border border-slate-800 hover:bg-slate-800/40 text-slate-400 hover:text-slate-200'
                }`}
              >
                <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
                  🎓
                </div>
                <span className="font-semibold text-sm">All Institutions</span>
              </button>

              {institutions.map((inst) => (
                <button
                  key={inst.id}
                  onClick={() => {
                    setSelectedInst(inst.user_id);
                    handleFilterChange(inst.user_id, selectedType, searchQuery);
                  }}
                  className={`w-full text-left px-4 py-3 rounded-xl flex items-center gap-3 transition-all duration-300 ${
                    selectedInst === inst.user_id
                      ? 'bg-gradient-to-r from-indigo-500/20 to-purple-500/10 border border-indigo-500/30 text-white shadow-md shadow-indigo-500/5'
                      : 'bg-slate-900/30 border border-slate-800 hover:bg-slate-800/40 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <img
                    src={inst.logo_url || 'https://images.unsplash.com/photo-1546410531-bb4caa6b424d?auto=format&fit=crop&q=80&w=40'}
                    alt={inst.name}
                    className="w-8 h-8 rounded-lg object-cover border border-slate-850"
                  />
                  <div className="truncate">
                    <p className="font-semibold text-sm truncate">{inst.name}</p>
                    <p className="text-[10px] text-slate-500 truncate">{inst.website_url || 'Visit page'}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </aside>

        {/* Feed Content Middle */}
        <main className="flex-1 space-y-6">
          {/* Top Filter and Search Bar */}
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5 space-y-4 backdrop-blur-sm">
            <div className="flex flex-col sm:flex-row gap-4">
              {/* Search */}
              <div className="relative flex-1">
                <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">🔍</span>
                <input
                  type="text"
                  placeholder="Search events, tags, notices..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    handleFilterChange(selectedInst, selectedType, e.target.value);
                  }}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 transition-all duration-300"
                />
              </div>

              {/* Category Select */}
              <div className="flex gap-2 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
                {['', 'news', 'notice', 'event', 'pdf'].map((type) => (
                  <button
                    key={type}
                    onClick={() => {
                      setSelectedType(type);
                      handleFilterChange(selectedInst, type, searchQuery);
                    }}
                    className={`px-4 py-2 rounded-xl text-xs font-semibold uppercase tracking-wider border transition-all duration-300 ${
                      selectedType === type
                        ? 'bg-gradient-to-r from-indigo-500 to-purple-600 border-indigo-500 text-white shadow-md shadow-indigo-500/20'
                        : 'bg-slate-950 border-slate-850 text-slate-400 hover:bg-slate-900 hover:text-slate-200'
                    }`}
                  >
                    {type === '' ? 'All categories' : type}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Posts Feed Grid */}
          {loading ? (
            <div className="py-20 flex justify-center"><Loading /></div>
          ) : posts.length === 0 ? (
            <div className="bg-slate-900/20 border border-dashed border-slate-800 rounded-2xl py-20 text-center text-slate-500">
              <span className="text-4xl">📭</span>
              <p className="mt-4 font-medium text-sm">No updates published under these filters yet.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {posts.map((post) => (
                <article
                  key={post.id}
                  className={`bg-slate-905 border rounded-2xl overflow-hidden transition-all duration-300 hover:shadow-lg hover:shadow-indigo-500/5 ${
                    post.is_pinned
                      ? 'border-amber-500/30 shadow-md shadow-amber-500/5 bg-gradient-to-b from-amber-500/5 to-transparent'
                      : 'border-slate-800/80 hover:border-slate-700/80'
                  }`}
                >
                  {/* Pin label */}
                  {post.is_pinned && (
                    <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-1.5 flex items-center gap-1.5 text-xs text-amber-400 font-semibold uppercase tracking-wider">
                      <span>📌</span> Pinned Announcement
                    </div>
                  )}

                  {/* Post Image/Media representation */}
                  {post.media_url && (
                    <div className="aspect-video relative overflow-hidden bg-slate-950 border-b border-slate-850">
                      {post.type === 'video' ? (
                        <video
                          src={getMediaUrl(post.media_url)}
                          controls
                          className="w-full h-full object-cover"
                        />
                      ) : post.type === 'pdf' ? (
                        <div className="w-full h-full flex flex-col items-center justify-center bg-slate-900/50 p-6 text-center">
                          <span className="text-4xl">📄</span>
                          <p className="mt-2 text-xs font-semibold text-indigo-400">{post.title}.pdf</p>
                          <a
                            href={getMediaUrl(post.media_url)}
                            target="_blank"
                            rel="noreferrer"
                            className="mt-3 px-3 py-1.5 rounded-lg text-[10px] font-semibold uppercase bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 transition"
                          >
                            Open Document
                          </a>
                        </div>
                      ) : (
                        <img
                          src={getMediaUrl(post.media_url)}
                          alt={post.title}
                          className="w-full h-full object-cover transition-transform duration-500 hover:scale-105"
                        />
                      )}
                    </div>
                  )}

                  <div className="p-5 space-y-3">
                    {/* Header */}
                    <div className="flex items-center justify-between gap-2">
                      <Link
                        to={`/institutions/${post.institution_id}`}
                        className="text-xs font-bold text-indigo-400 hover:underline hover:text-indigo-300 transition"
                      >
                        {post.institution_name}
                      </Link>
                      <span className="text-[10px] text-slate-500">
                        {new Date(post.created_at).toLocaleDateString(undefined, {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                        })}
                      </span>
                    </div>

                    {/* Title */}
                    <h3 className="text-base font-bold text-slate-100 line-clamp-1">{post.title}</h3>

                    {/* Content */}
                    <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed">{post.content}</p>

                    {/* Footer Tags */}
                    {post.hashtags && (
                      <div className="flex flex-wrap gap-1.5 pt-2">
                        {post.hashtags.split(',').map((tag: string, idx: number) => (
                          <span
                            key={idx}
                            className="text-[10px] font-semibold text-slate-400 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded-md"
                          >
                            #{tag.trim()}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </article>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
