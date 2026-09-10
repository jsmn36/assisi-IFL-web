import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api, { getMediaUrl, isVideoMedia } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import Loading from '@/components/Loading';

export default function Dashboard() {
  const navigate = useNavigate();
  const { logout: authLogout } = useAuth();
  
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [profile, setProfile] = useState<any>(null);
  const [posts, setPosts] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [feedbackMsg, setFeedbackMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Form states: Post Creation & Editing
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

  // Editing and Deleting post modal states
  const [editingPostId, setEditingPostId] = useState<number | null>(null);
  const [deletingPostId, setDeletingPostId] = useState<number | null>(null);
  const [showEditModal, setShowEditModal] = useState<boolean>(false);

  // Tab control
  const [activeTab, setActiveTab] = useState<'posts' | 'new-post' | 'profile'>('posts');
  const [mediaUploading, setMediaUploading] = useState(false);

  // Load user data and posts on mount
  const refreshData = async () => {
    try {
      setLoading(true);
      const me = await api.getMe();
      setCurrentUser(me);

      if (me.role === 'admin') {
        navigate('/admin-panel');
        return;
      }

      // Load Profile
      const institutions = await api.getInstitutions();
      const myProfile = institutions.find((inst: any) => Number(inst.user_id) === Number(me.id));
      
      if (myProfile) {
        setProfile(myProfile);
        setProfileName(myProfile.name || '');
        setProfileAbout(myProfile.about || '');
        setProfileEmail(myProfile.contact_email || '');
        setProfilePhone(myProfile.phone || '');
        setProfileWebsite(myProfile.website_url || '');
      }

      // Load Posts specific to this institution user
      const postsData = await api.getPosts({ institution_id: me.id });
      setPosts(postsData || []);
    } catch (err) {
      console.error('Error loading dashboard data:', err);
      authLogout();
      navigate('/login', { replace: true });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshData();
  }, [navigate]);

  const showToast = (type: 'success' | 'error', text: string) => {
    setFeedbackMsg({ type, text });
    setTimeout(() => setFeedbackMsg(null), 4000);
  };

  const handleMediaUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    try {
      setMediaUploading(true);
      const res = await api.uploadMedia(file);
      setPostMediaUrl(res.url);

      const ext = file.name.toLowerCase().split('.').pop() || '';
      if (['mp4', 'mov', 'avi', 'webm', 'mkv'].includes(ext)) {
        setPostType('video');
      } else if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp'].includes(ext)) {
        if (postType === 'video' || postType === 'pdf') {
          setPostType('news');
        }
      } else if (ext === 'pdf') {
        setPostType('pdf');
      }

      showToast('success', 'Media uploaded successfully!');
    } catch (err) {
      showToast('error', 'Error uploading media. Please ensure file is under 50MB.');
    } finally {
      setMediaUploading(false);
    }
  };

  const resetPostForm = () => {
    setPostTitle('');
    setPostContent('');
    setPostType('news');
    setPostMediaUrl('');
    setPostIsPinned(false);
    setPostHashtags('');
    setEditingPostId(null);
    setShowEditModal(false);
  };

  const handleEditPostClick = (post: any) => {
    setEditingPostId(post.id);
    setPostTitle(post.title || '');
    setPostContent(post.content || '');
    setPostType(post.type || 'news');
    setPostMediaUrl(post.media_url || '');
    setPostIsPinned(Boolean(post.is_pinned));
    setPostHashtags(post.hashtags || '');
    setShowEditModal(true);
  };

  const handlePublishOrUpdatePost = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!postTitle.trim()) {
      showToast('error', 'Please enter a post title');
      return;
    }

    try {
      setActionLoading(true);
      const payload = {
        title: postTitle.trim(),
        content: postContent.trim(),
        type: postType,
        media_url: postMediaUrl || null,
        is_pinned: postIsPinned,
        hashtags: postHashtags.trim() || null,
      };

      if (editingPostId) {
        const updated = await api.updatePost(editingPostId, payload);
        setPosts((prev) => prev.map((p) => (p.id === editingPostId ? updated : p)));
        showToast('success', 'Post / Note updated successfully!');
      } else {
        const created = await api.createPost(payload);
        setPosts((prev) => [created, ...prev]);
        showToast('success', 'New Post / Note published successfully!');
      }

      resetPostForm();
      setActiveTab('posts');
      
      // Sync fresh post list from API
      if (currentUser?.id) {
        const postsData = await api.getPosts({ institution_id: currentUser.id });
        setPosts(postsData || []);
      }
    } catch (err: any) {
      console.error('Publish error:', err);
      const errMsg = err?.detail || err?.message || 'Operation failed. Please try again.';
      showToast('error', errMsg);
    } finally {
      setActionLoading(false);
    }
  };

  const confirmDeletePost = async () => {
    if (!deletingPostId) return;

    try {
      setActionLoading(true);
      await api.deletePost(deletingPostId);
      setPosts((prev) => prev.filter((p) => p.id !== deletingPostId));
      showToast('success', 'Post / Note deleted successfully!');
    } catch (err: any) {
      console.error('Error deleting post:', err);
      const errMsg = err?.detail || err?.message || 'Failed to delete post.';
      showToast('error', errMsg);
    } finally {
      setActionLoading(false);
      setDeletingPostId(null);
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profileName.trim()) {
      showToast('error', 'Please enter institution name');
      return;
    }

    try {
      setActionLoading(true);
      const payload = {
        name: profileName.trim(),
        about: profileAbout.trim(),
        contact_email: profileEmail.trim(),
        phone: profilePhone.trim(),
        website_url: profileWebsite.trim(),
      };

      if (profile) {
        const updated = await api.updateInstitution(profile.id, payload);
        setProfile(updated);
        showToast('success', 'Profile parameters saved successfully!');
      } else {
        showToast('error', 'Profile record not found. Please contact administrator.');
      }
    } catch (err: any) {
      console.error('Error saving profile:', err);
      showToast('error', err?.detail || 'Failed to save profile.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleLogout = () => {
    try {
      authLogout();
    } catch (err) {
      console.error('Logout error:', err);
    }
    localStorage.clear();
    sessionStorage.clear();
    navigate('/login', { replace: true });
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
      {/* Toast Feedback Notification */}
      {feedbackMsg && (
        <div
          className={`fixed top-5 right-5 z-50 px-5 py-3 rounded-2xl shadow-xl border text-xs font-bold transition-all duration-300 flex items-center gap-2 ${
            feedbackMsg.type === 'success'
              ? 'bg-emerald-950/90 text-emerald-300 border-emerald-500/40'
              : 'bg-rose-950/90 text-rose-300 border-rose-500/40'
          }`}
        >
          <span>{feedbackMsg.type === 'success' ? '✅' : '⚠️'}</span>
          <span>{feedbackMsg.text}</span>
        </div>
      )}

      {/* Sidebar Navigation */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 shrink-0 hidden md:block">
        <div className="p-6 h-full flex flex-col justify-between">
          <div className="space-y-8">
            <Link to="/" className="flex items-center gap-2 group">
              <div className="bg-white p-1 rounded-lg shadow-md shadow-rose-500/20 group-hover:scale-105 transition-transform">
                <img src="/logo.png" alt="ASSISI IFL Logo" className="h-10 w-auto object-contain" />
              </div>
              <span className="font-extrabold text-base tracking-tight bg-gradient-to-r from-white to-rose-300 bg-clip-text text-transparent">
                ASSISI IFL
              </span>
            </Link>

            <div className="space-y-1">
              <button
                onClick={() => {
                  resetPostForm();
                  setActiveTab('posts');
                }}
                className={`w-full text-left px-4 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider transition ${
                  activeTab === 'posts' ? 'bg-indigo-500/10 text-indigo-400' : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
                }`}
              >
                📋 Published Posts & Notes ({posts.length})
              </button>
              <button
                onClick={() => {
                  resetPostForm();
                  setActiveTab('new-post');
                }}
                className={`w-full text-left px-4 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider transition ${
                  activeTab === 'new-post' ? 'bg-indigo-500/10 text-indigo-400' : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
                }`}
              >
                ✍️ Write Post / Note
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
            <div className="bg-slate-955 border border-slate-800 p-4 rounded-xl space-y-1">
              <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Logged In Branch</p>
              <p className="text-xs font-bold text-emerald-400 truncate">{profile?.name || currentUser?.username}</p>
              <p className="text-[10px] text-slate-400 truncate">{profile?.location || 'Gurukula Campus'}</p>
            </div>
            <button
              onClick={handleLogout}
              className="w-full py-2.5 bg-rose-600/10 hover:bg-rose-600/25 border border-rose-600/20 rounded-xl text-rose-400 font-semibold text-xs transition uppercase tracking-wider cursor-pointer"
            >
              Sign Out
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 min-h-screen overflow-y-auto bg-slate-950 p-6 md:p-10 space-y-8">
        {/* Mobile Header */}
        <div className="md:hidden flex items-center justify-between border-b border-slate-800 pb-4">
          <Link to="/" className="flex items-center gap-1.5">
            <span className="text-lg">🏫</span>
            <span className="font-extrabold text-sm tracking-tight text-white">Assisi Social</span>
          </Link>
          <div className="flex gap-1.5">
            <button
              onClick={() => {
                resetPostForm();
                setActiveTab('posts');
              }}
              className={`px-2.5 py-1.5 rounded-lg text-[10px] font-bold uppercase ${
                activeTab === 'posts' ? 'bg-indigo-500 text-white' : 'bg-slate-900 text-slate-400'
              }`}
            >
              Feed ({posts.length})
            </button>
            <button
              onClick={() => {
                resetPostForm();
                setActiveTab('new-post');
              }}
              className={`px-2.5 py-1.5 rounded-lg text-[10px] font-bold uppercase ${
                activeTab === 'new-post' ? 'bg-indigo-500 text-white' : 'bg-slate-900 text-slate-400'
              }`}
            >
              Write
            </button>
            <button
              onClick={() => setActiveTab('profile')}
              className={`px-2.5 py-1.5 rounded-lg text-[10px] font-bold uppercase ${
                activeTab === 'profile' ? 'bg-indigo-500 text-white' : 'bg-slate-900 text-slate-400'
              }`}
            >
              Profile
            </button>
            <button onClick={handleLogout} className="px-2.5 py-1.5 rounded-lg bg-rose-500/20 text-rose-400 text-[10px] font-bold uppercase cursor-pointer">
              Out
            </button>
          </div>
        </div>

        {/* Section Title */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-extrabold tracking-tight text-white">
              {activeTab === 'posts' && '📋 Branch Feed, Notices & Notes Gallery'}
              {activeTab === 'new-post' && (editingPostId ? '✍️ Edit Published Post / Note' : '✍️ Create New Announcement or Note')}
              {activeTab === 'profile' && '🏛️ Branch Profile Settings'}
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              {activeTab === 'posts' && 'Manage, edit, and delete announcements, official notes, and events live on the platform.'}
              {activeTab === 'new-post' && 'Publish updates, news, official circular notes, and media for students and visitors.'}
              {activeTab === 'profile' && 'Configure branch display name, location, contacts, and description.'}
            </p>
          </div>

          {activeTab === 'posts' && (
            <button
              onClick={() => {
                resetPostForm();
                setActiveTab('new-post');
              }}
              className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold uppercase tracking-wider transition shadow-lg shadow-indigo-600/20 shrink-0 cursor-pointer"
            >
              + Create Post / Note
            </button>
          )}
        </div>

        {/* Tab 1: Posts & Notes Gallery */}
        {activeTab === 'posts' && (
          <div className="space-y-6">
            {posts.length === 0 ? (
              <div className="bg-slate-900/40 border border-dashed border-slate-800 rounded-3xl py-20 text-center text-slate-500">
                <span className="text-4xl">📝</span>
                <p className="mt-4 font-semibold text-sm text-slate-300">No published posts or notes yet for this branch.</p>
                <p className="text-xs text-slate-500 mt-1">Create your first update to share with students and the public.</p>
                <button
                  onClick={() => {
                    resetPostForm();
                    setActiveTab('new-post');
                  }}
                  className="mt-6 px-5 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider bg-indigo-600 hover:bg-indigo-500 text-white transition cursor-pointer"
                >
                  Create First Post / Note
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {posts.map((post) => (
                  <div key={post.id} className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden flex flex-col justify-between hover:border-slate-700 transition group">
                    <div>
                      {post.media_url ? (
                        <div className="aspect-video w-full relative overflow-hidden bg-slate-950">
                          {isVideoMedia(post.type, post.media_url) ? (
                            <video src={getMediaUrl(post.media_url)} controls className="w-full h-full object-cover" />
                          ) : post.type === 'pdf' || post.media_url.endsWith('.pdf') ? (
                            <div className="w-full h-full flex flex-col items-center justify-center bg-slate-950 p-4 text-center space-y-1">
                              <span className="text-3xl">📄</span>
                              <p className="text-xs font-bold text-indigo-400">PDF Document</p>
                            </div>
                          ) : (
                            <img src={getMediaUrl(post.media_url)} alt={post.title} className="w-full h-full object-cover group-hover:scale-105 transition duration-300" />
                          )}
                        </div>
                      ) : (
                        <div className="h-2 w-full bg-gradient-to-r from-indigo-500 to-purple-600"></div>
                      )}
                      
                      <div className="p-5 space-y-2.5">
                        <div className="flex justify-between items-center text-[10px] text-slate-400 uppercase tracking-widest font-bold">
                          <span className={`px-2 py-0.5 rounded-md ${
                            post.type === 'notice' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                            post.type === 'event' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' :
                            'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                          }`}>
                            {post.type === 'notice' ? '📌 Official Notice / Note' : post.type}
                          </span>
                          <span>{post.is_pinned ? '📌 Pinned' : ''}</span>
                        </div>

                        <h3 className="font-bold text-sm text-slate-100 line-clamp-2">{post.title}</h3>
                        <p className="text-xs text-slate-300 line-clamp-3 leading-relaxed whitespace-pre-line">{post.content}</p>
                        
                        {post.hashtags && (
                          <div className="flex flex-wrap gap-1 pt-1">
                            {post.hashtags.split(',').map((tag: string, idx: number) => (
                              <span key={idx} className="text-[10px] text-indigo-400 bg-indigo-950/60 px-2 py-0.5 rounded">
                                #{tag.trim()}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="p-4 bg-slate-950/60 border-t border-slate-800 flex gap-2">
                      <button
                        type="button"
                        disabled={actionLoading}
                        onClick={() => handleEditPostClick(post)}
                        className="flex-1 py-2 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 font-bold text-xs uppercase rounded-xl border border-indigo-500/30 transition flex items-center justify-center gap-1 cursor-pointer"
                      >
                        ✏️ Edit
                      </button>
                      <button
                        type="button"
                        disabled={actionLoading}
                        onClick={() => setDeletingPostId(post.id)}
                        className="flex-1 py-2 bg-rose-600/20 hover:bg-rose-600/40 text-rose-300 font-bold text-xs uppercase rounded-xl border border-rose-500/30 transition flex items-center justify-center gap-1 cursor-pointer"
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Create / Edit Form */}
        {activeTab === 'new-post' && (
          <form onSubmit={handlePublishOrUpdatePost} className="bg-slate-900 border border-slate-800 rounded-3xl p-6 md:p-8 space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <h3 className="text-lg font-bold text-white">
                {editingPostId ? '✏️ Modify Post / Note #' + editingPostId : '✍️ Write New Update'}
              </h3>
              {editingPostId && (
                <span className="text-xs bg-amber-500/20 text-amber-300 border border-amber-500/30 px-3 py-1 rounded-full font-bold uppercase">
                  Editing Mode Active
                </span>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Left Column */}
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-300">Title / Headline</label>
                  <input
                    type="text"
                    required
                    value={postTitle}
                    onChange={(e) => setPostTitle(e.target.value)}
                    placeholder="E.g. Notice regarding upcoming examination schedule"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-300">Type / Category</label>
                  <select
                    value={postType}
                    onChange={(e) => setPostType(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="notice">📌 Official Notice / Note</option>
                    <option value="video">🎥 Campus Video Reel (Instagram Shorts)</option>
                    <option value="news">📰 News Update</option>
                    <option value="event">🎉 Campus Event</option>
                    <option value="pdf">📄 PDF Document / Circular</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-300">Hashtags (Comma-separated)</label>
                  <input
                    type="text"
                    value={postHashtags}
                    onChange={(e) => setPostHashtags(e.target.value)}
                    placeholder="E.g. notice, exams, campus"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="flex items-center gap-3 pt-2">
                  <input
                    type="checkbox"
                    id="is_pinned"
                    checked={postIsPinned}
                    onChange={(e) => setPostIsPinned(e.target.checked)}
                    className="w-4 h-4 text-indigo-500 border-slate-800 bg-slate-950 rounded focus:ring-indigo-500/20 cursor-pointer"
                  />
                  <label htmlFor="is_pinned" className="text-xs font-semibold text-slate-300 cursor-pointer">
                    📌 Pin to top of Notice Board
                  </label>
                </div>
              </div>

              {/* Right Column */}
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-300">Media Content Upload</label>
                  
                  {postMediaUrl ? (
                    <div className="border border-slate-800 rounded-xl p-4 bg-slate-950 space-y-3">
                      <div className="flex justify-between items-center text-[10px] text-slate-500 uppercase tracking-widest font-bold">
                        <span>Attached Asset Preview</span>
                        <button
                          type="button"
                          onClick={() => setPostMediaUrl('')}
                          className="text-[10px] font-bold text-rose-400 uppercase tracking-wider hover:underline cursor-pointer"
                        >
                          Remove Attachment
                        </button>
                      </div>

                      <div className="max-h-48 w-full overflow-hidden rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center">
                        {isVideoMedia(postType, postMediaUrl) ? (
                          <video src={getMediaUrl(postMediaUrl)} controls className="max-h-48 w-full object-contain" />
                        ) : postMediaUrl.endsWith('.pdf') || postType === 'pdf' ? (
                          <div className="p-4 text-center">
                            <span className="text-3xl">📄</span>
                            <p className="text-xs text-indigo-400 font-bold mt-1">PDF File Attached</p>
                          </div>
                        ) : (
                          <img src={getMediaUrl(postMediaUrl)} alt="Preview" className="max-h-48 w-full object-contain" />
                        )}
                      </div>

                      <p className="text-xs truncate text-indigo-400 font-bold">{postMediaUrl}</p>
                    </div>
                  ) : (
                    <div className="border border-dashed border-slate-800 rounded-xl p-6 bg-slate-950 flex flex-col items-center justify-center text-center">
                      {mediaUploading ? (
                        <div className="space-y-2">
                          <Loading />
                          <p className="text-[10px] text-slate-400">Uploading media asset...</p>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          <span className="text-2xl">📁</span>
                          <p className="text-xs text-slate-400">Select images, MP4 videos, or PDF circulars</p>
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
                  <label className="text-xs font-bold text-slate-300">Content / Description Note</label>
                  <textarea
                    rows={5}
                    value={postContent}
                    onChange={(e) => setPostContent(e.target.value)}
                    placeholder="Write detailed instructions, notes, or announcement body..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500 resize-none font-sans"
                  />
                </div>
              </div>
            </div>

            <div className="border-t border-slate-800 pt-6 flex gap-3 justify-end">
              <button
                type="button"
                onClick={() => {
                  resetPostForm();
                  setActiveTab('posts');
                }}
                className="px-6 py-2.5 bg-slate-950 border border-slate-800 hover:bg-slate-800 rounded-xl text-xs font-bold uppercase transition text-slate-300 cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={actionLoading}
                className="px-6 py-2.5 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 rounded-xl text-xs font-bold text-white shadow-md shadow-indigo-500/20 transition uppercase tracking-wider cursor-pointer"
              >
                {actionLoading ? 'Saving...' : editingPostId ? 'Save Changes' : 'Publish Post / Note'}
              </button>
            </div>
          </form>
        )}

        {/* Tab 3: Profile Settings */}
        {activeTab === 'profile' && (
          <form onSubmit={handleSaveProfile} className="bg-slate-900 border border-slate-800 rounded-3xl p-6 md:p-8 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-300">Institution Branch Name</label>
                  <input
                    type="text"
                    required
                    value={profileName}
                    onChange={(e) => setProfileName(e.target.value)}
                    placeholder="E.g. Liebhaus Gurukula, Kidangoor"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-300">Contact Email</label>
                  <input
                    type="email"
                    value={profileEmail}
                    onChange={(e) => setProfileEmail(e.target.value)}
                    placeholder="E.g. contact@assisi.edu"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-300">Contact Telephone</label>
                  <input
                    type="text"
                    value={profilePhone}
                    onChange={(e) => setProfilePhone(e.target.value)}
                    placeholder="E.g. +91 94471 10001"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-300">Website URL</label>
                  <input
                    type="url"
                    value={profileWebsite}
                    onChange={(e) => setProfileWebsite(e.target.value)}
                    placeholder="E.g. https://liebhaus.assisi.edu"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-300">About / Campus Description</label>
                  <textarea
                    rows={8}
                    value={profileAbout}
                    onChange={(e) => setProfileAbout(e.target.value)}
                    placeholder="Describe your branch, achievements, values, and educational standard..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500 resize-none font-sans"
                  />
                </div>
              </div>
            </div>

            <div className="border-t border-slate-800 pt-6 flex justify-end">
              <button
                type="submit"
                disabled={actionLoading}
                className="px-6 py-2.5 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 rounded-xl text-xs font-bold text-white shadow-md shadow-indigo-500/20 transition uppercase tracking-wider cursor-pointer"
              >
                {actionLoading ? 'Saving...' : 'Save Profile Parameters'}
              </button>
            </div>
          </form>
        )}
      </main>

      {/* Edit Quick Modal Popup */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-lg w-full p-6 space-y-5 shadow-2xl">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h3 className="font-extrabold text-base text-white">✏️ Quick Edit Post / Note</h3>
              <button
                type="button"
                onClick={() => setShowEditModal(false)}
                className="text-slate-400 hover:text-white text-lg font-bold cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-bold text-slate-300 block mb-1">Title</label>
                <input
                  type="text"
                  value={postTitle}
                  onChange={(e) => setPostTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="font-bold text-slate-300 block mb-1">Category / Type</label>
                <select
                  value={postType}
                  onChange={(e) => setPostType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="notice">📌 Official Notice / Note</option>
                  <option value="news">📰 News Update</option>
                  <option value="event">🎉 Campus Event</option>
                  <option value="pdf">📄 PDF Circular</option>
                </select>
              </div>

              <div>
                <label className="font-bold text-slate-300 block mb-1">Content / Note Body</label>
                <textarea
                  rows={4}
                  value={postContent}
                  onChange={(e) => setPostContent(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500 resize-none font-sans"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="modal_pinned"
                  checked={postIsPinned}
                  onChange={(e) => setPostIsPinned(e.target.checked)}
                  className="w-4 h-4 text-indigo-500 border-slate-800 bg-slate-950 rounded cursor-pointer"
                />
                <label htmlFor="modal_pinned" className="font-semibold text-slate-300 cursor-pointer">
                  📌 Pinned Post / Note
                </label>
              </div>
            </div>

            <div className="flex gap-2 justify-end border-t border-slate-800 pt-4">
              <button
                type="button"
                onClick={() => setShowEditModal(false)}
                className="px-4 py-2 bg-slate-950 border border-slate-800 hover:bg-slate-800 text-slate-300 rounded-xl text-xs font-bold cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={actionLoading}
                onClick={handlePublishOrUpdatePost}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold uppercase tracking-wider cursor-pointer"
              >
                {actionLoading ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Custom Delete Confirmation Modal */}
      {deletingPostId !== null && (
        <div className="fixed inset-0 z-50 bg-slate-950/85 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-rose-500/30 rounded-3xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center gap-3 text-rose-400">
              <div className="w-10 h-10 rounded-2xl bg-rose-500/20 flex items-center justify-center text-xl shrink-0">
                🗑️
              </div>
              <div>
                <h3 className="font-extrabold text-base text-white">Delete Post / Note</h3>
                <p className="text-xs text-slate-400">Confirmation required</p>
              </div>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-4 rounded-2xl border border-slate-800">
              Are you sure you want to permanently delete this post / note (ID #{deletingPostId})? This action cannot be undone.
            </p>

            <div className="flex gap-3 justify-end border-t border-slate-800 pt-4">
              <button
                type="button"
                disabled={actionLoading}
                onClick={() => setDeletingPostId(null)}
                className="px-5 py-2.5 bg-slate-950 border border-slate-800 hover:bg-slate-800 text-slate-300 rounded-xl text-xs font-bold uppercase transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={actionLoading}
                onClick={confirmDeletePost}
                className="px-5 py-2.5 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-bold uppercase tracking-wider transition shadow-lg shadow-rose-600/20 cursor-pointer flex items-center gap-1.5"
              >
                {actionLoading ? 'Deleting...' : 'Yes, Delete Post'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
