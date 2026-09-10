import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import StudentLayout from '@/components/StudentLayout';
import { useAuth } from '@/contexts/AuthContext';
import api from '@/lib/api';
import { 
  Edit2, 
  MapPin, 
  BookOpen, 
  Settings, 
  Grid, 
  Plus, 
  X,
  FileText,
  UserCheck
} from 'lucide-react';
import { useToast } from '@/components/Toast';

export default function StudentProfilePage() {
  const { username } = useParams<{ username: string }>();
  const { user: currentUser } = useAuth();
  const { showToast } = useToast();

  const [profile, setProfile] = useState<any | null>(null);
  const [highlights, setHighlights] = useState<any[]>([]);
  const [posts, setPosts] = useState<any[]>([]);
  const [followers, setFollowers] = useState<any[]>([]);
  const [following, setFollowing] = useState<any[]>([]);
  const [isFollowing, setIsFollowing] = useState(false);

  // Modals state
  const [showEditModal, setShowEditModal] = useState(false);
  const [showHighlightModal, setShowHighlightModal] = useState(false);
  const [showFollowersModal, setShowFollowersModal] = useState(false);
  const [showFollowingModal, setShowFollowingModal] = useState(false);

  // Edit fields
  const [editBio, setEditBio] = useState('');
  const [editClass, setEditClass] = useState('');
  const [editProfilePic, setEditProfilePic] = useState('');
  const [editCoverPhoto, setEditCoverPhoto] = useState('');
  const [savingProfile, setSavingProfile] = useState(false);

  // Create Highlight fields
  const [highlightName, setHighlightName] = useState('');
  const [highlightCover, setHighlightCover] = useState('');
  const [availableStories, setAvailableStories] = useState<any[]>([]);
  const [selectedStoryIds, setSelectedStoryIds] = useState<number[]>([]);
  const [savingHighlight, setSavingHighlight] = useState(false);

  // Active Highlight viewer
  const [activeHighlight, setActiveHighlight] = useState<any | null>(null);
  const [activeStoryIndex, setActiveStoryIndex] = useState(0);

  const isOwnProfile = currentUser?.username === username;

  const loadProfileData = async () => {
    try {
      const uName = username || currentUser?.username;
      if (!uName) return;

      // 1. Get profile details
      const profileData = await api.getStudentProfile(uName);
      setProfile(profileData);

      // Populate edit fields
      setEditBio(profileData.bio || '');
      setEditClass(profileData.class_or_department || '');
      setEditProfilePic(profileData.profile_pic_url || '');
      setEditCoverPhoto(profileData.cover_photo_url || '');

      // 2. Load highlights
      const hData = await api.getHighlights(profileData.user_id);
      setHighlights(hData);

      // 3. Load user posts
      const allPosts = await api.getPosts({ institution_id: profileData.user_id });
      setPosts(allPosts);

      // 4. Load followers & following
      const followersList = await api.getFollowers(profileData.user_id);
      setFollowers(followersList);
      const followingList = await api.getFollowing(profileData.user_id);
      setFollowing(followingList);

      // Check if current user is following this profile
      if (currentUser) {
        setIsFollowing(followersList.some((f: any) => f.id === currentUser.id));
      }
    } catch (e) {
      console.error(e);
      showToast('Failed to load profile.', 'error');
    }
  };

  useEffect(() => {
    loadProfileData();
  }, [username, currentUser]);

  const handleFollowToggle = async () => {
    if (!profile) return;
    try {
      if (isFollowing) {
        await api.unfollowUser(profile.user_id);
        setIsFollowing(false);
        showToast('Unfollowed user', 'success');
      } else {
        await api.followUser(profile.user_id);
        setIsFollowing(true);
        showToast('Following user', 'success');
      }
      loadProfileData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    try {
      await api.updateStudentProfile({
        bio: editBio,
        class_or_department: editClass,
        profile_pic_url: editProfilePic,
        cover_photo_url: editCoverPhoto
      });
      showToast('Profile updated!', 'success');
      setShowEditModal(false);
      loadProfileData();
    } catch (err) {
      showToast('Failed to update profile.', 'error');
    } finally {
      setSavingProfile(false);
    }
  };

  const handleOpenHighlightModal = async () => {
    setShowHighlightModal(true);
    try {
      // Fetch active stories to build highlight from
      const activeStories = await api.getActiveStories();
      // Find own stories
      const ownStories = activeStories.find(g => g.user_id === currentUser?.id);
      setAvailableStories(ownStories?.stories || []);
    } catch (err) {
      console.error(err);
    }
  };

  const handleToggleStorySelection = (storyId: number) => {
    setSelectedStoryIds(prev => 
      prev.includes(storyId) 
        ? prev.filter(id => id !== storyId) 
        : [...prev, storyId]
    );
  };

  const handleCreateHighlight = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!highlightName.trim()) return;
    setSavingHighlight(true);
    try {
      await api.createHighlight({
        name: highlightName,
        cover_url: highlightCover || 'https://images.unsplash.com/photo-1518156677180-95a2893f3e9f?auto=format&fit=crop&q=80&w=200',
        story_ids: selectedStoryIds
      });
      showToast('Highlight created successfully!', 'success');
      setHighlightName('');
      setHighlightCover('');
      setSelectedStoryIds([]);
      setShowHighlightModal(false);
      loadProfileData();
    } catch (err) {
      showToast('Failed to create highlight.', 'error');
    } finally {
      setSavingHighlight(false);
    }
  };

  if (!profile) {
    return (
      <StudentLayout>
        <div className="flex items-center justify-center h-[50vh] text-slate-400">
          Loading student profile...
        </div>
      </StudentLayout>
    );
  }

  return (
    <StudentLayout>
      <div className="bg-slate-50 dark:bg-slate-950 min-h-screen">
        
        {/* Cover Photo */}
        <div className="h-64 md:h-80 w-full relative bg-indigo-900 overflow-hidden border-b border-slate-200 dark:border-slate-800">
          <img
            src={profile.cover_photo_url || 'https://images.unsplash.com/photo-1507842217343-583bb7270b66?auto=format&fit=crop&q=80&w=1200'}
            alt="Cover"
            className="w-full h-full object-cover"
          />
        </div>

        {/* Profile Details Header */}
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 -mt-20 relative z-10 pb-8">
          <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 md:p-8 shadow-md">
            <div className="flex flex-col md:flex-row items-center md:items-start justify-between gap-6">
              
              {/* Avatar + Basic details */}
              <div className="flex flex-col md:flex-row items-center gap-5 text-center md:text-left">
                <img
                  src={profile.profile_pic_url || `https://api.dicebear.com/7.x/adventurer/svg?seed=${profile.username}`}
                  alt={profile.username}
                  className="h-28 w-28 rounded-full border-4 border-white dark:border-slate-900 shadow-lg bg-white bg-slate-100 dark:bg-slate-800"
                />
                <div className="space-y-1">
                  <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">
                    {profile.student_name}
                  </h1>
                  <p className="text-sm font-semibold text-indigo-600 dark:text-indigo-400">
                    @{profile.username}
                  </p>
                  
                  <div className="flex flex-wrap items-center justify-center md:justify-start gap-4 text-xs font-semibold text-slate-400 mt-2.5">
                    <div className="flex items-center gap-1.5">
                      <BookOpen className="h-4 w-4 text-slate-500" />
                      <span>{profile.class_or_department || 'General Department'}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <FileText className="h-4 w-4 text-slate-500" />
                      <span>Admission: {profile.admission_number}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Buttons (Edit Profile or Follow/Chat) */}
              <div className="flex gap-2">
                {isOwnProfile ? (
                  <button
                    onClick={() => setShowEditModal(true)}
                    className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-800 dark:text-white font-bold text-xs px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 transition"
                  >
                    <Edit2 className="h-4 w-4" />
                    Edit Profile
                  </button>
                ) : (
                  <>
                    <button
                      onClick={handleFollowToggle}
                      className={`flex items-center gap-2 font-bold text-xs px-5 py-2.5 rounded-xl transition ${
                        isFollowing 
                          ? 'bg-slate-200 dark:bg-slate-800 text-slate-800 dark:text-white'
                          : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/10'
                      }`}
                    >
                      {isFollowing ? (
                        <>
                          <UserCheck className="h-4 w-4" />
                          Following
                        </>
                      ) : (
                        'Follow'
                      )}
                    </button>
                    <Link
                      to={`/chat?userId=${profile.user_id}&username=${profile.username}&name=${encodeURIComponent(profile.student_name)}&avatar=${encodeURIComponent(profile.profile_pic_url || '')}`}
                      className="bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-800 dark:text-white font-bold text-xs px-5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 transition"
                    >
                      Message
                    </Link>
                  </>
                )}
              </div>
            </div>

            {/* Bio description */}
            <div className="mt-6 pt-6 border-t border-slate-150 dark:border-slate-800/60">
              <h3 className="font-bold text-xs text-slate-400 uppercase tracking-wider mb-2">About me</h3>
              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed max-w-2xl whitespace-pre-wrap">
                {profile.bio || 'This student has not shared a bio yet.'}
              </p>
            </div>

            {/* Counts (Followers, Following, Posts) */}
            <div className="flex gap-8 mt-6 pt-6 border-t border-slate-150 dark:border-slate-800/60 text-center md:text-left">
              <div className="cursor-pointer" onClick={() => setShowFollowersModal(true)}>
                <p className="text-xl font-extrabold">{followers.length}</p>
                <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Followers</p>
              </div>
              <div className="cursor-pointer" onClick={() => setShowFollowingModal(true)}>
                <p className="text-xl font-extrabold">{following.length}</p>
                <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Following</p>
              </div>
              <div>
                <p className="text-xl font-extrabold">{posts.length}</p>
                <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Posts</p>
              </div>
            </div>
          </div>

          {/* Highlights Section */}
          <div className="mt-8 space-y-4">
            <h2 className="font-extrabold text-base flex items-center gap-2">
              <span className="h-2.5 w-2.5 bg-indigo-500 rounded-full"></span>
              Highlights
            </h2>
            <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-none">
              {isOwnProfile && (
                <div 
                  onClick={handleOpenHighlightModal}
                  className="flex flex-col items-center flex-shrink-0 cursor-pointer"
                >
                  <div className="h-16 w-16 bg-slate-100 dark:bg-slate-900 border border-dashed border-indigo-400 dark:border-indigo-600 rounded-full flex items-center justify-center hover:bg-indigo-50 dark:hover:bg-indigo-950/20 transition-all shadow-sm">
                    <Plus className="h-5 w-5 text-indigo-500" />
                  </div>
                  <span className="text-[10px] font-bold text-slate-500 mt-2">New</span>
                </div>
              )}

              {highlights.map((h) => (
                <div 
                  key={h.id}
                  onClick={() => {
                    setActiveHighlight(h);
                    setActiveStoryIndex(0);
                  }}
                  className="flex flex-col items-center flex-shrink-0 cursor-pointer animate-fade-in"
                >
                  <img
                    src={h.cover_url || 'https://images.unsplash.com/photo-1518156677180-95a2893f3e9f?auto=format&fit=crop&q=80&w=200'}
                    alt={h.name}
                    className="h-16 w-16 rounded-full border border-indigo-200 dark:border-slate-800 object-cover shadow-sm bg-white"
                  />
                  <span className="text-[10px] font-bold text-slate-500 dark:text-slate-400 mt-2 truncate max-w-[70px]">
                    {h.name}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Posts Feed Grid */}
          <div className="mt-8 space-y-4">
            <h2 className="font-extrabold text-base flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
              <Grid className="h-4.5 w-4.5 text-indigo-500" />
              Student Posts
            </h2>

            {posts.length === 0 ? (
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-10 text-center text-slate-400">
                <p className="font-semibold text-sm">No posts published yet.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {posts.map((post) => (
                  <div key={post.id} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
                    {post.media_url && (
                      <div className="aspect-[4/3] w-full bg-slate-950 flex items-center justify-center overflow-hidden">
                        <img
                          src={post.media_url}
                          alt={post.title}
                          className="w-full h-full object-cover"
                        />
                      </div>
                    )}
                    <div className="p-4 space-y-1.5">
                      <h4 className="font-bold text-sm">{post.title}</h4>
                      {post.content && (
                        <p className="text-xs text-slate-500 line-clamp-3 leading-relaxed">{post.content}</p>
                      )}
                      <p className="text-[9px] text-slate-400 font-semibold">{new Date(post.created_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Edit Profile Modal */}
        {showEditModal && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl relative">
              <button 
                onClick={() => setShowEditModal(false)}
                className="absolute top-4 right-4 text-slate-400 hover:text-slate-200"
              >
                <X className="h-5 w-5" />
              </button>
              <h3 className="font-bold text-base mb-4">Edit Student Profile</h3>
              <form onSubmit={handleUpdateProfile} className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-500">Bio Description</label>
                  <textarea
                    rows={3}
                    value={editBio}
                    onChange={(e) => setEditBio(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 px-3 py-2 rounded-xl text-sm focus:outline-none text-slate-850 dark:text-white"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-500">Class or Department</label>
                  <input
                    type="text"
                    value={editClass}
                    onChange={(e) => setEditClass(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 px-3 py-2 rounded-xl text-sm focus:outline-none text-slate-850 dark:text-white"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-500">Avatar Image URL</label>
                  <input
                    type="text"
                    value={editProfilePic}
                    onChange={(e) => setEditProfilePic(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 px-3 py-2 rounded-xl text-sm focus:outline-none text-slate-850 dark:text-white"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-500">Cover Photo URL</label>
                  <input
                    type="text"
                    value={editCoverPhoto}
                    onChange={(e) => setEditCoverPhoto(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 px-3 py-2 rounded-xl text-sm focus:outline-none text-slate-850 dark:text-white"
                  />
                </div>
                <button
                  type="submit"
                  disabled={savingProfile}
                  className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-2.5 rounded-xl transition"
                >
                  {savingProfile ? 'Saving Changes...' : 'Save Settings'}
                </button>
              </form>
            </div>
          </div>
        )}

        {/* Create Highlight Modal */}
        {showHighlightModal && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl relative max-h-[85vh] flex flex-col justify-between">
              <button 
                onClick={() => setShowHighlightModal(false)}
                className="absolute top-4 right-4 text-slate-400 hover:text-slate-200"
              >
                <X className="h-5 w-5" />
              </button>
              
              <div className="flex-1 overflow-y-auto">
                <h3 className="font-bold text-base mb-4">Create Highlight</h3>
                <form onSubmit={handleCreateHighlight} className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-500">Highlight Name *</label>
                    <input
                      type="text"
                      placeholder="e.g. Memories"
                      value={highlightName}
                      onChange={(e) => setHighlightName(e.target.value)}
                      className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 px-3 py-2 rounded-xl text-sm focus:outline-none text-slate-850 dark:text-white"
                      required
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-500">Cover Photo URL</label>
                    <input
                      type="text"
                      placeholder="https://images.unsplash.com/..."
                      value={highlightCover}
                      onChange={(e) => setHighlightCover(e.target.value)}
                      className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 px-3 py-2 rounded-xl text-sm focus:outline-none text-slate-850 dark:text-white"
                    />
                  </div>

                  {/* Available stories to select */}
                  <div className="space-y-2.5 pt-2">
                    <label className="text-xs font-semibold text-slate-550 block">Select Active Stories to Add</label>
                    {availableStories.length === 0 ? (
                      <p className="text-xs text-slate-400 italic">No active stories in the last 24h to select from.</p>
                    ) : (
                      <div className="grid grid-cols-3 gap-2">
                        {availableStories.map((story) => {
                          const isSelected = selectedStoryIds.includes(story.id);
                          return (
                            <div 
                              key={story.id}
                              onClick={() => handleToggleStorySelection(story.id)}
                              className={`aspect-[9/16] rounded-xl overflow-hidden relative cursor-pointer border-2 transition ${
                                isSelected ? 'border-indigo-500' : 'border-transparent opacity-60'
                              }`}
                            >
                              <img src={story.media_url} className="w-full h-full object-cover" />
                              {isSelected && (
                                <div className="absolute top-1 right-1 bg-indigo-600 rounded-full p-0.5 text-white">
                                  <Plus className="h-3 w-3 rotate-45" />
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>

                  <button
                    type="submit"
                    disabled={savingHighlight || !highlightName.trim()}
                    className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-2.5 rounded-xl transition mt-4"
                  >
                    {savingHighlight ? 'Creating Highlight...' : 'Create'}
                  </button>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* Highlight Story Viewer Modal */}
        {activeHighlight && (
          <div className="fixed inset-0 bg-black/95 z-50 flex items-center justify-center">
            <button 
              onClick={() => setActiveHighlight(null)}
              className="absolute top-6 right-6 text-white hover:text-slate-300 z-50"
            >
              <X className="h-6 w-6" />
            </button>
            
            <div className="relative max-w-md w-full aspect-[9/16] bg-slate-950 flex flex-col justify-between p-4 overflow-hidden rounded-2xl shadow-2xl">
              {/* Header info */}
              <div className="absolute top-4 left-4 right-4 z-40 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <img
                    src={profile.profile_pic_url || `https://api.dicebear.com/7.x/adventurer/svg?seed=${profile.username}`}
                    alt="Highlight Creator"
                    className="h-9 w-9 rounded-full bg-slate-700 border-2 border-indigo-500"
                  />
                  <div>
                    <span className="text-sm font-bold text-white block leading-none">{profile.student_name}</span>
                    <span className="text-[10px] text-indigo-400 font-bold uppercase tracking-wider">{activeHighlight.name}</span>
                  </div>
                </div>
              </div>

              {/* Main story media */}
              <div className="w-full h-full flex items-center justify-center bg-slate-950">
                {activeHighlight.stories.length > 0 ? (
                  <img
                    src={activeHighlight.stories[activeStoryIndex]?.media_url}
                    alt="Highlight Story content"
                    className="w-full max-h-full object-contain"
                  />
                ) : (
                  <div className="text-slate-400 text-sm">No stories in this highlight.</div>
                )}
              </div>

              {/* Navigation Controls */}
              {activeHighlight.stories.length > 1 && (
                <>
                  <div className="absolute inset-y-0 left-0 w-1/4 z-30 cursor-pointer" onClick={() => {
                    if (activeStoryIndex > 0) {
                      setActiveStoryIndex(prev => prev - 1);
                    }
                  }}></div>
                  <div className="absolute inset-y-0 right-0 w-1/4 z-30 cursor-pointer" onClick={() => {
                    if (activeStoryIndex < activeHighlight.stories.length - 1) {
                      setActiveStoryIndex(prev => prev + 1);
                    } else {
                      setActiveHighlight(null); // end
                    }
                  }}></div>
                </>
              )}
            </div>
          </div>
        )}

        {/* Followers List Modal */}
        {showFollowersModal && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-sm w-full p-5 shadow-2xl relative">
              <button 
                onClick={() => setShowFollowersModal(false)}
                className="absolute top-4 right-4 text-slate-400 hover:text-slate-200"
              >
                <X className="h-5 w-5" />
              </button>
              <h3 className="font-bold text-sm mb-4">Followers</h3>
              <div className="space-y-4 max-h-[50vh] overflow-y-auto">
                {followers.length === 0 ? (
                  <p className="text-xs text-slate-400 italic text-center py-4">No followers yet.</p>
                ) : (
                  followers.map((f) => (
                    <div key={f.id} className="flex items-center gap-3">
                      <img src={f.profile_pic_url || `https://api.dicebear.com/7.x/adventurer/svg?seed=${f.username}`} className="h-9 w-9 rounded-full bg-slate-100 dark:bg-slate-800" />
                      <div>
                        <h4 className="font-bold text-xs">{f.name}</h4>
                        <p className="text-[10px] text-slate-400">@{f.username}</p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* Following List Modal */}
        {showFollowingModal && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-sm w-full p-5 shadow-2xl relative">
              <button 
                onClick={() => setShowFollowingModal(false)}
                className="absolute top-4 right-4 text-slate-400 hover:text-slate-200"
              >
                <X className="h-5 w-5" />
              </button>
              <h3 className="font-bold text-sm mb-4">Following</h3>
              <div className="space-y-4 max-h-[50vh] overflow-y-auto">
                {following.length === 0 ? (
                  <p className="text-xs text-slate-400 italic text-center py-4">Not following anyone yet.</p>
                ) : (
                  following.map((f) => (
                    <div key={f.id} className="flex items-center gap-3">
                      <img src={f.profile_pic_url || `https://api.dicebear.com/7.x/adventurer/svg?seed=${f.username}`} className="h-9 w-9 rounded-full bg-slate-100 dark:bg-slate-800" />
                      <div>
                        <h4 className="font-bold text-xs">{f.name}</h4>
                        <p className="text-[10px] text-slate-400">@{f.username}</p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

      </div>
    </StudentLayout>
  );
}
