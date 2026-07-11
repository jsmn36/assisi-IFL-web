import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import StudentLayout from '@/components/StudentLayout';
import api from '@/lib/api';
import { Search, Compass, User as UserIcon, Grid, Calendar } from 'lucide-react';
import { useToast } from '@/components/Toast';

export default function StudentExplore() {
  const { showToast } = useToast();

  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [explorePosts, setExplorePosts] = useState<any[]>([]);

  const loadExplorePosts = async () => {
    try {
      // Get general posts
      const posts = await api.getPosts({ limit: 18 });
      setExplorePosts(posts);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadExplorePosts();
  }, []);

  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchTerm.trim()) {
      setSearchResults([]);
      return;
    }
    try {
      const results = await api.searchSocial(searchTerm);
      setSearchResults(results.users || []);
    } catch (err) {
      showToast('Search failed.', 'error');
    }
  };

  return (
    <StudentLayout>
      <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
        
        {/* Explore Title & Search form */}
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 bg-indigo-100 dark:bg-indigo-950/60 text-indigo-600 rounded-xl flex items-center justify-center">
              <Compass className="h-5.5 w-5.5" />
            </div>
            <div>
              <h1 className="font-extrabold text-xl">Explore</h1>
              <p className="text-xs text-slate-400 dark:text-slate-500 font-semibold">Discover campus feeds, hashtags, and connect with other students.</p>
            </div>
          </div>

          <form onSubmit={handleSearchSubmit} className="relative max-w-xl">
            <Search className="absolute left-3.5 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-400" />
            <input
              type="text"
              placeholder="Search students by name, username, major, or admission number..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 pl-11 pr-24 py-3 rounded-2xl text-sm focus:outline-none focus:border-indigo-500 text-slate-855 dark:text-white shadow-sm"
            />
            <button
              type="submit"
              className="absolute right-2.5 top-1/2 transform -translate-y-1/2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs px-4 py-2 rounded-xl transition"
            >
              Search
            </button>
          </form>
        </div>

        {/* Search Results Display */}
        {searchTerm && (
          <div className="space-y-4">
            <h3 className="font-bold text-xs text-slate-400 uppercase tracking-wider">Search Results</h3>
            {searchResults.length === 0 ? (
              <p className="text-sm text-slate-455 dark:text-slate-400 italic">No students matched your query.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {searchResults.map((user) => (
                  <Link
                    key={user.id}
                    to={`/students/profile/${user.username}`}
                    className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-4 rounded-2xl flex items-center justify-between hover:shadow-md hover:border-indigo-200 dark:hover:border-indigo-900/50 transition shadow-sm"
                  >
                    <div className="flex items-center gap-3">
                      <img
                        src={user.profile_pic_url || `https://api.dicebear.com/7.x/adventurer/svg?seed=${user.username}`}
                        alt={user.username}
                        className="h-11 w-11 rounded-full bg-slate-100 dark:bg-slate-800"
                      />
                      <div>
                        <h4 className="font-bold text-xs text-slate-900 dark:text-white">{user.name}</h4>
                        <p className="text-[10px] text-slate-400">@{user.username}</p>
                        <p className="text-[9px] text-indigo-500 dark:text-indigo-400 font-semibold mt-0.5">{user.class_or_department || 'General major'}</p>
                      </div>
                    </div>
                    <span className="text-[9px] bg-slate-100 dark:bg-slate-800 font-bold px-2.5 py-1.5 rounded-lg text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                      View Profile
                    </span>
                  </Link>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Explore Feed */}
        <div className="space-y-4">
          <h2 className="font-extrabold text-base flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
            <Grid className="h-4.5 w-4.5 text-indigo-500" />
            Trending Posts
          </h2>

          {explorePosts.length === 0 ? (
            <p className="text-xs text-slate-400 text-center py-10 italic">No posts available to show.</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {explorePosts.map((post) => (
                <div key={post.id} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm flex flex-col justify-between hover:shadow-md transition">
                  {post.media_url ? (
                    <div className="aspect-[4/3] w-full bg-slate-950 flex items-center justify-center overflow-hidden">
                      <img
                        src={post.media_url}
                        alt={post.title}
                        className="w-full h-full object-cover"
                      />
                    </div>
                  ) : (
                    <div className="aspect-[4/3] w-full bg-gradient-to-br from-indigo-50 to-violet-50 dark:from-slate-950 dark:to-indigo-950/40 p-4 flex items-center justify-center">
                      <p className="text-[10px] text-slate-400 dark:text-slate-500 italic text-center leading-relaxed line-clamp-4">{post.content || 'Notice update'}</p>
                    </div>
                  )}
                  <div className="p-4 space-y-2">
                    <h4 className="font-bold text-xs line-clamp-1">{post.title}</h4>
                    <div className="flex items-center justify-between pt-1 border-t border-slate-100 dark:border-slate-800/40">
                      <span className="text-[9px] text-slate-400 font-semibold">@{post.institution_name}</span>
                      <span className="text-[9px] text-slate-455 font-medium">{new Date(post.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </StudentLayout>
  );
}
