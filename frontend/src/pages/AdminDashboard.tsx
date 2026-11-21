/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars */
import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { ShieldAlert, Users, Building, FileText, Search, Activity, MoreVertical, Ban, Edit, LogOut, Key, Trash2, X, Trophy, Upload, Loader2, Pin, Send, Paperclip } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { mockBranches, mockPosts } from '@/lib/mockData';
import { useToast } from '@/components/Toast';
import AdminGalleryManager from '@/components/AdminGalleryManager';
import { getB2Winners, getUploads, saveUpload, deleteUpload, B2_WINNER_TYPE } from '@/lib/storage';

const ADMIN_NOTE_SOURCE = 'Assisi Super Admin';

export default function AdminDashboard() {
  const { user, logout } = useAuth();
  const { showToast } = useToast();

  // Local state for mock editing
  const [branches, setBranches] = useState([...mockBranches]);
  const [posts, setPosts] = useState([...mockPosts]);

  // Modal states
  const [editingCredsBranch, setEditingCredsBranch] = useState<any>(null);
  const [managingContentBranch, setManagingContentBranch] = useState<any>(null);

  const [editUsername, setEditUsername] = useState('');
  const [editPassword, setEditPassword] = useState('');

  // B2 winners state
  const [winners, setWinners] = useState<any[]>([]);
  const [winnerFiles, setWinnerFiles] = useState<File[]>([]);
  const [winnerName, setWinnerName] = useState('');
  const [winnerCaption, setWinnerCaption] = useState('');
  const [uploadingWinners, setUploadingWinners] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadWinners = () => getB2Winners().then(setWinners);
  useEffect(() => { loadWinners(); }, []);

  const handleUploadWinners = async () => {
    if (winnerFiles.length === 0) return showToast('Select at least one photo');
    setUploadingWinners(true);
    try {
      for (const file of winnerFiles) {
        const fallbackName = file.name.replace(/\.[^.]+$/, '');
        await saveUpload({
          title: winnerName || fallbackName,
          content: winnerCaption || 'B2 Exam Winner',
          type: B2_WINNER_TYPE,
          mediaBlob: file,
        });
      }
      showToast(`${winnerFiles.length} winner photo(s) uploaded`);
      setWinnerFiles([]);
      setWinnerName('');
      setWinnerCaption('');
      if (fileInputRef.current) fileInputRef.current.value = '';
      await loadWinners();
    } catch (err) {
      console.error(err);
      showToast('Upload failed');
    } finally {
      setUploadingWinners(false);
    }
  };

  const handleDeleteWinner = async (id: number) => {
    await deleteUpload(id);
    setWinners((w) => w.filter((x) => x.id !== id));
    showToast('Winner photo removed');
  };

  // Important notes state
  const [notes, setNotes] = useState<any[]>([]);
  const [noteTitle, setNoteTitle] = useState('');
  const [noteBody, setNoteBody] = useState('');
  const [noteFile, setNoteFile] = useState<File | null>(null);
  const [postingNote, setPostingNote] = useState(false);
  const noteFileRef = useRef<HTMLInputElement>(null);

  const loadNotes = () =>
    getUploads().then((all) => setNotes(all.filter((u) => u.type === 'notice' && u.institution_name === ADMIN_NOTE_SOURCE)));
  useEffect(() => { loadNotes(); }, []);

  const handlePostNote = async () => {
    if (!noteTitle.trim() || !noteBody.trim()) return showToast('Enter a title and the note text');
    setPostingNote(true);
    try {
      await saveUpload({
        title: noteTitle.trim(),
        content: noteBody.trim(),
        type: 'notice',
        institution_name: ADMIN_NOTE_SOURCE,
        institution_id: 0,
        hashtags: '#important',
        mediaBlob: noteFile || undefined,
      });
      showToast('Important note published');
      setNoteTitle('');
      setNoteBody('');
      setNoteFile(null);
      if (noteFileRef.current) noteFileRef.current.value = '';
      await loadNotes();
    } catch (err) {
      console.error(err);
      showToast('Failed to publish note');
    } finally {
      setPostingNote(false);
    }
  };

  const handleDeleteNote = async (id: number) => {
    await deleteUpload(id);
    setNotes((n) => n.filter((x) => x.id !== id));
    showToast('Note deleted');
  };

  const handleLogout = async () => {
    try {
      await logout();
      showToast('Logged out successfully');
    } catch (err) {
      console.error(err);
    }
  };

  const handleSaveCreds = () => {
    if (!editingCredsBranch) return;
    const branchIndex = mockBranches.findIndex(b => b.id === editingCredsBranch.id);
    if (branchIndex !== -1) {
      mockBranches[branchIndex].username = editUsername;
      mockBranches[branchIndex].password = editPassword;
      setBranches([...mockBranches]);
      showToast(`Credentials updated for ${editingCredsBranch.name}`);
    }
    setEditingCredsBranch(null);
  };

  const handleDeletePost = (postId: number) => {
    const postIndex = mockPosts.findIndex(p => p.id === postId);
    if (postIndex !== -1) {
      mockPosts.splice(postIndex, 1);
      setPosts([...mockPosts]);
      showToast('Post deleted successfully');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200">
      {/* Top Navbar */}
      <header className="sticky top-0 z-50 bg-slate-900/80 backdrop-blur-xl border-b border-white/5 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 bg-rose-500/10 rounded-xl flex items-center justify-center border border-rose-500/20">
            <ShieldAlert className="h-5 w-5 text-rose-500" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white leading-tight">Super Admin Center</h1>
            <p className="text-xs text-slate-400">Assisi Platform Control Panel</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-3 px-4 py-2 bg-slate-900 rounded-full border border-white/5">
            <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <span className="text-xs font-medium text-slate-300">System Online</span>
          </div>
          <button 
            onClick={handleLogout}
            className="flex items-center gap-2 px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-sm font-bold transition-colors"
          >
            <LogOut className="h-4 w-4" />
            <span className="hidden sm:inline">Logout</span>
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8">
        
        {/* Welcome Section */}
        <div>
          <h2 className="text-3xl font-extrabold text-white">Welcome, {user?.username}</h2>
          <p className="text-slate-400 mt-1">Here's what's happening across the Assisi network today.</p>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Active Branches', value: branches.length.toString(), icon: Building, color: 'text-indigo-400', bg: 'bg-indigo-500/10' },
            { label: 'Total Students', value: '4,209', icon: Users, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
            { label: 'Content Uploads', value: '892', icon: FileText, color: 'text-amber-400', bg: 'bg-amber-500/10' },
            { label: 'System Health', value: '100%', icon: Activity, color: 'text-rose-400', bg: 'bg-rose-500/10' },
          ].map((stat, idx) => {
            const Icon = stat.icon;
            return (
              <motion.div 
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="bg-slate-900 border border-white/5 rounded-2xl p-6 relative overflow-hidden group"
              >
                <div className={`absolute -right-6 -top-6 w-24 h-24 rounded-full ${stat.bg} blur-2xl group-hover:bg-opacity-20 transition-all`}></div>
                <div className="flex items-center gap-4 relative z-10">
                  <div className={`p-3 rounded-xl ${stat.bg} ${stat.color}`}>
                    <Icon className="h-6 w-6" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-400 font-medium">{stat.label}</p>
                    <p className="text-2xl font-bold text-white">{stat.value}</p>
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>

        {/* Network Operations */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Branches Table */}
          <div className="lg:col-span-2 bg-slate-900 border border-white/5 rounded-2xl overflow-hidden shadow-xl shadow-black/20">
            <div className="p-6 border-b border-white/5 flex items-center justify-between">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Building className="h-5 w-5 text-indigo-500" />
                Institution Branches
              </h3>
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input 
                  type="text" 
                  placeholder="Search branches..." 
                  className="pl-9 pr-4 py-2 bg-slate-950 border border-white/5 rounded-xl text-sm focus:outline-none focus:border-indigo-500 text-slate-200 w-48 sm:w-64"
                />
              </div>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm whitespace-nowrap">
                <thead className="bg-slate-950/50 text-slate-400">
                  <tr>
                    <th className="px-6 py-4 font-semibold">Branch Name</th>
                    <th className="px-6 py-4 font-semibold">Location</th>
                    <th className="px-6 py-4 font-semibold">Username</th>
                    <th className="px-6 py-4 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {branches.map((branch) => (
                    <tr key={branch.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-bold text-white">{branch.name}</div>
                        <div className="text-xs text-slate-500">{branch.tag}</div>
                      </td>
                      <td className="px-6 py-4 text-slate-300">{branch.location}</td>
                      <td className="px-6 py-4">
                        <span className="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 text-xs font-mono">
                          {branch.username}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex justify-end gap-2">
                          <button 
                            onClick={() => {
                              setEditingCredsBranch(branch);
                              setEditUsername(branch.username);
                              setEditPassword(branch.password || '');
                            }}
                            className="px-3 py-1.5 bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 rounded-lg text-xs font-bold transition flex items-center gap-1"
                          >
                            <Key className="h-3 w-3" /> Credentials
                          </button>
                          <button 
                            onClick={() => setManagingContentBranch(branch)}
                            className="px-3 py-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 rounded-lg text-xs font-bold transition flex items-center gap-1"
                          >
                            <FileText className="h-3 w-3" /> Content
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Activity Feed */}
          <div className="bg-slate-900 border border-white/5 rounded-2xl overflow-hidden shadow-xl shadow-black/20 flex flex-col h-[600px]">
            <div className="p-6 border-b border-white/5">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Activity className="h-5 w-5 text-emerald-500" />
                Network Activity
              </h3>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-slate-800">
              {/* Mock Activity Logs */}
              {[
                { time: '10 mins ago', action: 'Uploaded new timetable PDF', user: 'Pala Gurukula', type: 'doc' },
                { time: '1 hour ago', action: 'Posted campus reel', user: 'Liebhaus Gurukula', type: 'video' },
                { time: '3 hours ago', action: 'Added 45 new student accounts', user: 'Bethsleeha Gurukula', type: 'user' },
                { time: '5 hours ago', action: 'Published official announcement', user: 'Assisi Mount Gurukula', type: 'news' },
                { time: '1 day ago', action: 'Uploaded event gallery', user: 'Traumhaus Gurukula', type: 'img' },
              ].map((log, i) => (
                <div key={i} className="flex gap-4 relative">
                  {i !== 4 && <div className="absolute top-8 left-3.5 w-px h-full bg-slate-800"></div>}
                  <div className="h-7 w-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center flex-shrink-0 relative z-10">
                    <div className="h-2 w-2 rounded-full bg-indigo-500"></div>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-300">{log.action}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs font-bold text-indigo-400">{log.user}</span>
                      <span className="text-xs text-slate-600">•</span>
                      <span className="text-xs text-slate-500">{log.time}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* Important Notes Manager */}
        <div className="bg-slate-900 border border-white/5 rounded-2xl overflow-hidden shadow-xl shadow-black/20">
          <div className="p-6 border-b border-white/5 flex items-center justify-between">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Pin className="h-5 w-5 text-sky-400" />
              Important Notes
            </h3>
            <span className="text-xs text-slate-400">Shown on Public Notices as Official Notes</span>
          </div>

          <div className="grid lg:grid-cols-2 gap-6 p-6">
            <div className="space-y-3">
              <input
                id="note-title"
                value={noteTitle}
                onChange={(e) => setNoteTitle(e.target.value)}
                placeholder="Note title e.g. Exam schedule changed"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-400"
              />
              <textarea
                id="note-body"
                value={noteBody}
                onChange={(e) => setNoteBody(e.target.value)}
                rows={5}
                placeholder="Write the important note for all students and branches..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-400 resize-none"
              />
              <div className="flex flex-wrap items-center gap-3">
                <label htmlFor="note-file" className="flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold cursor-pointer transition">
                  <Paperclip className="h-4 w-4" />
                  {noteFile ? noteFile.name : 'Attach PDF / image (optional)'}
                  <input
                    id="note-file"
                    ref={noteFileRef}
                    type="file"
                    accept="image/*,application/pdf"
                    className="hidden"
                    onChange={(e) => setNoteFile(e.target.files?.[0] || null)}
                  />
                </label>
                <button
                  id="note-post-btn"
                  onClick={handlePostNote}
                  disabled={postingNote}
                  className="ml-auto flex items-center gap-2 px-5 py-2.5 bg-sky-500 hover:bg-sky-400 disabled:opacity-60 text-slate-900 rounded-xl text-sm font-bold transition"
                >
                  {postingNote ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  {postingNote ? 'Publishing...' : 'Publish Note'}
                </button>
              </div>
            </div>

            <div className="space-y-3 max-h-[300px] overflow-y-auto pr-1">
              {notes.length === 0 ? (
                <p className="text-center text-slate-500 text-sm py-10">No important notes posted yet.</p>
              ) : (
                notes.map((n) => (
                  <div key={n.id} className="group bg-slate-950 border border-slate-800 rounded-xl p-4 flex justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] font-bold uppercase tracking-widest text-sky-400 bg-sky-500/10 px-2 py-0.5 rounded">Important</span>
                        <span className="text-xs text-slate-500">{n.created_at ? new Date(n.created_at).toLocaleString() : ''}</span>
                      </div>
                      <h4 className="text-sm font-bold text-white truncate">{n.title}</h4>
                      <p className="text-xs text-slate-400 mt-1 line-clamp-2">{n.content}</p>
                      {n.media_url && (
                        <a href={n.media_url} target="_blank" rel="noreferrer" className="text-xs text-sky-400 hover:underline mt-1 inline-block">View attachment</a>
                      )}
                    </div>
                    <button
                      onClick={() => handleDeleteNote(n.id)}
                      className="self-start p-2 text-slate-500 hover:text-rose-500 hover:bg-rose-500/10 rounded-lg transition"
                      title="Delete note"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        <AdminGalleryManager />

        {/* B2 Winners Manager */}
        <div className="bg-slate-900 border border-white/5 rounded-2xl overflow-hidden shadow-xl shadow-black/20">
          <div className="p-6 border-b border-white/5 flex items-center justify-between">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Trophy className="h-5 w-5 text-amber-400" />
              B2 Winners Showcase
            </h3>
            <span className="text-xs text-slate-400">{winners.length} photo(s) on home page</span>
          </div>

          <div className="p-6 grid md:grid-cols-4 gap-4 border-b border-white/5">
            <label htmlFor="b2-file-input" className="md:col-span-1 flex flex-col items-center justify-center gap-2 border-2 border-dashed border-slate-700 hover:border-amber-400 rounded-xl p-4 cursor-pointer text-slate-400 hover:text-amber-300 transition">
              <Upload className="h-6 w-6" />
              <span className="text-xs font-semibold text-center">
                {winnerFiles.length ? `${winnerFiles.length} photo(s) selected` : 'Choose student photos'}
              </span>
              <input
                id="b2-file-input"
                ref={fileInputRef}
                type="file"
                accept="image/*"
                multiple
                className="hidden"
                onChange={(e) => setWinnerFiles(Array.from(e.target.files || []))}
              />
            </label>
            <input
              id="b2-winner-name"
              value={winnerName}
              onChange={(e) => setWinnerName(e.target.value)}
              placeholder="Student name (optional – uses file name)"
              className="bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-amber-400"
            />
            <input
              id="b2-winner-caption"
              value={winnerCaption}
              onChange={(e) => setWinnerCaption(e.target.value)}
              placeholder="Caption e.g. German B2 – Goethe 2026"
              className="bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-amber-400"
            />
            <button
              id="b2-upload-btn"
              onClick={handleUploadWinners}
              disabled={uploadingWinners}
              className="flex items-center justify-center gap-2 px-4 py-2.5 bg-amber-500 hover:bg-amber-400 disabled:opacity-60 text-slate-900 rounded-xl text-sm font-bold transition"
            >
              {uploadingWinners ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
              {uploadingWinners ? 'Uploading...' : 'Upload Winners'}
            </button>
          </div>

          <div className="p-6">
            {winners.length === 0 ? (
              <p className="text-center text-slate-500 text-sm py-6">No B2 winner photos yet. Uploaded photos will rotate on the home page.</p>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-4">
                {winners.map((w) => (
                  <div key={w.id} className="relative group rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
                    <img src={w.media_url} alt={w.title} className="w-full h-32 object-cover" />
                    <div className="p-2">
                      <p className="text-xs font-bold text-white truncate">{w.title}</p>
                      <p className="text-[10px] text-slate-500 truncate">{w.content}</p>
                    </div>
                    <button
                      onClick={() => handleDeleteWinner(w.id)}
                      className="absolute top-2 right-2 p-1.5 bg-rose-600/90 hover:bg-rose-500 text-white rounded-lg opacity-0 group-hover:opacity-100 transition"
                      title="Remove"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Edit Credentials Modal */}
      {editingCredsBranch && (
        <div className="fixed inset-0 z-[100] bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-md shadow-2xl p-6">
            <div className="flex justify-between items-center mb-6 border-b border-slate-800 pb-4">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Key className="h-5 w-5 text-indigo-400" />
                Edit Credentials
              </h3>
              <button onClick={() => setEditingCredsBranch(null)} className="text-slate-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="space-y-4 mb-6">
              <p className="text-sm text-slate-400">Updating access for <strong className="text-white">{editingCredsBranch.name}</strong></p>
              
              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Branch ID / Username</label>
                <input 
                  type="text" 
                  value={editUsername}
                  onChange={e => setEditUsername(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
              
              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Password</label>
                <input 
                  type="text" 
                  value={editPassword}
                  onChange={e => setEditPassword(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3">
              <button 
                onClick={() => setEditingCredsBranch(null)}
                className="px-4 py-2 text-sm font-bold text-slate-300 hover:text-white bg-slate-800 rounded-xl"
              >
                Cancel
              </button>
              <button 
                onClick={handleSaveCreds}
                className="px-4 py-2 text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl"
              >
                Save Credentials
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Manage Content Modal */}
      {managingContentBranch && (
        <div className="fixed inset-0 z-[100] bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-2xl max-h-[80vh] flex flex-col shadow-2xl">
            <div className="flex justify-between items-center p-6 border-b border-slate-800">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <FileText className="h-5 w-5 text-emerald-400" />
                Manage Content: {managingContentBranch.name}
              </h3>
              <button onClick={() => setManagingContentBranch(null)} className="text-slate-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto flex-1 space-y-4">
              {posts.filter(p => p.institution_id === managingContentBranch.id).length === 0 ? (
                <div className="text-center py-10">
                  <p className="text-slate-500 font-medium">No active content uploaded by this branch.</p>
                </div>
              ) : (
                posts.filter(p => p.institution_id === managingContentBranch.id).map(post => (
                  <div key={post.id} className="bg-slate-950 border border-slate-800 rounded-xl p-4 flex justify-between items-start group">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] font-bold uppercase tracking-widest text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded">
                          {post.type}
                        </span>
                        <span className="text-xs text-slate-500">{new Date(post.created_at).toLocaleDateString()}</span>
                      </div>
                      <h4 className="text-sm font-bold text-white">{post.title}</h4>
                      <p className="text-xs text-slate-400 mt-1 line-clamp-1">{post.content}</p>
                    </div>
                    <button 
                      onClick={() => handleDeletePost(post.id)}
                      className="p-2 text-slate-500 hover:text-rose-500 hover:bg-rose-500/10 rounded-lg transition opacity-0 group-hover:opacity-100"
                      title="Delete Post"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))
              )}
            </div>

            <div className="p-4 border-t border-slate-800 flex justify-end">
              <button 
                onClick={() => setManagingContentBranch(null)}
                className="px-4 py-2 text-sm font-bold text-white bg-slate-800 hover:bg-slate-700 rounded-xl"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
