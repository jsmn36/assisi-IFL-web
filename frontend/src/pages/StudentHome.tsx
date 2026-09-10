import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import StudentLayout from '@/components/StudentLayout';
import { useAuth } from '@/contexts/AuthContext';
import api from '@/lib/api';
import { 
  Heart, 
  MessageCircle, 
  Send, 
  Image as ImageIcon, 
  Plus, 
  Check, 
  Clock, 
  X,
  Volume2,
  ShieldAlert,
  ArrowRight,
  Building
} from 'lucide-react';
import { useToast } from '@/components/Toast';

interface StoryGroup {
  user_id: number;
  username: string;
  user_profile_pic: string | null;
  stories: any[];
}

export default function StudentHome() {
  const { user } = useAuth();
  const { showToast } = useToast();

  const [feed, setFeed] = useState<any[]>([]);
  const [stories, setStories] = useState<StoryGroup[]>([]);
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [announcements, setAnnouncements] = useState<any[]>([]);

  // Post creation fields
  const [newTitle, setNewTitle] = useState('');
  const [newContent, setNewContent] = useState('');
  const [newMediaUrl, setNewMediaUrl] = useState('');
  const [newHashtags, setNewHashtags] = useState('');
  const [submittingPost, setSubmittingPost] = useState(false);

  // Story creation
  const [storyMediaUrl, setStoryMediaUrl] = useState('');
  const [submittingStory, setSubmittingStory] = useState(false);
  const [showStoryModal, setShowStoryModal] = useState(false);

  // Active Story viewer modal
  const [activeStoryGroup, setActiveStoryGroup] = useState<StoryGroup | null>(null);
  const [activeStoryIndex, setActiveStoryIndex] = useState(0);

  // Post comments modal / drawer
  const [activePostComments, setActivePostComments] = useState<any | null>(null);
  const [commentsList, setCommentsList] = useState<any[]>([]);
  const [newCommentText, setNewCommentText] = useState('');

  const loadData = async () => {
    try {
      // 1. Load custom student feed
      const feedData = await api.getStudentFeed();
      setFeed(feedData);

      // 2. Load active stories
      const storyData = await api.getActiveStories();
      setStories(storyData);

      // 3. Load institutional announcements/pinned posts
      const publicPosts = await api.getPosts({ type: 'news', limit: 5 });
      setAnnouncements(publicPosts.filter(p => p.is_pinned));

      // 4. Load some suggested followers (students not followed yet)
      const searchRes = await api.searchSocial('');
      // Filter out self and followed
      const allUsers = searchRes.users || [];
      const following = await api.getFollowing(user?.id || 0);
      const followingIds = following.map(f => f.id);
      
      const filtered = allUsers.filter(
        (u: any) => u.id !== user?.id && !followingIds.includes(u.id)
      );
      setSuggestions(filtered.slice(0, 5));
    } catch (e) {
      console.error('Failed to load feed data', e);
    }
  };

  useEffect(() => {
    loadData();
  }, [user]);

  const handleCreatePost = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    setSubmittingPost(true);
    try {
      await api.createPost({
        title: newTitle,
        content: newContent,
        media_url: newMediaUrl || 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&q=80&w=800',
        type: 'image',
        hashtags: newHashtags
      });
      showToast('Post published successfully!', 'success');
      setNewTitle('');
      setNewContent('');
      setNewMediaUrl('');
      setNewHashtags('');
      loadData();
    } catch (err) {
      showToast('Failed to create post.', 'error');
    } finally {
      setSubmittingPost(false);
    }
  };

  const handleCreateStory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!storyMediaUrl.trim()) return;
    setSubmittingStory(true);
    try {
      await api.createStory({
        media_url: storyMediaUrl,
        type: 'image'
      });
      showToast('Story uploaded!', 'success');
      setStoryMediaUrl('');
      setShowStoryModal(false);
      loadData();
    } catch (err) {
      showToast('Failed to upload story.', 'error');
    } finally {
      setSubmittingStory(false);
    }
  };

  const handleToggleLike = async (postId: number) => {
    try {
      const res = await api.toggleLikePost(postId);
      setFeed(prev => 
        prev.map(post => 
          post.id === postId 
            ? { 
                ...post, 
                has_liked: res.liked, 
                likes_count: res.liked ? post.likes_count + 1 : post.likes_count - 1 
              } 
            : post
        )
      );
    } catch (err) {
      console.error(err);
    }
  };

  const handleOpenComments = async (post: any) => {
    setActivePostComments(post);
    try {
      const comments = await api.getPostComments(post.id);
      setCommentsList(comments);
    } catch (err) {
      console.error(err);
    }
  };

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCommentText.trim() || !activePostComments) return;
    try {
      const newComment = await api.commentOnPost(activePostComments.id, newCommentText);
      setCommentsList(prev => [...prev, newComment]);
      setNewCommentText('');
      
      // Update comment count on feed list
      setFeed(prev => 
        prev.map(post => 
          post.id === activePostComments.id 
            ? { ...post, comments_count: post.comments_count + 1 } 
            : post
        )
      );
    } catch (err) {
      showToast('Failed to add comment.', 'error');
    }
  };

  const handleFollowSuggestion = async (userId: number) => {
    try {
      await api.followUser(userId);
      showToast('Following user', 'success');
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <StudentLayout>
      <div className="max-w-6xl mx-auto px-4 py-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left column: Stories + Feed creator + Posts Feed */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Stories Bar */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 flex gap-4 overflow-x-auto items-center scrollbar-none shadow-sm">
            {/* Add Story Button */}
            <div className="flex flex-col items-center flex-shrink-0 cursor-pointer" onClick={() => setShowStoryModal(true)}>
              <div className="relative h-16 w-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center border border-dashed border-indigo-400 dark:border-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-950/20 transition-all">
                <Plus className="h-6 w-6 text-indigo-500" />
              </div>
              <span className="text-[11px] font-semibold text-slate-500 mt-1.5">Add Story</span>
            </div>

            {/* Stories Group list */}
            {stories.map((group) => (
              <div 
                key={group.user_id} 
                className="flex flex-col items-center flex-shrink-0 cursor-pointer"
                onClick={() => {
                  setActiveStoryGroup(group);
                  setActiveStoryIndex(0);
                }}
              >
                <div className="p-[2.5px] rounded-full bg-gradient-to-tr from-pink-500 via-purple-500 to-indigo-500 shadow-md">
                  <img
                    src={group.user_profile_pic || `https://api.dicebear.com/7.x/adventurer/svg?seed=${group.username}`}
                    alt={group.username}
                    className="h-14 w-14 rounded-full border-2 border-white dark:border-slate-900 bg-white"
                  />
                </div>
                <span className="text-[11px] font-semibold mt-1.5 truncate max-w-[70px]">
                  {group.username}
                </span>
              </div>
            ))}
          </div>

          {/* Create Post Card */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
            <h2 className="font-bold text-base mb-4 flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-indigo-500"></span>
              Create Post
            </h2>
            <form onSubmit={handleCreatePost} className="space-y-3.5">
              <input
                type="text"
                placeholder="Give your post a title..."
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 px-4 py-2.5 rounded-xl text-sm focus:outline-none focus:border-indigo-500 text-slate-800 dark:text-white"
                required
              />
              <textarea
                placeholder="What's on your mind? Share thoughts, updates, or campus activities..."
                rows={3}
                value={newContent}
                onChange={(e) => setNewContent(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 px-4 py-2.5 rounded-xl text-sm focus:outline-none focus:border-indigo-500 text-slate-800 dark:text-white resize-none"
              />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <input
                  type="text"
                  placeholder="Image/Video URL (e.g. from Unsplash)"
                  value={newMediaUrl}
                  onChange={(e) => setNewMediaUrl(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 px-4 py-2 rounded-xl text-xs focus:outline-none focus:border-indigo-500 text-slate-800 dark:text-white"
                />
                <input
                  type="text"
                  placeholder="Hashtags (comma separated: study, midterm)"
                  value={newHashtags}
                  onChange={(e) => setNewHashtags(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 px-4 py-2 rounded-xl text-xs focus:outline-none focus:border-indigo-500 text-slate-800 dark:text-white"
                />
              </div>
              <div className="flex justify-between items-center pt-2">
                <span className="text-[11px] text-slate-400 font-medium">
                  Posting as @{user?.username}
                </span>
                <button
                  type="submit"
                  disabled={submittingPost || !newTitle.trim()}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs px-5 py-2.5 rounded-xl shadow-md shadow-indigo-600/10 transition disabled:opacity-50"
                >
                  {submittingPost ? 'Publishing...' : 'Publish'}
                </button>
              </div>
            </form>
          </div>

          {/* Posts Feed */}
          <div className="space-y-6">
            {feed.length === 0 ? (
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-10 text-center text-slate-400">
                <Clock className="h-8 w-8 mx-auto mb-3 opacity-40 text-indigo-400" />
                <p className="font-semibold text-sm">Your feed is currently empty.</p>
                <p className="text-xs text-slate-500 mt-1">Follow other student accounts or check suggested list to see posts.</p>
              </div>
            ) : (
              feed.map((post) => (
                <div key={post.id} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm hover:shadow-md transition">
                  {/* Post Header */}
                  <div className="p-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <img
                        src={post.avatar_url || `https://api.dicebear.com/7.x/adventurer/svg?seed=${post.institution_name}`}
                        alt={post.institution_name}
                        className="h-9 w-9 rounded-full bg-slate-100 dark:bg-slate-800"
                      />
                      <div>
                        <h3 className="font-bold text-sm">{post.institution_name}</h3>
                        <p className="text-[10px] text-slate-400 dark:text-slate-500 font-medium">
                          {new Date(post.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Post Media */}
                  {post.media_url && (
                    <div className="aspect-[4/3] bg-slate-900 flex items-center justify-center overflow-hidden border-y border-slate-100 dark:border-slate-800/40">
                      <img
                        src={post.media_url}
                        alt="Post media"
                        className="w-full h-full object-cover"
                      />
                    </div>
                  )}

                  {/* Post Content */}
                  <div className="p-4 space-y-3">
                    <div>
                      <h4 className="font-extrabold text-base text-slate-900 dark:text-white leading-snug">
                        {post.title}
                      </h4>
                      {post.content && (
                        <p className="text-sm text-slate-600 dark:text-slate-300 mt-1.5 whitespace-pre-wrap leading-relaxed">
                          {post.content}
                        </p>
                      )}
                    </div>

                    {/* Hashtags */}
                    {post.hashtags && (
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {post.hashtags.split(',').map((tag: string) => (
                          <span key={tag} className="text-xs font-semibold text-indigo-600 dark:text-indigo-400">
                            #{tag.trim()}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Actions Bar */}
                    <div className="flex items-center gap-6 pt-3 border-t border-slate-100 dark:border-slate-800/60 mt-4">
                      <button
                        onClick={() => handleToggleLike(post.id)}
                        className={`flex items-center gap-2 text-xs font-semibold transition ${
                          post.has_liked 
                            ? 'text-rose-600' 
                            : 'text-slate-500 hover:text-rose-500'
                        }`}
                      >
                        <Heart className={`h-5 w-5 ${post.has_liked ? 'fill-rose-600' : ''}`} />
                        <span>{post.likes_count}</span>
                      </button>
                      <button
                        onClick={() => handleOpenComments(post)}
                        className="flex items-center gap-2 text-xs font-semibold text-slate-500 hover:text-indigo-500 transition"
                      >
                        <MessageCircle className="h-5 w-5" />
                        <span>{post.comments_count}</span>
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Suggested followers & Pinned campus notices */}
        <div className="space-y-6">
          {/* Suggested Followers */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
            <h2 className="font-bold text-sm mb-4 text-slate-500 uppercase tracking-wider text-[11px]">
              Suggested Accounts
            </h2>
            <div className="space-y-4">
              {suggestions.length === 0 ? (
                <p className="text-xs text-slate-400 italic">No new suggestions.</p>
              ) : (
                 suggestions.map((s) => (
                  <div key={s.id} className="flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800/40 p-1.5 -mx-1.5 rounded-xl transition">
                    <Link to={`/students/profile/${s.username}`} className="flex items-center gap-2.5 hover:opacity-80 transition overflow-hidden">
                      <img
                        src={s.profile_pic_url || `https://api.dicebear.com/7.x/adventurer/svg?seed=${s.username}`}
                        alt={s.username}
                        className="h-8.5 w-8.5 rounded-full bg-slate-100 dark:bg-slate-800 flex-shrink-0"
                      />
                      <div className="overflow-hidden max-w-[100px]">
                        <h4 className="font-bold text-xs truncate text-slate-900 dark:text-white">{s.name}</h4>
                        <p className="text-[10px] text-slate-400 dark:text-slate-500 truncate">@{s.username}</p>
                      </div>
                    </Link>
                    <button
                      onClick={() => handleFollowSuggestion(s.id)}
                      className="bg-indigo-600 hover:bg-indigo-500 text-white text-[10px] font-bold px-3 py-1.5 rounded-lg transition flex-shrink-0"
                    >
                      Follow
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Campus Pinned Notices */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
            <h2 className="font-bold text-sm mb-4 text-slate-500 uppercase tracking-wider text-[11px] flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-rose-500"></span>
              Campus Announcements
            </h2>
            <div className="space-y-4">
              {announcements.length === 0 ? (
                <p className="text-xs text-slate-400 italic">No pinned notices currently.</p>
              ) : (
                announcements.map((ann) => (
                  <div key={ann.id} className="border-b border-slate-100 dark:border-slate-800/40 pb-3 last:border-0 last:pb-0">
                    <span className="text-[9px] bg-rose-100 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 font-bold px-2 py-0.5 rounded-full uppercase">
                      Pinned
                    </span>
                    <h4 className="font-bold text-xs mt-1.5 text-slate-900 dark:text-white leading-tight">
                      {ann.title}
                    </h4>
                    <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                      {ann.content}
                    </p>
                    <span className="text-[9px] text-indigo-500 dark:text-indigo-400 font-semibold block mt-1.5">
                      by {ann.institution_name}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Super Admin Center Quick Access Card */}
          <div className="bg-gradient-to-b from-rose-950/30 via-slate-900 to-slate-900 border border-rose-500/30 rounded-2xl p-5 shadow-sm relative overflow-hidden group hover:border-rose-500/50 transition">
            <div className="flex items-center gap-2 mb-3">
              <div className="p-1.5 rounded-lg bg-rose-500/10 text-rose-400">
                <ShieldAlert className="h-5 w-5" />
              </div>
              <h2 className="font-extrabold text-sm text-white">Super Admin Center</h2>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed mb-4">
              Platform-wide control panel. Create new educational institutions, manage tenant databases, audit system activities, and review system-wide analytics.
            </p>
            <a
              href="http://localhost:3001"
              className="inline-flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-xl bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white font-extrabold text-xs shadow-lg shadow-rose-600/20 transition-all hover:scale-[1.02]"
            >
              <span>Enter Super Admin Panel</span>
              <ArrowRight className="h-4 w-4 transform group-hover:translate-x-1 transition-transform" />
            </a>
          </div>
        </div>
      </div>

      {/* Add Story Modal */}
      {showStoryModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-sm w-full p-5 shadow-2xl relative">
            <button 
              onClick={() => setShowStoryModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-200"
            >
              <X className="h-5 w-5" />
            </button>
            <h3 className="font-bold text-base mb-4">Post a Temporary Story</h3>
            <form onSubmit={handleCreateStory} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-500">Story Image URL</label>
                <input
                  type="text"
                  placeholder="https://images.unsplash.com/..."
                  value={storyMediaUrl}
                  onChange={(e) => setStoryMediaUrl(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 px-3 py-2 rounded-xl text-sm focus:outline-none text-slate-800 dark:text-white"
                  required
                />
              </div>
              <button
                type="submit"
                disabled={submittingStory || !storyMediaUrl.trim()}
                className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-2 rounded-xl transition"
              >
                {submittingStory ? 'Uploading...' : 'Upload Story'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Story Viewer Modal */}
      {activeStoryGroup && (
        <div className="fixed inset-0 bg-black/95 z-50 flex items-center justify-center">
          <button 
            onClick={() => setActiveStoryGroup(null)}
            className="absolute top-6 right-6 text-white hover:text-slate-300 z-50"
          >
            <X className="h-6 w-6" />
          </button>
          
          <div className="relative max-w-md w-full aspect-[9/16] bg-slate-950 flex flex-col justify-between p-4 overflow-hidden rounded-2xl shadow-2xl">
            {/* Header info */}
            <div className="absolute top-4 left-4 right-4 z-40 flex items-center gap-3">
              <img
                src={activeStoryGroup.user_profile_pic || `https://api.dicebear.com/7.x/adventurer/svg?seed=${activeStoryGroup.username}`}
                alt="Story Poster"
                className="h-9 w-9 rounded-full bg-slate-700 border-2 border-indigo-500"
              />
              <span className="text-sm font-bold text-white shadow-sm">
                {activeStoryGroup.username}
              </span>
            </div>

            {/* Main story media */}
            <div className="w-full h-full flex items-center justify-center bg-slate-950">
              <img
                src={activeStoryGroup.stories[activeStoryIndex]?.media_url}
                alt="Story content"
                className="w-full max-h-full object-contain"
              />
            </div>

            {/* Story Navigation Controls */}
            <div className="absolute inset-y-0 left-0 w-1/4 z-30 cursor-pointer" onClick={() => {
              if (activeStoryIndex > 0) {
                setActiveStoryIndex(prev => prev - 1);
              }
            }}></div>
            <div className="absolute inset-y-0 right-0 w-1/4 z-30 cursor-pointer" onClick={() => {
              if (activeStoryIndex < activeStoryGroup.stories.length - 1) {
                setActiveStoryIndex(prev => prev + 1);
              } else {
                setActiveStoryGroup(null); // end of stories
              }
            }}></div>
          </div>
        </div>
      )}

      {/* Post Comments Drawer/Modal */}
      {activePostComments && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-lg w-full h-[80vh] flex flex-col justify-between shadow-2xl relative">
            <button 
              onClick={() => setActivePostComments(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-200 z-10"
            >
              <X className="h-5 w-5" />
            </button>

            {/* Modal Header */}
            <div className="p-4 border-b border-slate-100 dark:border-slate-800">
              <h3 className="font-bold text-sm">Comments</h3>
              <p className="text-xs text-slate-400">Post by @{activePostComments.institution_name}</p>
            </div>

            {/* Comments List */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {commentsList.length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-10 italic">No comments yet. Be the first to say something!</p>
              ) : (
                commentsList.map((c) => (
                  <div key={c.id} className="flex gap-3">
                    <img
                      src={c.user_profile_pic || `https://api.dicebear.com/7.x/adventurer/svg?seed=${c.username}`}
                      alt={c.username}
                      className="h-8 w-8 rounded-full bg-slate-100 dark:bg-slate-800 flex-shrink-0"
                    />
                    <div className="bg-slate-50 dark:bg-slate-950 p-3 rounded-2xl flex-1 border border-slate-200/40 dark:border-slate-850">
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-bold text-xs text-slate-800 dark:text-slate-200">@{c.username}</span>
                        <span className="text-[9px] text-slate-400 font-semibold">{new Date(c.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                      </div>
                      <p className="text-xs text-slate-600 dark:text-slate-300 leading-normal">{c.content}</p>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Comment Form */}
            <form onSubmit={handleAddComment} className="p-4 border-t border-slate-100 dark:border-slate-800 flex gap-2.5 bg-slate-50 dark:bg-slate-950 rounded-b-2xl">
              <input
                type="text"
                placeholder="Write a comment..."
                value={newCommentText}
                onChange={(e) => setNewCommentText(e.target.value)}
                className="flex-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 px-4 py-2 rounded-xl text-xs focus:outline-none focus:border-indigo-500 text-slate-800 dark:text-white"
                required
              />
              <button
                type="submit"
                disabled={!newCommentText.trim()}
                className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold px-4 rounded-xl flex items-center justify-center transition"
              >
                <Send className="h-4 w-4" />
              </button>
            </form>
          </div>
        </div>
      )}
    </StudentLayout>
  );
}
