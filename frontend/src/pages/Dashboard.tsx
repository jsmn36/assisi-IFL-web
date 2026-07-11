import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '@/lib/api';
import Loading from '@/components/Loading';

export default function Dashboard() {
  const navigate = useNavigate();
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [profile, setProfile] = useState<any>(null);
  const [posts, setPosts] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Form states: Post Creation
  const [postTitle, setPostTitle] = useState('');
  const [postContent, setPostContent] = useState('');
  const [postType, setPostType] = useState('news');
  const [postMediaUrl, setPostMediaUrl] = useState('');
  const [postIsPinned, setPostIsPinned] = useState(false);
  const [postHashtags, setPostHashtags] = useState('');

  // Form states: Profile Update
  const [profileName, setProfileName] = useState('');
  const [profileAbout, setProfileAbout] = useState('');
  const [profileEmail, setProfileEmail] = useState('');
  const [profilePhone, setProfilePhone] = useState('');
  const [profileWebsite, setProfileWebsite] = useState('');

  // Editing post states
  const [editingPostId, setEditingPostId] = useState<number | null>(null);

  // Tab control
  const [activeTab, setActiveTab] = useState<'posts' | 'new-post' | 'profile'>('posts');
  const [mediaUploading, setMediaUploading] = useState(false);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        setLoading(true);
        // Check current authenticated user details
        const me = await api.getMe();
        setCurrentUser(me);

        // If user is superadmin, redirect to admin panel
        if (me.role === 'admin') {
          navigate('/admin-panel');
          return;
        }

        // Get matching InstitutionProfile using lists filter
        const institutions = await api.getInstitutions();
        const myProfile = institutions.find((inst) => inst.user_id === me.id);
        
        if (myProfile) {
          setProfile(myProfile);
          setProfileName(myProfile.name || '');
          setProfileAbout(myProfile.about || '');
          setProfileEmail(myProfile.contact_email || '');
          setProfilePhone(myProfile.phone || '');
          setProfileWebsite(myProfile.website_url || '');

          // Get posts specific to me
          const postsData = await api.getPosts({ institution_id: me.id });
          setPosts(postsData);
        } else {
          // No profile yet, create profile tab automatically
          setActiveTab('profile');
        }
      } catch (err) {
        console.error('Unauthorized. Redirecting to login.', err);
        navigate('/login');
      } finally {
        setLoading(false);
      }
    }
    loadDashboardData();
  }, [navigate]);

  const handleMediaUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    try {
      setMediaUploading(true);
      const res = await api.uploadMedia(file);
      setPostMediaUrl(res.url);
    } catch (err) {
      alert('Error uploading media. Supported files are images, videos, and PDFs under 50MB.');
    } finally {
      setMediaUploading(false);
    }
  };

  const handlePublishPost = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!postTitle.trim()) return;

    try {
      setLoading(true);
      const payload = {
        title: postTitle,
        content: postContent,
        type: postType,
        media_url: postMediaUrl,
        is_pinned: postIsPinned,
        hashtags: postHashtags,
      };

      if (editingPostId) {
        await api.updatePost(editingPostId, payload);
        alert('Post updated successfully!');
      } else {
        await api.createPost(payload);
        alert('Post published successfully!');
      }

      // Reset form fields
      setPostTitle('');
      setPostContent('');
      setPostType('news');
      setPostMediaUrl('');
      setPostIsPinned(false);
      setPostHashtags('');
      setEditingPostId(null);

      // Refresh list
      const postsData = await api.getPosts({ institution_id: currentUser.id });
      setPosts(postsData);
      setActiveTab('posts');
    } catch (err) {
      console.error('Publish failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profileName.trim()) return;

    try {
      setLoading(true);
      const payload = {
        name: profileName,
        about: profileAbout,
        contact_email: profileEmail,
        phone: profilePhone,
        website_url: profileWebsite,
      };

      // Since profile id might not be loaded initially if profile was created manually
      if (profile) {
        const updated = await api.updateInstitution(profile.id, payload);
        setProfile(updated);
        alert('Profile saved successfully!');
      }
    } catch (err) {
      console.error('Error saving profile:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleEditPost = (post: any) => {
    setEditingPostId(post.id);
    setPostTitle(post.title);
    setPostContent(post.content || '');
    setPostType(post.type);
    setPostMediaUrl(post.media_url || '');
    setPostIsPinned(post.is_pinned);
    setPostHashtags(post.hashtags || '');
    setActiveTab('new-post');
  };

  const handleDeletePost = async (id: number) => {
    if (!confirm('Are you sure you want to delete this post?')) return;
    try {
      setLoading(true);
      await api.deletePost(id);
      setPosts(posts.filter((p) => p.id !== id));
      alert('Post deleted!');
    } catch (err) {
      console.error('Error deleting post:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch (err) {
      console.error('Logout error:', err);
    }
    localStorage.clear();
    navigate('/login');
  };

  if (loading && !currentUser) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <Loading />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans flex">
      {/* Sidebar navigation */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 shrink-0 hidden md:block">
        <div className="p-6 h-full flex flex-col justify-between">
          <div className="space-y-8">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center">🏫</div>
              <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white to-indigo-300 bg-clip-text text-transparent">
                Assisi Social
              </span>
            </Link>

            <div className="space-y-1">
              <button
                onClick={() => {
                  setEditingPostId(null);
                  setActiveTab('posts');
                }}
                className={`w-full text-left px-4 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider transition ${
                  activeTab === 'posts' ? 'bg-indigo-500/10 text-indigo-400' : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
                }`}
              >
                📋 Published Posts
              </button>
              <button
                onClick={() => {
                  setEditingPostId(null);
                  setActiveTab('new-post');
                }}
                className={`w-full text-left px-4 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider transition ${
                  activeTab === 'new-post' ? 'bg-indigo-500/10 text-indigo-400' : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
                }`}
              >
                ✍️ Write Update
              </button>
              <button
                onClick={() => setActiveTab('profile')}
                className={`w-full text-left px-4 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider transition ${
                  activeTab === 'profile' ? 'bg-indigo-500/10 text-indigo-400' : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
                }`}
              >
                🏛️ Profile Settings
              </button>
            </div>
          </div>

          <div className="space-y-4">
            <div className="bg-slate-950 border border-slate-850 p-4 rounded-xl space-y-1">
              <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Logged In As</p>
              <p className="text-xs font-bold text-slate-300 truncate">{currentUser?.username}</p>
            </div>
            <button
              onClick={handleLogout}
              className="w-full py-2.5 bg-rose-600/10 hover:bg-rose-600/25 border border-rose-600/20 rounded-xl text-rose-400 font-semibold text-xs transition uppercase tracking-wider"
            >
              Sign Out
            </button>
          </div>
        </div>
      </aside>

      {/* Main panel content */}
      <main className="flex-1 min-h-screen overflow-y-auto bg-slate-955/40 p-6 md:p-10 space-y-8">
        
        {/* Mobile top navigation header */}
        <div className="md:hidden flex items-center justify-between border-b border-slate-850 pb-4">
          <Link to="/" className="flex items-center gap-1.5">
            <span className="text-lg">🏫</span>
            <span className="font-extrabold text-sm tracking-tight text-white">Assisi Social</span>
          </Link>
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('posts')}
              className={`px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase ${
                activeTab === 'posts' ? 'bg-indigo-500 text-white' : 'bg-slate-900 text-slate-400'
              }`}
            >
              Feed
            </button>
            <button
              onClick={() => setActiveTab('new-post')}
              className={`px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase ${
                activeTab === 'new-post' ? 'bg-indigo-500 text-white' : 'bg-slate-900 text-slate-400'
              }`}
            >
              Write
            </button>
            <button
              onClick={() => setActiveTab('profile')}
              className={`px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase ${
                activeTab === 'profile' ? 'bg-indigo-500 text-white' : 'bg-slate-900 text-slate-400'
              }`}
            >
              Bio
            </button>
            <button onClick={handleLogout} className="px-3 py-1.5 rounded-lg bg-rose-500/20 text-rose-400 text-[10px] font-bold uppercase">
              Out
            </button>
          </div>
        </div>

        {/* Dynamic header summary */}
        <div>
          <h2 className="text-2xl font-extrabold tracking-tight text-white">
            {activeTab === 'posts' && '📋 Published Posts Gallery'}
            {activeTab === 'new-post' && (editingPostId ? '✍️ Update Published Story' : '✍️ Write Community Update')}
            {activeTab === 'profile' && '🏛️ Institution Profile Setup'}
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            {activeTab === 'posts' && 'Observe, modify, and delete the articles currently live on the public feed.'}
            {activeTab === 'new-post' && 'Compose beautiful text and upload rich media to showcase updates.'}
            {activeTab === 'profile' && 'Edit display properties, banner displays, logo representations, and contacts.'}
          </p>
        </div>

        {/* Tab 1: Posts gallery */}
        {activeTab === 'posts' && (
          <div className="space-y-6">
            {posts.length === 0 ? (
              <div className="bg-slate-900/10 border border-dashed border-slate-800 rounded-3xl py-24 text-center text-slate-500">
                <span className="text-4xl">📝</span>
                <p className="mt-4 font-semibold text-sm">You haven't published any stories yet.</p>
                <button
                  onClick={() => setActiveTab('new-post')}
                  className="mt-6 px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-500 hover:bg-indigo-600 text-white transition"
                >
                  Write Your First Post
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {posts.map((post) => (
                  <div key={post.id} className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden flex flex-col justify-between">
                    <div>
                      {post.media_url && (
                        <div className="aspect-video w-full relative overflow-hidden bg-slate-950">
                          {post.type === 'video' ? (
                            <video src={post.media_url} className="w-full h-full object-cover" />
                          ) : (
                            <img src={post.media_url} alt={post.title} className="w-full h-full object-cover" />
                          )}
                        </div>
                      )}
                      <div className="p-5 space-y-2">
                        <div className="flex justify-between items-center text-[10px] text-slate-500 uppercase tracking-widest font-bold">
                          <span>{post.type}</span>
                          <span>{post.is_pinned ? '📌 Pinned' : ''}</span>
                        </div>
                        <h3 className="font-bold text-sm text-slate-100">{post.title}</h3>
                        <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed">{post.content}</p>
                      </div>
                    </div>

                    <div className="p-5 pt-0 border-t border-slate-850 flex gap-2">
                      <button
                        onClick={() => handleEditPost(post)}
                        className="flex-1 py-1.5 bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 font-semibold text-[10px] uppercase rounded-lg transition"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDeletePost(post.id)}
                        className="flex-1 py-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 font-semibold text-[10px] uppercase rounded-lg transition"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Write post */}
        {activeTab === 'new-post' && (
          <form onSubmit={handlePublishPost} className="bg-slate-900 border border-slate-800 rounded-3xl p-6 md:p-8 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Left Column Fields */}
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-400">Headline/Title</label>
                  <input
                    type="text"
                    required
                    value={postTitle}
                    onChange={(e) => setPostTitle(e.target.value)}
                    placeholder="E.g. Spring Fest registrations open!"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-400">Post Type/Category</label>
                  <select
                    value={postType}
                    onChange={(e) => setPostType(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:border-indigo-500"
                  >
                    <option value="news">News Update</option>
                    <option value="notice">Official Notice</option>
                    <option value="event">Campus Event</option>
                    <option value="pdf">Document / Newsletter (PDF)</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-400">Hashtags (Comma-separated)</label>
                  <input
                    type="text"
                    value={postHashtags}
                    onChange={(e) => setPostHashtags(e.target.value)}
                    placeholder="E.g. campus, sports, registration"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="flex items-center gap-3 pt-2">
                  <input
                    type="checkbox"
                    id="is_pinned"
                    checked={postIsPinned}
                    onChange={(e) => setPostIsPinned(e.target.checked)}
                    className="w-4 h-4 text-indigo-500 border-slate-800 bg-slate-955 rounded focus:ring-indigo-500/20"
                  />
                  <label htmlFor="is_pinned" className="text-xs font-semibold text-slate-300">
                    📌 Pin this post to top of official Notice Board
                  </label>
                </div>
              </div>

              {/* Right Column Media uploading */}
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-400">Media Content Upload</label>
                  
                  {postMediaUrl ? (
                    <div className="border border-slate-800 rounded-xl p-4 bg-slate-950 space-y-2">
                      <p className="text-[10px] text-slate-500 uppercase tracking-widest">Media asset ready</p>
                      <p className="text-xs truncate text-indigo-400 font-bold">{postMediaUrl}</p>
                      <button
                        type="button"
                        onClick={() => setPostMediaUrl('')}
                        className="text-[10px] font-bold text-rose-400 uppercase tracking-wider hover:underline"
                      >
                        Remove file
                      </button>
                    </div>
                  ) : (
                    <div className="border border-dashed border-slate-800 rounded-xl p-6 bg-slate-950 flex flex-col items-center justify-center text-center">
                      {mediaUploading ? (
                        <div className="space-y-2">
                          <Loading />
                          <p className="text-[10px] text-slate-500">Uploading rich media asset...</p>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          <span className="text-2xl">📁</span>
                          <p className="text-xs text-slate-400">Select images, mp4 videos, or PDF circulars</p>
                          <label className="inline-block px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl cursor-pointer transition">
                            Browse Local Files
                            <input
                              type="file"
                              onChange={handleMediaUpload}
                              className="hidden"
                              accept="image/*,video/*,application/pdf"
                            />
                          </label>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-400">Body Description/Content</label>
                  <textarea
                    rows={4}
                    value={postContent}
                    onChange={(e) => setPostContent(e.target.value)}
                    placeholder="Describe what this announcement is about..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:border-indigo-500 resize-none"
                  />
                </div>
              </div>
            </div>

            <div className="border-t border-slate-850 pt-6 flex gap-3 justify-end">
              <button
                type="button"
                onClick={() => {
                  setEditingPostId(null);
                  setActiveTab('posts');
                }}
                className="px-6 py-2.5 bg-slate-950 border border-slate-800 hover:bg-slate-900 rounded-xl text-xs font-semibold uppercase transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-6 py-2.5 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 rounded-xl text-xs font-semibold text-white shadow-md shadow-indigo-500/20 transition uppercase"
              >
                {editingPostId ? 'Save Changes' : 'Publish to Public Feed'}
              </button>
            </div>
          </form>
        )}

        {/* Tab 3: Profile settings */}
        {activeTab === 'profile' && (
          <form onSubmit={handleSaveProfile} className="bg-slate-900 border border-slate-800 rounded-3xl p-6 md:p-8 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Profile fields */}
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-400">Institution Name</label>
                  <input
                    type="text"
                    required
                    value={profileName}
                    onChange={(e) => setProfileName(e.target.value)}
                    placeholder="E.g. Assisi Engineering College"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-400">Contact Email</label>
                  <input
                    type="email"
                    value={profileEmail}
                    onChange={(e) => setProfileEmail(e.target.value)}
                    placeholder="E.g. contact@assisi.edu"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-400">Contact Telephone</label>
                  <input
                    type="text"
                    value={profilePhone}
                    onChange={(e) => setProfilePhone(e.target.value)}
                    placeholder="E.g. +91 98765 43210"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-400">Website URL</label>
                  <input
                    type="url"
                    value={profileWebsite}
                    onChange={(e) => setProfileWebsite(e.target.value)}
                    placeholder="E.g. https://assisi.edu"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              {/* Bio block */}
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-400">About / Bio description</label>
                  <textarea
                    rows={8}
                    value={profileAbout}
                    onChange={(e) => setProfileAbout(e.target.value)}
                    placeholder="Describe your history, standard of education, achievements, and courses..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:border-indigo-500 resize-none font-sans"
                  />
                </div>
              </div>
            </div>

            <div className="border-t border-slate-850 pt-6 flex justify-end">
              <button
                type="submit"
                className="px-6 py-2.5 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 rounded-xl text-xs font-semibold text-white shadow-md shadow-indigo-500/20 transition uppercase tracking-wider"
              >
                Save Profile Parameters
              </button>
            </div>
          </form>
        )}
      </main>
    </div>
  );
}
