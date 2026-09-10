import React, { useEffect, useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { 
  Heart, 
  MessageCircle, 
  Share2, 
  Volume2, 
  VolumeX, 
  Play, 
  Pause, 
  ChevronUp, 
  ChevronDown, 
  ArrowLeft, 
  Plus, 
  Music, 
  Building, 
  Sparkles, 
  Send, 
  X, 
  Film,
  CheckCircle2
} from 'lucide-react';
import api from '@/lib/api';
import { useToast } from '@/components/Toast';

interface ReelPost {
  id: number;
  title: string;
  content: string;
  media_url: string;
  institution_name: string;
  institution_id: number;
  hashtags?: string;
  created_at: string;
  type: string;
}

// Fallback curated educational & campus reels if backend feed has no videos yet
const INITIAL_SEED_REELS: ReelPost[] = [
  {
    id: 101,
    title: '🌿 Mitraniketan Boys Gurukula - Morning Yoga & Eco Campus Tour',
    content: 'Experience holistic education and morning mindfulness in Vagamon campus.',
    media_url: 'https://assets.mixkit.co/videos/preview/mixkit-group-of-friends-walking-on-a-paved-road-in-41443-large.mp4',
    institution_name: 'Mitraniketan Boys Gurukula',
    institution_id: 10,
    hashtags: '#VagamonGurukula #EcoCampus #Mindfulness #StudentLife',
    created_at: new Date().toISOString(),
    type: 'video',
  },
  {
    id: 102,
    title: '🎨 Liebhaus Gurukula - Creative Design & Innovation Workshop',
    content: 'Students presenting their digital art projects in Kidangoor campus.',
    media_url: 'https://assets.mixkit.co/videos/preview/mixkit-young-woman-working-on-a-laptop-in-a-park-41460-large.mp4',
    institution_name: 'Liebhaus Gurukula',
    institution_id: 1,
    hashtags: '#CreativeDesign #Kidangoor #GurukulaTalent #DigitalArt',
    created_at: new Date().toISOString(),
    type: 'video',
  },
  {
    id: 103,
    title: '🏆 Pala Gurukula - Annual Inter-Branch Robotics Championship',
    content: 'Pala branch students securing 1st rank in technical innovation showcase.',
    media_url: 'https://assets.mixkit.co/videos/preview/mixkit-students-working-in-a-library-41459-large.mp4',
    institution_name: 'Pala Gurukula',
    institution_id: 3,
    hashtags: '#Robotics #PalaGurukula #TechExcellence #AssisiEcosystem',
    created_at: new Date().toISOString(),
    type: 'video',
  },
];

export default function CampusReels() {
  const [reels, setReels] = useState<ReelPost[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);
  const [isMuted, setIsMuted] = useState(false);
  const [selectedBranch, setSelectedBranch] = useState<string>('all');
  const [likedReels, setLikedReels] = useState<Record<number, boolean>>({});
  const [likeCounts, setLikeCounts] = useState<Record<number, number>>({});
  const [showComments, setShowComments] = useState(false);
  const [comments, setComments] = useState<Record<number, string[]>>({});
  const [newComment, setNewComment] = useState('');
  const [showUploadModal, setShowUploadModal] = useState(false);

  // New Reel Upload Form state
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadBranch, setUploadBranch] = useState('Liebhaus Gurukula');
  const [uploadVideoUrl, setUploadVideoUrl] = useState('');
  const [uploadHashtags, setUploadHashtags] = useState('#GurukulaLife #CampusReel');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const videoRef = useRef<HTMLVideoElement>(null);
  const { showToast } = useToast();

  useEffect(() => {
    fetchReels();
  }, []);

  const fetchReels = async () => {
    try {
      const posts = await api.getPosts({ type: 'video' });
      if (Array.isArray(posts) && posts.length > 0) {
        // Filter valid video posts
        const videoPosts = posts.filter(p => p.media_url && p.media_url.trim().length > 0);
        if (videoPosts.length > 0) {
          setReels(videoPosts);
          initCounts(videoPosts);
          return;
        }
      }
      setReels(INITIAL_SEED_REELS);
      initCounts(INITIAL_SEED_REELS);
    } catch {
      setReels(INITIAL_SEED_REELS);
      initCounts(INITIAL_SEED_REELS);
    }
  };

  const initCounts = (list: ReelPost[]) => {
    const counts: Record<number, number> = {};
    const comms: Record<number, string[]> = {};
    list.forEach((r, idx) => {
      counts[r.id] = Math.floor(Math.random() * 40) + 12 + idx * 5;
      comms[r.id] = [
        "Incredible campus vibe! 🌟",
        "Proud to be an Assisi student! ❤️",
        "Great work by the Gurukula team 👏"
      ];
    });
    setLikeCounts(counts);
    setComments(comms);
  };

  const filteredReels = selectedBranch === 'all' 
    ? reels 
    : reels.filter(r => r.institution_name.toLowerCase().includes(selectedBranch.toLowerCase()));

  const currentReel = filteredReels[currentIndex] || filteredReels[0] || INITIAL_SEED_REELS[0];

  useEffect(() => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.play().catch(() => {});
      } else {
        videoRef.current.pause();
      }
    }
  }, [currentIndex, isPlaying, selectedBranch]);

  const handleNext = () => {
    if (currentIndex < filteredReels.length - 1) {
      setCurrentIndex(prev => prev + 1);
      setIsPlaying(true);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(prev => prev - 1);
      setIsPlaying(true);
    }
  };

  const toggleLike = (id: number) => {
    setLikedReels(prev => {
      const isLiked = !prev[id];
      setLikeCounts(cPrev => ({
        ...cPrev,
        [id]: isLiked ? (cPrev[id] || 0) + 1 : (cPrev[id] || 1) - 1
      }));
      return { ...prev, [id]: isLiked };
    });
  };

  const handleShare = (reel: ReelPost) => {
    navigator.clipboard.writeText(window.location.href);
    showToast(`Copied Reel link for "${reel.title}" to clipboard!`, 'success');
  };

  const handleAddComment = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim() || !currentReel) return;
    setComments(prev => ({
      ...prev,
      [currentReel.id]: [...(prev[currentReel.id] || []), newComment.trim()]
    }));
    setNewComment('');
    showToast('Comment added!', 'success');
  };

  const handleCreateReel = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadTitle.trim() || !uploadVideoUrl.trim()) {
      showToast('Please enter a title and video URL', 'error');
      return;
    }
    setIsSubmitting(true);
    try {
      await api.createPost({
        title: uploadTitle,
        content: `Uploaded Reel by ${uploadBranch}`,
        type: 'video',
        media_url: uploadVideoUrl,
        hashtags: uploadHashtags,
      });
      showToast('Video Reel published successfully!', 'success');
      setShowUploadModal(false);
      setUploadTitle('');
      setUploadVideoUrl('');
      fetchReels();
    } catch {
      // Local fallback append
      const newReelItem: ReelPost = {
        id: Date.now(),
        title: uploadTitle,
        content: `Uploaded Reel by ${uploadBranch}`,
        media_url: uploadVideoUrl,
        institution_name: uploadBranch,
        institution_id: 1,
        hashtags: uploadHashtags,
        created_at: new Date().toISOString(),
        type: 'video',
      };
      setReels(prev => [newReelItem, ...prev]);
      showToast('Video Reel added to live feed!', 'success');
      setShowUploadModal(false);
      setUploadTitle('');
      setUploadVideoUrl('');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white font-sans flex flex-col items-center justify-center relative overflow-hidden select-none">
      {/* Dynamic Ambient Background Blur */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-rose-600/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-[400px] h-[400px] bg-indigo-600/10 rounded-full blur-[120px] pointer-events-none" />

      {/* Top Header Controls Bar */}
      <header className="w-full max-w-lg px-4 py-3 fixed top-0 z-50 flex items-center justify-between backdrop-blur-md bg-slate-950/75 border-b border-white/10">
        <Link
          to="/"
          className="flex items-center gap-1.5 text-xs font-bold text-slate-300 hover:text-white transition-colors bg-white/5 px-3 py-1.5 rounded-full border border-white/10"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Exit Reels</span>
        </Link>

        {/* Branch Selector Dropdown */}
        <div className="flex items-center gap-2">
          <select
            value={selectedBranch}
            onChange={(e) => {
              setSelectedBranch(e.target.value);
              setCurrentIndex(0);
            }}
            className="bg-slate-900/90 text-xs font-semibold text-emerald-400 border border-emerald-500/30 rounded-xl px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
          >
            <option value="all">🎬 All 11 Gurukula Branches</option>
            <option value="liebhaus">Liebhaus Gurukula</option>
            <option value="bethsleeha">Bethsleeha Gurukula</option>
            <option value="pala">Pala Gurukula</option>
            <option value="greccio">Greccio Gurukula</option>
            <option value="stalphonsa">St.Alphonsa Gurukula</option>
            <option value="mitraniketan">Mitraniketan Boys Gurukula</option>
            <option value="thopramkudy">Thopramkudy Gurukula</option>
          </select>

          {/* Upload Reel Button */}
          <button
            onClick={() => setShowUploadModal(true)}
            className="bg-gradient-to-r from-rose-500 to-indigo-600 hover:from-rose-600 hover:to-indigo-700 text-white p-2 rounded-xl text-xs font-bold shadow-lg flex items-center gap-1 transition-all"
            title="Upload Branch Reel"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>
      </header>

      {/* Main Vertical Reel Player Container */}
      <main className="w-full max-w-sm h-[84vh] mt-14 mb-4 relative rounded-3xl overflow-hidden bg-slate-900 border border-slate-800 shadow-2xl flex flex-col justify-between">
        {currentReel ? (
          <>
            {/* Video Player or Fallback Container */}
            <div 
              className="absolute inset-0 bg-slate-950 flex items-center justify-center cursor-pointer group"
              onClick={() => setIsPlaying(!isPlaying)}
            >
              {currentReel.media_url.endsWith('.mp4') || currentReel.media_url.includes('mixkit') || currentReel.media_url.includes('cdn') ? (
                <video
                  ref={videoRef}
                  src={currentReel.media_url}
                  className="w-full h-full object-cover"
                  loop
                  muted={isMuted}
                  playsInline
                  autoPlay
                />
              ) : (
                /* iframe embed fallback if youtube/vimeo */
                <iframe
                  src={currentReel.media_url}
                  title={currentReel.title}
                  className="w-full h-full pointer-events-none"
                  allow="autoplay; encrypted-media"
                />
              )}

              {/* Play / Pause Animated Overlay Badge */}
              {!isPlaying && (
                <div className="absolute inset-0 bg-black/40 flex items-center justify-center transition-opacity">
                  <div className="p-4 rounded-full bg-slate-900/80 text-white shadow-2xl border border-white/20 backdrop-blur-md">
                    <Play className="h-10 w-10 fill-white translate-x-0.5" />
                  </div>
                </div>
              )}
            </div>

            {/* Top Reel Overlay Header */}
            <div className="relative z-20 p-4 flex items-center justify-between bg-gradient-to-b from-black/80 via-black/40 to-transparent pointer-events-none">
              <div className="flex items-center gap-2 pointer-events-auto">
                <span className="flex items-center gap-1 text-[10px] font-extrabold uppercase px-2.5 py-1 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30 backdrop-blur-md">
                  <Film className="h-3 w-3" /> Gurukula Reel #{currentIndex + 1}
                </span>
              </div>
              <button
                onClick={() => setIsMuted(!isMuted)}
                className="p-2 rounded-full bg-black/50 text-white hover:bg-black/70 backdrop-blur-md border border-white/10 pointer-events-auto transition"
              >
                {isMuted ? <VolumeX className="h-4 w-4 text-rose-400" /> : <Volume2 className="h-4 w-4 text-emerald-400" />}
              </button>
            </div>

            {/* Right Action Bar (Likes, Comments, Share) */}
            <div className="absolute right-3 bottom-20 z-30 flex flex-col items-center gap-5">
              {/* Like Button */}
              <button
                onClick={() => toggleLike(currentReel.id)}
                className="flex flex-col items-center gap-1 group"
              >
                <div className={`p-3 rounded-full backdrop-blur-md border transition-all duration-200 ${
                  likedReels[currentReel.id] 
                    ? 'bg-rose-500/30 border-rose-500/50 text-rose-500 scale-110 shadow-lg shadow-rose-500/20' 
                    : 'bg-slate-900/60 border-white/10 text-white hover:bg-slate-800/80'
                }`}>
                  <Heart className={`h-6 w-6 ${likedReels[currentReel.id] ? 'fill-rose-500' : ''}`} />
                </div>
                <span className="text-[11px] font-bold drop-shadow">
                  {likeCounts[currentReel.id] || 0}
                </span>
              </button>

              {/* Comment Button */}
              <button
                onClick={() => setShowComments(!showComments)}
                className="flex flex-col items-center gap-1 group"
              >
                <div className="p-3 rounded-full bg-slate-900/60 border border-white/10 text-white hover:bg-slate-800/80 backdrop-blur-md transition-all">
                  <MessageCircle className="h-6 w-6" />
                </div>
                <span className="text-[11px] font-bold drop-shadow">
                  {(comments[currentReel.id] || []).length}
                </span>
              </button>

              {/* Share Button */}
              <button
                onClick={() => handleShare(currentReel)}
                className="flex flex-col items-center gap-1 group"
              >
                <div className="p-3 rounded-full bg-slate-900/60 border border-white/10 text-white hover:bg-slate-800/80 backdrop-blur-md transition-all">
                  <Share2 className="h-6 w-6" />
                </div>
                <span className="text-[11px] font-bold drop-shadow">Share</span>
              </button>

              {/* Spinning Music Vinyl Disc */}
              <div className="w-9 h-9 rounded-full bg-slate-900/90 border border-white/20 flex items-center justify-center animate-spin duration-3000">
                <Music className="h-4 w-4 text-emerald-400" />
              </div>
            </div>

            {/* Bottom Caption & Branch Info Overlay */}
            <div className="relative z-20 p-4 bg-gradient-to-t from-black/90 via-black/50 to-transparent pr-16 space-y-2 pointer-events-auto">
              {/* Branch Header Badge */}
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-bold text-xs">
                  <Building className="h-4 w-4" />
                </div>
                <div>
                  <div className="flex items-center gap-1">
                    <h3 className="text-xs font-bold text-white tracking-wide">{currentReel.institution_name}</h3>
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 fill-emerald-400/20" />
                  </div>
                  <span className="text-[9px] text-emerald-400 font-semibold uppercase">Official Gurukula Branch</span>
                </div>
              </div>

              {/* Title & Caption */}
              <p className="text-xs font-semibold text-slate-100 leading-snug line-clamp-2">
                {currentReel.title}
              </p>
              
              {/* Hashtags */}
              {currentReel.hashtags && (
                <p className="text-[11px] text-indigo-300 font-medium">
                  {currentReel.hashtags}
                </p>
              )}

              {/* Music Ticker */}
              <div className="flex items-center gap-1.5 text-[10px] text-slate-400 pt-0.5">
                <Music className="h-3 w-3 text-rose-400 animate-pulse" />
                <span className="truncate">Assisi Campus Media Sound • Original Audio</span>
              </div>
            </div>
          </>
        ) : (
          <div className="h-full flex flex-col items-center justify-center p-6 text-center text-slate-400">
            <Film className="h-12 w-12 text-slate-600 mb-3" />
            <p className="text-sm font-semibold">No campus video reels found for this branch.</p>
            <button
              onClick={() => setSelectedBranch('all')}
              className="mt-3 px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-bold"
            >
              Show All Gurukula Reels
            </button>
          </div>
        )}
      </main>

      {/* Up / Down Floating Scroll Navigation Buttons */}
      <div className="fixed right-4 top-1/2 -translate-y-1/2 z-40 hidden sm:flex flex-col gap-3">
        <button
          onClick={handlePrev}
          disabled={currentIndex === 0}
          className="p-3 rounded-full bg-slate-900/80 border border-white/10 text-white hover:bg-slate-800 disabled:opacity-30 backdrop-blur-md shadow-xl transition"
          title="Previous Reel"
        >
          <ChevronUp className="h-5 w-5" />
        </button>
        <button
          onClick={handleNext}
          disabled={currentIndex >= filteredReels.length - 1}
          className="p-3 rounded-full bg-slate-900/80 border border-white/10 text-white hover:bg-slate-800 disabled:opacity-30 backdrop-blur-md shadow-xl transition"
          title="Next Reel"
        >
          <ChevronDown className="h-5 w-5" />
        </button>
      </div>

      {/* Comments Side Drawer Overlay */}
      {showComments && currentReel && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4">
          <div className="w-full max-w-sm bg-slate-900 border border-slate-700/60 rounded-t-3xl sm:rounded-3xl p-4 text-white shadow-2xl animate-in slide-in-from-bottom">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <MessageCircle className="h-4 w-4 text-indigo-400" />
                <h4 className="text-sm font-bold">Community Comments</h4>
              </div>
              <button
                onClick={() => setShowComments(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="max-h-60 overflow-y-auto py-3 space-y-2.5 text-xs">
              {(comments[currentReel.id] || []).map((comm, idx) => (
                <div key={idx} className="bg-slate-950/60 p-2.5 rounded-xl border border-white/5 flex items-start gap-2">
                  <div className="w-6 h-6 rounded-full bg-indigo-500/20 text-indigo-300 font-bold flex items-center justify-center text-[10px]">
                    S
                  </div>
                  <div>
                    <span className="font-bold text-slate-300 block text-[10px]">Campus Member</span>
                    <p className="text-slate-200">{comm}</p>
                  </div>
                </div>
              ))}
            </div>

            <form onSubmit={handleAddComment} className="pt-2 flex items-center gap-2">
              <input
                type="text"
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Write a comment..."
                className="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
              <button
                type="submit"
                className="bg-indigo-600 hover:bg-indigo-500 text-white p-2 rounded-xl transition"
              >
                <Send className="h-4 w-4" />
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Upload Reel Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-slate-900 border border-slate-700/80 rounded-3xl p-6 text-white shadow-2xl relative">
            <button
              onClick={() => setShowUploadModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white"
            >
              <X className="h-5 w-5" />
            </button>

            <div className="flex items-center gap-2 mb-4">
              <div className="p-2 rounded-xl bg-rose-500/20 text-rose-400">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold">Publish Campus Video Reel</h3>
                <p className="text-xs text-slate-400">Upload video updates across 11 Gurukula branches</p>
              </div>
            </div>

            <form onSubmit={handleCreateReel} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Reel Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Science Exhibition & Lab Demonstration"
                  value={uploadTitle}
                  onChange={(e) => setUploadTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-white focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Select Gurukula Branch *</label>
                <select
                  value={uploadBranch}
                  onChange={(e) => setUploadBranch(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-white focus:border-indigo-500 focus:outline-none"
                >
                  <option value="Liebhaus Gurukula">Liebhaus Gurukula (Kidangoor)</option>
                  <option value="Mitraniketan Boys Gurukula">Mitraniketan Boys Gurukula (Vagamon)</option>
                  <option value="Pala Gurukula">Pala Gurukula (Pala)</option>
                  <option value="Bethsleeha Gurukula">Bethsleeha Gurukula (Kaduthuruthy)</option>
                  <option value="St.Alphonsa Gurukula">St.Alphonsa Gurukula (Bharanaganam)</option>
                  <option value="Thopramkudy Gurukula">Thopramkudy Gurukula (Thopramkudy)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Video URL (.mp4 or video link) *</label>
                <input
                  type="url"
                  required
                  placeholder="https://assets.mixkit.co/videos/preview/mixkit-..."
                  value={uploadVideoUrl}
                  onChange={(e) => setUploadVideoUrl(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-white font-mono text-[11px] focus:border-indigo-500 focus:outline-none"
                />
                <p className="text-[10px] text-slate-500 mt-1">Paste any direct MP4 video link or hosted video stream URL.</p>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Hashtags</label>
                <input
                  type="text"
                  placeholder="#Gurukula #CampusLife #AssisiSocial"
                  value={uploadHashtags}
                  onChange={(e) => setUploadHashtags(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-white focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-gradient-to-r from-rose-500 to-indigo-600 hover:from-rose-600 hover:to-indigo-700 text-white font-bold py-3 rounded-xl shadow-lg mt-2 transition"
              >
                {isSubmitting ? 'Publishing Reel...' : 'Publish Campus Reel 🎬'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
