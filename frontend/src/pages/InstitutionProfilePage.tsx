import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '@/lib/api';
import Loading from '@/components/Loading';

export default function InstitutionProfilePage() {
  const { id } = useParams<{ id: string }>();
  const [profile, setProfile] = useState<any>(null);
  const [posts, setPosts] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('');

  useEffect(() => {
    async function loadProfileData() {
      if (!id) return;
      try {
        setLoading(true);
        const parsedId = parseInt(id);
        const profileData = await api.getInstitution(parsedId);
        setProfile(profileData);

        // Fetch posts specific to this institution's owner user_id
        const postsData = await api.getPosts({ institution_id: profileData.user_id });
        setPosts(postsData);
      } catch (err) {
        console.error('Error loading institution profile:', err);
      } finally {
        setLoading(false);
      }
    }
    loadProfileData();
  }, [id]);

  const filteredPosts = selectedCategory
    ? posts.filter((p) => p.type === selectedCategory)
    : posts;

  const getMediaUrl = (url: string) => {
    if (!url) return '';
    if (url.startsWith('http')) return url;
    return `${import.meta.env.VITE_API_URL || ''}${url}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <Loading />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-400 flex flex-col items-center justify-center p-6 text-center">
        <span className="text-5xl">🏛️</span>
        <p className="mt-4 font-bold">Institution Profile Not Found</p>
        <Link to="/" className="mt-6 px-4 py-2 bg-indigo-500 rounded-lg text-white font-medium hover:bg-indigo-600 transition">
          Return to Feed
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans pb-16">
      {/* Top Banner Cover */}
      <div className="h-64 md:h-80 w-full relative overflow-hidden bg-slate-900 border-b border-slate-800">
        <img
          src={profile.banner_url || 'https://images.unsplash.com/photo-1541339907198-e08756dedf3f?auto=format&fit=crop&q=80&w=1200'}
          alt="Cover Banner"
          className="w-full h-full object-cover opacity-80"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/20 to-transparent" />

        <Link
          to="/"
          className="absolute top-6 left-6 px-4 py-2 rounded-xl text-xs font-semibold uppercase tracking-wider bg-slate-900/60 border border-slate-800 hover:bg-slate-800 text-white backdrop-blur-md transition flex items-center gap-2"
        >
          ← Feed Home
        </Link>
      </div>

      {/* Main Profile Header */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 -mt-24 relative z-10 space-y-8">
        
        {/* Profile Card Overlay */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 md:p-8 backdrop-blur-md shadow-2xl flex flex-col md:flex-row items-center md:items-end gap-6">
          <img
            src={profile.logo_url || 'https://images.unsplash.com/photo-1546410531-bb4caa6b424d?auto=format&fit=crop&q=80&w=200'}
            alt={profile.name}
            className="w-32 h-32 md:w-36 md:h-36 rounded-2xl object-cover border-4 border-slate-900 shadow-xl bg-slate-950"
          />

          <div className="flex-1 text-center md:text-left space-y-2">
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
              {profile.name}
            </h1>
            <p className="text-xs text-indigo-400 font-semibold uppercase tracking-wider">Educational Institute</p>
            
            <div className="flex flex-wrap items-center justify-center md:justify-start gap-4 text-xs text-slate-400 pt-2">
              {profile.contact_email && (
                <span className="flex items-center gap-1.5">
                  ✉️ <a href={`mailto:${profile.contact_email}`} className="hover:underline">{profile.contact_email}</a>
                </span>
              )}
              {profile.phone && <span className="flex items-center gap-1.5">📞 {profile.phone}</span>}
              {profile.website_url && (
                <span className="flex items-center gap-1.5">
                  🌐 <a href={profile.website_url} target="_blank" rel="noreferrer" className="hover:underline text-indigo-400">{profile.website_url}</a>
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Content Section: Split Screen Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left Column: About Panel */}
          <aside className="space-y-6">
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-sm space-y-4">
              <h2 className="text-base font-bold text-slate-200">About Institute</h2>
              <p className="text-xs text-slate-400 leading-relaxed whitespace-pre-line">
                {profile.about || 'No detailed biography provided.'}
              </p>
            </div>
          </aside>

          {/* Right Column: Published Content */}
          <main className="lg:col-span-2 space-y-6">
            {/* Category Filter */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <h2 className="text-lg font-bold">Announcements & Notices</h2>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500/50"
              >
                <option value="">All updates</option>
                <option value="news">News</option>
                <option value="notice">Notices</option>
                <option value="event">Events</option>
                <option value="pdf">Documents</option>
              </select>
            </div>

            {/* Gallery Timeline */}
            {filteredPosts.length === 0 ? (
              <div className="bg-slate-900/10 border border-dashed border-slate-800 rounded-2xl py-20 text-center text-slate-500">
                <span className="text-4xl">🏛️</span>
                <p className="mt-4 font-medium text-sm">No updates published under this category yet.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {filteredPosts.map((post) => (
                  <article
                    key={post.id}
                    className={`bg-slate-905 border rounded-2xl overflow-hidden transition-all duration-300 hover:shadow-lg hover:shadow-indigo-500/5 ${
                      post.is_pinned
                        ? 'border-amber-500/30 bg-gradient-to-b from-amber-500/5 to-transparent'
                        : 'border-slate-800/80 hover:border-slate-700/80'
                    }`}
                  >
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
                            className="w-full h-full object-cover"
                          />
                        )}
                      </div>
                    )}

                    <div className="p-5 space-y-3">
                      <div className="flex items-center justify-between text-[10px] text-slate-500">
                        <span className="font-semibold uppercase tracking-wider text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-md">
                          {post.type}
                        </span>
                        <span>
                          {new Date(post.created_at).toLocaleDateString(undefined, {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric',
                          })}
                        </span>
                      </div>

                      <h3 className="text-sm font-bold text-slate-100 line-clamp-1">{post.title}</h3>
                      <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed">{post.content}</p>

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
    </div>
  );
}
